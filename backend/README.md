# Factory Safety Detector - Backend

## Overview

This is the backend service for the Factory Safety Detector system, built with FastAPI and powered by ML models.

## Structure

```
backend/
├── app/
│   ├── main.py                    # FastAPI application with API endpoints
│   └── services/                  # ML model services
│       ├── helmet_service.py      # Helmet detection
│       ├── loitering_service.py   # Loitering detection
│       ├── production_counter_service.py
│       └── attendance_service.py  # Face recognition
│
├── models/                        # ML model files (.pt)
│   ├── best_helmet.pt
│   ├── best_product.pt
│   └── yolo*.pt
│
├── database/
│   └── employees/                 # Employee photos for face recognition
│
├── config/
│   └── data.yaml                  # YOLO configuration
│
├── scripts/                       # Standalone detection scripts
│   ├── attendance_system.py
│   ├── loitering_monitor.py
│   ├── production_counter.py
│   └── realtime_detector.py
│
└── requirements.txt               # Python dependencies
```

## Installation

### 1. Install Python Dependencies

```powershell
cd backend
pip install -r requirements.txt
```

### 2. Setup Employee Database (Optional)

Add employee photos to `database/employees/`:
- Format: `firstname.jpg` or `firstname.png`
- Example: `john.jpg`, `sarah.png`

## Running the Backend

### Start the API Server

```powershell
cd backend
uvicorn app.main:app --reload --port 8000
```

Or from project root:
```powershell
cd backend
uvicorn app.main:app --reload --port 8000
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/api/status/helmet` | GET | Helmet detection data |
| `/api/status/loitering` | GET | Loitering detection data |
| `/api/status/counting` | GET | Production counter data |
| `/api/status/attendance` | GET | Attendance system data |

### API Documentation

Interactive API docs available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Configuration

### Video Source

Edit service files to change camera source:
```python
VIDEO_SOURCE = 0  # Change to 1, 2, or video file path
```

### Detection Thresholds

Edit in service files:
- `CONFIDENCE_THRESHOLD` - Helmet detection sensitivity
- `LOITERING_TIME_THRESHOLD` - Loitering duration (seconds)
- `RECOGNITION_INTERVAL` - Face recognition frequency

### Model Paths

Models are located in `models/` folder. Update paths in service files if needed:
```python
MODEL_WEIGHTS_PATH = 'models/best_helmet.pt'
```

## Dependencies

- **FastAPI**: Web framework
- **Uvicorn**: ASGI server
- **Ultralytics**: YOLO models
- **OpenCV**: Video processing
- **DeepFace**: Face recognition
- **Supervision**: Computer vision utilities
- **NumPy**: Numerical operations

## Testing

### Test API Endpoints

```powershell
# Health check
curl http://localhost:8000

# Helmet detection
curl http://localhost:8000/api/status/helmet

# Loitering detection
curl http://localhost:8000/api/status/loitering

# Production counter
curl http://localhost:8000/api/status/counting

# Attendance system
curl http://localhost:8000/api/status/attendance
```

## Troubleshooting

### Camera Not Working
- Check camera permissions
- Try different VIDEO_SOURCE values (0, 1, 2)
- Ensure no other app is using the camera

### Model Loading Error
- Verify model files exist in `models/` folder
- Check file paths in service files
- Ensure models are compatible with Ultralytics version

### DeepFace Not Found
```powershell
pip install deepface
```

### Import Errors
```powershell
# From backend directory
pip install -r requirements.txt
```

## Performance Optimization

1. **Use GPU**: Install CUDA for faster inference
2. **Reduce Resolution**: Lower camera resolution
3. **Adjust Intervals**: Increase recognition intervals
4. **Use Smaller Models**: Switch to lighter YOLO models

## CORS Configuration

CORS is enabled in `app/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

For production, change to specific origins:
```python
allow_origins=["https://your-domain.com"],
```

## License

Internal use only - Factory Safety Monitoring System
