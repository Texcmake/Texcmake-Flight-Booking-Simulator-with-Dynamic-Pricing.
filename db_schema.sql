-- This script is for reference and practice in a MySQL database.
-- The FastAPI application will create its own SQLite database automatically.

-- Drop the database if it exists to start fresh
DROP DATABASE IF EXISTS flight_booking_system;

-- Create the database
CREATE DATABASE flight_booking_system;

-- Use the newly created database
USE flight_booking_system;

-- ---------------------------------
-- TABLE CREATION
-- ---------------------------------

-- Create the 'flights' table to store flight information
CREATE TABLE flights (
    id INT AUTO_INCREMENT PRIMARY KEY,
    flight_no VARCHAR(10) NOT NULL UNIQUE,
    origin VARCHAR(50) NOT NULL,
    destination VARCHAR(50) NOT NULL,
    departure DATETIME NOT NULL,
    arrival DATETIME NOT NULL,
    base_fare DECIMAL(10, 2) NOT NULL,
    total_seats INT NOT NULL,
    seats_available INT NOT NULL,
    airline_name VARCHAR(50) NOT NULL,
    -- 'economy', 'business', 'first' can be used for pricing tiers
    airline_tier VARCHAR(20) DEFAULT 'economy',
    -- Add a check constraint to ensure seats_available is logical
    CONSTRAINT chk_seats_available CHECK (seats_available >= 0 AND seats_available <= total_seats)
);

-- Create the 'bookings' table to store booking details
CREATE TABLE bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    flight_id INT NOT NULL,
    passenger_name VARCHAR(100) NOT NULL,
    seat_no VARCHAR(5),
    pnr VARCHAR(10) NOT NULL UNIQUE,
    price DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Confirmed', -- e.g., Confirmed, Cancelled, Paid
    booking_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Establish a foreign key relationship with the 'flights' table
    FOREIGN KEY (flight_id) REFERENCES flights(id) ON DELETE CASCADE
);

-- ---------------------------------
-- DATA INSERTION (Populating the DB)
-- ---------------------------------

INSERT INTO flights (flight_no, origin, destination, departure, arrival, base_fare, total_seats, seats_available, airline_name)
VALUES
('AI101', 'Delhi', 'Mumbai', '2025-11-20 10:00:00', '2025-11-20 12:00:00', 8000.00, 200, 150, 'Air India'),
('AI102', 'Mumbai', 'Delhi', '2025-11-20 15:00:00', '2025-11-20 17:00:00', 8200.00, 200, 180, 'Air India'),
('6E201', 'Delhi', 'Chennai', '2025-11-21 09:00:00', '2025-11-21 11:30:00', 9000.00, 180, 160, 'IndiGo'),
('6E202', 'Chennai', 'Delhi', '2025-11-21 13:00:00', '2025-11-21 15:30:00', 9100.00, 180, 175, 'IndiGo'),
('UK301', 'Mumbai', 'Chennai', '2025-11-22 12:00:00', '2025-11-22 14:30:00', 6000.00, 150, 120, 'Vistara'),
('UK302', 'Chennai', 'Mumbai', '2025-11-22 16:00:00', '2025-11-22 18:30:00', 7000.00, 150, 140, 'Vistara'),
('SG401', 'Delhi', 'Kolkata', '2025-11-23 07:00:00', '2025-11-23 09:00:00', 5500.00, 180, 100, 'SpiceJet');


-- ---------------------------------
-- SQL PRACTICE QUERIES
-- ---------------------------------

-- SELECT: Get all flights
SELECT * FROM flights;

-- SELECT with specific columns and WHERE clause: Find flights from Mumbai
SELECT flight_no, origin, destination, base_fare FROM flights WHERE origin = 'Mumbai';

-- UPDATE: Change the number of available seats for a flight
UPDATE flights SET seats_available = 115 WHERE flight_no = 'UK301';

-- DELETE: Remove a flight from the system
-- DELETE FROM flights WHERE flight_no = 'SG401';

-- ORDER BY: List flights sorted by base fare (cheapest first)
SELECT flight_no, base_fare, airline_name FROM flights ORDER BY base_fare ASC;

-- AGGREGATE FUNCTIONS: Count total flights and find average fare from Delhi
SELECT COUNT(*) AS total_flights FROM flights;
SELECT AVG(base_fare) AS avg_delhi_fare FROM flights WHERE origin = 'Delhi';

-- GROUP BY and HAVING: Find average fare per origin city, for cities with avg fare < 8500
SELECT origin, AVG(base_fare) AS average_fare, COUNT(*) as number_of_flights
FROM flights
GROUP BY origin
HAVING average_fare < 8500;

-- JOIN: Get passenger details along with their flight number and destination
-- First, add some sample bookings to join with:
INSERT INTO bookings (flight_id, passenger_name, seat_no, pnr, price)
VALUES
(1, 'Alice Johnson', '12A', 'PNR123', 8500.00),
(3, 'Charlie Brown', '24C', 'PNR345', 9200.00);

-- Inner Join Query
SELECT
    b.pnr,
    b.passenger_name,
    f.flight_no,
    f.origin,
    f.destination,
    f.departure
FROM bookings AS b
INNER JOIN flights AS f ON b.flight_id = f.id;


-- TRANSACTION: Safely book a flight
-- This ensures that all commands execute together as a single atomic unit.
START TRANSACTION;

-- 1. Check seat availability for flight with id 4
-- Let's assume we are booking a seat on flight_id = 4 ('6E202')
-- In a real app, you'd check if the result of this select is > 0

-- 2. Update the seat availability (decrement by 1)
UPDATE flights SET seats_available = seats_available - 1 WHERE id = 4 AND seats_available > 0;

-- 3. Insert the new booking record
INSERT INTO bookings (flight_id, passenger_name, seat_no, pnr, price)
VALUES (4, 'David Lee', '18B', 'PNR901', 9300.00);

-- If all commands are successful, commit the changes to the database
COMMIT;

-- If there was an error (e.g., no seats available), you would issue a ROLLBACK command.
-- ROLLBACK;