from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import Flight, Base, DATABASE_URL

# Data to insert into the flights table
flights_data = [
    {
        "flight_no": "AI101", "origin": "Delhi", "destination": "Mumbai",
        "departure": datetime(2025, 11, 20, 10, 0), "arrival": datetime(2025, 11, 20, 12, 0),
        "base_fare": 8000.00, "total_seats": 200, "seats_available": 150, "airline_name": "Air India"
    },
    {
        "flight_no": "AI102", "origin": "Mumbai", "destination": "Delhi",
        "departure": datetime(2025, 11, 20, 15, 0), "arrival": datetime(2025, 11, 20, 17, 0),
        "base_fare": 8200.00, "total_seats": 200, "seats_available": 180, "airline_name": "Air India"
    },
    {
        "flight_no": "6E201", "origin": "Delhi", "destination": "Chennai",
        "departure": datetime(2025, 11, 21, 9, 0), "arrival": datetime(2025, 11, 21, 11, 30),
        "base_fare": 9000.00, "total_seats": 180, "seats_available": 160, "airline_name": "IndiGo"
    },
    {
        "flight_no": "6E202", "origin": "Chennai", "destination": "Delhi",
        "departure": datetime(2025, 11, 21, 13, 0), "arrival": datetime(2025, 11, 21, 15, 30),
        "base_fare": 9100.00, "total_seats": 180, "seats_available": 175, "airline_name": "IndiGo"
    },
    {
        "flight_no": "UK301", "origin": "Mumbai", "destination": "Chennai",
        "departure": datetime(2025, 11, 22, 12, 0), "arrival": datetime(2025, 11, 22, 14, 30),
        "base_fare": 6000.00, "total_seats": 150, "seats_available": 120, "airline_name": "Vistara"
    },
    {
        "flight_no": "SG401", "origin": "Delhi", "destination": "Kolkata",
        "departure": datetime(2025, 11, 23, 7, 0), "arrival": datetime(2025, 11, 23, 9, 0),
        "base_fare": 5500.00, "total_seats": 180, "seats_available": 100, "airline_name": "SpiceJet"
    }
]

def seed_data():
    """Populates the database with initial flight data."""
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Check if flights table is empty before seeding
        if db.query(Flight).count() == 0:
            print("Database is empty. Seeding data...")
            for flight_info in flights_data:
                flight = Flight(**flight_info)
                db.add(flight)
            db.commit()
            print("✅ Database seeded successfully!")
        else:
            print("Database already contains data. Skipping seed.")
    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
