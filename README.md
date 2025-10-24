# Flight Booking System API

This is a complete simulation of a flight booking backend built with FastAPI. It provides APIs for searching flights with real-time dynamic pricing, creating concurrency-safe bookings, and managing them.

## Key Features

-   **Database Ready**: Uses SQLite out of the box (no setup needed) but can be easily switched to MySQL.
-   **RESTful APIs**: Endpoints to search, book, view, and cancel flights.
-   **Dynamic Pricing Engine**: Flight costs adjust based on seat availability and time to departure.
-   **Concurrency Safe**: Booking transactions are atomic to prevent overbooking.
-   **Interactive API Docs**: Explore and test all APIs easily in your browser.

---

## 🚀 How to Run This Project

### 1. Setup Your Environment

First, open your terminal in the project folder and create a virtual environment. This keeps your project's packages separate from others on your system.

```bash
# Create the virtual environment
python -m venv venv

# Activate it (the command is different for Windows vs. Mac/Linux)
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate