# Module 2: Vehicle & Gate Management - Quick Start Guide

**Fast-track integration in 30 minutes** ⚡

---

## 5-Step Integration Process

### Step 1: Copy Files (2 minutes)

```bash
# Copy the 3 implementation files to backend directories

cp vehicle_gate_service.py backend/services/
cp vehicle_models.py backend/detection_system/
cp vehicle_endpoints.py backend/detection_system/
```

### Step 2: Install Dependencies (5 minutes)

```bash
cd backend

# Install Python dependencies
pip install ultralytics>=8.0.0        # YOLOv8
pip install easyocr>=1.7.0             # License plate OCR
pip install opencv-python>=4.5.0       # Image processing
pip install bytetrack>=1.3.0           # Vehicle tracking
pip install sqlalchemy>=2.0.0          # Database ORM
pip install psycopg2-binary>=2.9.0    # PostgreSQL driver
```

### Step 3: Configure Database (8 minutes)

**Create PostgreSQL database:**
```bash
psql -U postgres
```

```sql
-- In PostgreSQL terminal
CREATE DATABASE factory_vehicles;
CREATE USER vehicle_user WITH PASSWORD 'SecurePassword123';
GRANT ALL PRIVILEGES ON DATABASE factory_vehicles TO vehicle_user;
\q
```

**Create `.env` file in `backend/` directory:**
```env
DATABASE_URL=postgresql://vehicle_user:SecurePassword123@localhost:5432/factory_vehicles
YOLO_MODEL_PATH=models/yolov8n.pt
OCR_ENGINE=easyocr
OCR_CONFIDENCE=0.6
GATE_ZONE_PERCENTAGE=0.3
SNAPSHOT_DIR=snapshots/vehicles
USE_GPU=true
SESSION_TIMEOUT=300
```

### Step 4: Initialize Database (5 minutes)

```python
# Create init_db.py in backend/
from backend.detection_system.vehicle_endpoints import init_vehicle_module
import os

database_url = os.getenv("DATABASE_URL", "postgresql://vehicle_user:SecurePassword123@localhost:5432/factory_vehicles")

print("Initializing vehicle module...")
success = init_vehicle_module(
    database_url=database_url,
    model_path="models/yolov8n.pt",
    ocr_engine="easyocr",
    use_gpu=True
)

if success:
    print("✓ Vehicle module initialized successfully!")
else:
    print("✗ Failed to initialize vehicle module")
```

**Run:**
```bash
python backend/init_db.py
```

### Step 5: Integrate with FastAPI (10 minutes)

**Update your main FastAPI app (`backend/main.py` or similar):**

```python
from fastapi import FastAPI
from backend.detection_system.vehicle_endpoints import router as vehicle_router, init_vehicle_module
import os

app = FastAPI(title="Factory Safety System with Vehicle Gate Management")

# Initialize vehicle module at startup
@app.on_event("startup")
async def startup_event():
    database_url = os.getenv("DATABASE_URL")
    success = init_vehicle_module(
        database_url=database_url,
        model_path="models/yolov8n.pt",
        ocr_engine="easyocr",
        use_gpu=True
    )
    if not success:
        print("WARNING: Vehicle module failed to initialize")

# Include vehicle router
app.include_router(vehicle_router, prefix="/api", tags=["vehicle_management"])

# Health check
@app.get("/health")
async def health():
    return {"status": "healthy", "modules": ["vehicle_gate"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Start the app:**
```bash
python backend/main.py
# OR
uvicorn backend.main:app --reload
```

---

## Verification Checklist

✅ **Database Connection**
```bash
curl http://localhost:8000/api/module2/health
# Response: {"status":"healthy",...}
```

✅ **Register Test Vehicle**
```bash
curl -X POST http://localhost:8000/api/module2/vehicle/register \
  -H "Content-Type: application/json" \
  -d '{
    "plate_number": "TEST001",
    "owner_name": "Test Company",
    "vehicle_type": "car",
    "category": "vendor",
    "status": "allowed"
  }'
```

✅ **List Vehicles**
```bash
curl http://localhost:8000/api/module2/vehicles
```

✅ **Get Statistics**
```bash
curl http://localhost:8000/api/module2/statistics
```

---

## Quick Examples

### Example 1: Process a Single Image

```python
import cv2
import base64
import requests

# Read image
frame = cv2.imread("gate_camera.jpg")
_, buffer = cv2.imencode('.jpg', frame)
frame_b64 = base64.b64encode(buffer).decode()

# Send to API
response = requests.post(
    "http://localhost:8000/api/module2/process-frame",
    json={
        "frame_base64": frame_b64,
        "frame_index": 0
    }
)

result = response.json()
print(f"Vehicles detected: {result['vehicles_detected']}")
print(f"Plates recognized: {result['plates_recognized']}")
print(f"Alerts: {result['alerts_triggered']}")
```

### Example 2: Register Multiple Vehicles from CSV

```python
import csv
import requests

with open('vehicles.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        response = requests.post(
            "http://localhost:8000/api/module2/vehicle/register",
            json={
                "plate_number": row['plate'],
                "owner_name": row['owner'],
                "vehicle_type": row['type'],
                "category": row['category'],
                "status": row['status']
            }
        )
        if response.status_code == 200:
            print(f"✓ Registered {row['plate']}")
        else:
            print(f"✗ Failed to register {row['plate']}: {response.text}")
```

### Example 3: Get Daily Summary

```python
import requests
from datetime import datetime

# Get today's summary
response = requests.get(
    "http://localhost:8000/api/module2/access-logs/daily-summary",
    params={"date": datetime.now().strftime("%Y-%m-%d")}
)

summary = response.json()
print(f"Total vehicles today: {summary['total_vehicles']}")
print(f"Authorized: {summary['authorized_count']}")
print(f"Blocked: {summary['blocked_count']}")
print(f"Unknown: {summary['unknown_count']}")
print(f"Peak hour: {summary['peak_hour']}")
```

### Example 4: Block a Plate

```python
import requests

# Find vehicle first
vehicles = requests.get("http://localhost:8000/api/module2/vehicles").json()
vehicle_id = next(v['id'] for v in vehicles if v['plate_number'] == 'ABC123')

# Update status
response = requests.put(
    f"http://localhost:8000/api/module2/vehicles/{vehicle_id}/status",
    json={
        "status": "blocked",
        "reason": "Vehicle reported stolen"
    }
)

print(f"Status updated: {response.json()['status']}")
```

---

## Troubleshooting

### "Module not found" error

```bash
# Verify file locations
ls -la backend/services/vehicle_gate_service.py
ls -la backend/detection_system/vehicle_models.py
ls -la backend/detection_system/vehicle_endpoints.py

# Add to PYTHONPATH if needed
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"
```

### "Database connection refused"

```bash
# Check PostgreSQL is running
psql -U postgres -c "SELECT version();"

# If not running
pg_ctl start -D /path/to/data  # macOS/Linux
# OR
"C:\Program Files\PostgreSQL\14\bin\pg_ctl" start  # Windows
```

### "YOLO model not found"

```python
# Auto-download model
from ultralytics import YOLO
model = YOLO("yolov8n.pt")  # Downloads if missing
```

### "OCR engine not initialized"

```bash
# Install EasyOCR
pip install easyocr

# Or PaddleOCR (alternative)
pip install paddlepaddle paddleocr
```

### Low FPS / Slow processing

```python
# Reduce gate zone for faster processing
service = VehicleGateService(
    gate_zone_percentage=0.2,      # Smaller zone
    confidence_threshold=0.6,       # Higher threshold
    ocr_confidence=0.7             # More selective
)

# Or use CPU-optimized model
service = VehicleGateService(
    model_path="yolov8n.pt",       # Nano model
    use_gpu=False                  # CPU only
)
```

---

## API Endpoints Quick Reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/module2/process-frame` | Process video frame |
| POST | `/api/module2/vehicle/register` | Register new vehicle |
| GET | `/api/module2/vehicles` | List vehicles |
| GET | `/api/module2/vehicles/{id}` | Get vehicle details |
| PUT | `/api/module2/vehicles/{id}/status` | Update vehicle status |
| GET | `/api/module2/access-logs` | Query access logs |
| GET | `/api/module2/access-logs/daily-summary` | Daily statistics |
| GET | `/api/module2/access-logs/monthly-summary` | Monthly statistics |
| POST | `/api/module2/access-logs/{id}/flag` | Flag for review |
| GET | `/api/module2/alerts` | Get recent alerts |
| GET | `/api/module2/statistics` | Service statistics |
| GET | `/api/module2/health` | Health check |

---

## Next Steps

1. **Load Camera Stream:** Update frame processing to use RTSP stream
2. **Configure Snapshots:** Adjust snapshot quality and retention
3. **Set Up Alerts:** Configure email/SMS notifications
4. **Customize ROI:** Adjust gate zone percentage for your camera
5. **Tune Performance:** Adjust confidence thresholds
6. **Monitor Logs:** Check `backend/logs/vehicle_gate.log`

---

## Performance Expectations

| Metric | Typical | Optimized |
|--------|---------|-----------|
| Detection | 30-50ms | 20-30ms |
| Tracking | 5-10ms | 2-5ms |
| ANPR | 150-300ms | 100-150ms |
| **Total FPS** | 10-20 | 15-30 |

---

**For detailed documentation, see `MODULE_2_IMPLEMENTATION_GUIDE.md`**
