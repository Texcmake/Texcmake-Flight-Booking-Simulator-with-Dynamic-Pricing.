import asyncio
import random
import string
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status
# --- NEW IMPORTS ---
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse 

from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, DateTime, DECIMAL, ForeignKey, CheckConstraint, func
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.exc import IntegrityError

# --- Configuration (Unchanged) ---
DATABASE_URL = "sqlite:///./flight_booking.db"

# --- SQLAlchemy Setup (Unchanged) ---
Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Database Models (Flight is Unchanged) ---
class Flight(Base):
    __tablename__ = "flights"
    id = Column(Integer, primary_key=True, index=True)
    flight_no = Column(String, unique=True, nullable=False)
    origin = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    departure = Column(DateTime, nullable=False)
    arrival = Column(DateTime, nullable=False)
    base_fare = Column(DECIMAL(10, 2), nullable=False)
    total_seats = Column(Integer, nullable=False)
    seats_available = Column(Integer, nullable=False)
    airline_name = Column(String, nullable=False)
    __table_args__ = (CheckConstraint('seats_available >= 0 AND seats_available <= total_seats'),)

# --- Database Models (Booking is MODIFIED) ---
class Booking(Base):
    __tablename__ = "bookings"
    booking_id = Column(Integer, primary_key=True, index=True)
    flight_id = Column(Integer, ForeignKey("flights.id"), nullable=False)
    passenger_name = Column(String, nullable=False)
    seat_no = Column(String)
    pnr = Column(String, unique=True, nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    # --- MODIFIED ---
    # The default status is now 'Pending' until payment is confirmed.
    status = Column(String, default='Pending', nullable=False) 

# --- Pydantic Models (Unchanged) ---
class Passenger(BaseModel):
    first_name: str = Field(..., min_length=1, example="John")
    last_name: str = Field(..., min_length=1, example="Doe")

class BookingRequest(BaseModel):
    flight_id: int
    passenger: Passenger

class FlightResponse(BaseModel):
    flight_id: int
    flight_no: str
    origin: str
    destination: str
    departure: datetime
    arrival: datetime
    duration_hours: float
    dynamic_price: float
    seats_available: int
    airline_name: str
    class Config:
        orm_mode = True # orm_mode is deprecated, but we'll keep it as it's in your file
        from_attributes=True # Use this for Pydantic v2

class BookingResponse(BaseModel):
    pnr: str
    flight_no: str
    passenger_name: str
    status: str
    price: float
    departure: datetime
    origin: str
    destination: str
    class Config:
        orm_mode = True
        from_attributes=True

# --- NEW PYDANTIC MODEL ---
class PaymentResponse(BaseModel):
    pnr: str
    status: str
    message: str

# --- Database Dependency (Unchanged) ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Core Logic: Dynamic Pricing Engine (Unchanged) ---
def calculate_dynamic_price(base_fare: float, seats_available: int, total_seats: int, departure: datetime) -> float:
    occupancy = (total_seats - seats_available) / total_seats
    if occupancy < 0.4: seat_factor = 0.9
    elif occupancy < 0.8: seat_factor = 1.2
    else: seat_factor = 1.5

    days_to_departure = (departure - datetime.now()).days
    if days_to_departure > 45: time_factor = 0.85
    elif days_to_departure > 10: time_factor = 1.1
    else: time_factor = 1.4

    demand_factor = random.uniform(0.98, 1.08)
    dynamic_price = base_fare * seat_factor * time_factor * demand_factor
    return round(dynamic_price, 2)

# --- Helper Functions (Unchanged) ---
def generate_pnr() -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# --- FastAPI Application (Unchanged) ---
app = FastAPI(title="Flight Booking API", version="1.0")

# --- Background Task (Unchanged) ---
async def simulate_market_changes():
    await asyncio.sleep(15)
    while True:
        try:
            db = SessionLocal()
            flight = db.query(Flight).filter(Flight.seats_available > 0, Flight.departure > datetime.now()).order_by(func.random()).first()
            if flight and flight.seats_available > 0:
                flight.seats_available -= 1
                db.commit()
                print(f"SIMULATOR: A seat was booked on {flight.flight_no}. Remaining: {flight.seats_available}")
        except Exception as e:
            db.rollback()
        finally:
            db.close()
        await asyncio.sleep(random.randint(20, 45))

@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)
    # Optional: You can uncomment the line below to start the background simulator
    # asyncio.create_task(simulate_market_changes())

# --- API Endpoints ---
@app.get("/api/", tags=["Root"]) # --- MODIFIED --- Added /api prefix
def read_root():
    return {"message": "Welcome to the Flight Booking API ✈️"}

@app.get("/api/flights/search", response_model=List[FlightResponse], tags=["Flights"]) # --- MODIFIED --- Added /api prefix
def search_flights(origin: str, destination: str, date: str, sort_by: Optional[str] = 'price', db: Session = Depends(get_db)):
    try:
        search_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    query = db.query(Flight).filter(
        Flight.origin.ilike(f"%{origin}%"),
        Flight.destination.ilike(f"%{destination}%"),
        Flight.departure >= datetime.combine(search_date, datetime.min.time()),
        Flight.departure < datetime.combine(search_date, datetime.max.time()),
        Flight.seats_available > 0
    )
    
    flights = query.all()
    if not flights:
        return []

    response_flights = []
    for flight in flights:
        price = calculate_dynamic_price(float(flight.base_fare), flight.seats_available, flight.total_seats, flight.departure)
        duration = (flight.arrival - flight.departure).total_seconds() / 3600
        response_flights.append(
            FlightResponse(
                flight_id=flight.id, flight_no=flight.flight_no, origin=flight.origin,
                destination=flight.destination, departure=flight.departure, arrival=flight.arrival,
                duration_hours=round(duration, 2), dynamic_price=price,
                seats_available=flight.seats_available, airline_name=flight.airline_name
            )
        )

    if sort_by == 'duration':
        response_flights.sort(key=lambda x: x.duration_hours)
    else:
        response_flights.sort(key=lambda x: x.dynamic_price)
    return response_flights

@app.post("/api/bookings", response_model=BookingResponse, status_code=status.HTTP_201_CREATED, tags=["Bookings"]) # --- MODIFIED --- Added /api prefix
def create_booking(request: BookingRequest, db: Session = Depends(get_db)):
    """Creates a booking. This is a transactional and concurrency-safe endpoint."""
    try:
        flight = db.query(Flight).filter(Flight.id == request.flight_id).with_for_update().first()

        if not flight:
            raise HTTPException(status_code=404, detail="Flight not found.")
        if flight.seats_available <= 0:
            raise HTTPException(status_code=400, detail="No seats available.")

        final_price = calculate_dynamic_price(float(flight.base_fare), flight.seats_available, flight.total_seats, flight.departure)
        
        flight.seats_available -= 1
        
        new_booking = Booking(
            flight_id=flight.id,
            passenger_name=f"{request.passenger.first_name} {request.passenger.last_name}",
            pnr=generate_pnr(),
            price=final_price,
            # --- MODIFIED ---
            # Status is now 'Pending' by default, so we don't set it to 'Confirmed' here.
            status="Pending" 
        )
        
        db.add(new_booking)
        db.commit()
        db.refresh(new_booking)
        
        return BookingResponse(
            pnr=new_booking.pnr, flight_no=flight.flight_no, passenger_name=new_booking.passenger_name,
            status=new_booking.status, price=float(new_booking.price), departure=flight.departure,
            origin=flight.origin, destination=flight.destination
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Booking failed. Please try again. Error: {e}")

# --- NEW ENDPOINT: SIMULATE PAYMENT ---
@app.post("/api/bookings/{pnr}/pay", response_model=PaymentResponse, tags=["Bookings"])
def pay_for_booking(pnr: str, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.pnr.ilike(pnr)).with_for_update().first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")
    
    if booking.status == "Confirmed":
        return {"pnr": pnr, "status": "Confirmed", "message": "This booking is already paid for."}

    # Simulate a payment success or failure
    payment_success = random.choice([True, False])
    
    if payment_success:
        booking.status = "Confirmed"
        db.commit()
        return {"pnr": pnr, "status": "Confirmed", "message": "Payment successful. Your booking is confirmed."}
    else:
        # If payment fails, we'll "cancel" the booking and restore the seat
        booking.status = "Failed"
        flight = db.query(Flight).filter(Flight.id == booking.flight_id).with_for_update().first()
        if flight:
            flight.seats_available += 1
        
        db.commit()
        return {"pnr": pnr, "status": "Failed", "message": "Payment failed. Your booking has been cancelled and seat released."}

# --- NEW ENDPOINT: GET RECEIPT (JSON) ---
@app.get("/api/bookings/{pnr}/receipt", response_model=BookingResponse, tags=["Bookings"])
def get_booking_receipt(pnr: str, db: Session = Depends(get_db)):
    """Returns the booking details, which serves as a JSON receipt."""
    return get_booking(pnr=pnr, db=db)


@app.get("/api/bookings/{pnr}", response_model=BookingResponse, tags=["Bookings"]) # --- MODIFIED --- Added /api prefix
def get_booking(pnr: str, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.pnr.ilike(pnr)).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")
    
    flight = db.query(Flight).filter(Flight.id == booking.flight_id).first()
    
    return BookingResponse(
        pnr=booking.pnr, flight_no=flight.flight_no, passenger_name=booking.passenger_name,
        status=booking.status, price=float(booking.price), departure=flight.departure,
        origin=flight.origin, destination=flight.destination
    )

@app.delete("/api/bookings/{pnr}", status_code=status.HTTP_200_OK, tags=["Bookings"]) # --- MODIFIED --- Added /api prefix
def cancel_booking(pnr: str, db: Session = Depends(get_db)):
    try:
        booking = db.query(Booking).filter(Booking.pnr.ilike(pnr)).with_for_update().first()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found.")
        if booking.status == "Cancelled":
            raise HTTPException(status_code=400, detail="Booking is already cancelled.")

        flight = db.query(Flight).filter(Flight.id == booking.flight_id).with_for_update().first()

        # Only restore seat if booking was confirmed (not just pending or failed)
        if flight and booking.status == "Confirmed":
            flight.seats_available += 1
        
        booking.status = "Cancelled"
        db.commit()
        return {"message": f"Booking {pnr} has been cancelled successfully."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Cancellation failed. Error: {e}")


# --- NEW: MOUNT THE FRONTEND ---
# This line tells FastAPI to serve all files from the 'static' folder
app.mount("/", StaticFiles(directory="static", html=True), name="static")

# This is a fallback to ensure your index.html is served from the root
@app.get("/")
async def get_index():
    return FileResponse('static/index.html')