from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import ALL four of your services
from app.services import helmet_service
from app.services import loitering_service
from app.services import production_counter_service
from app.services import attendance_service

app = FastAPI(title="Factory Safety Dashboard API")

# --- CORS MIDDLEWARE ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, change to your Angular app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API ENDPOINTS ---

@app.get("/")
def read_root():
    return {"message": "Factory Safety API is running."}


@app.get("/api/status/helmet")
def get_helmet_status():
    data = helmet_service.get_helmet_detection_status()
    return data


@app.get("/api/status/loitering")
def get_loitering_status():
    data = loitering_service.get_loitering_status()
    return data


@app.get("/api/status/counting")
def get_production_count():
    data = production_counter_service.get_production_count()
    return data


# --- NEW FINAL ENDPOINT ---
@app.get("/api/status/attendance")
def get_attendance_status():
    """
    Endpoint for the attendance system.
    """
    data = attendance_service.get_attendance_status()
    return data
# --------------------


# --- STARTUP COMMAND ---
# Use this to run the server: uvicorn app.main:app --reload --port 8000