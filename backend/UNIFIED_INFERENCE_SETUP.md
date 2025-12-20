# 🚀 Unified Inference Pipeline - Complete Setup Guide

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│          UNIFIED INFERENCE ENGINE (unified_inference.py)    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. YOLOv8 Detection & Tracking                            │
│     ├─ Person detection                                    │
│     ├─ Vehicle detection (car, truck, bus, motorcycle)    │
│     └─ Track ID assignment                                │
│                                                             │
│  2. Face Recognition Pipeline                             │
│     ├─ Crop face from frame                              │
│     ├─ Check local cache (save AWS costs)                │
│     ├─ Query AWS Rekognition if new track_id            │
│     └─ Cache result for 10 minutes                       │
│                                                             │
│  3. Vehicle ANPR                                          │
│     ├─ Detect license plate region                       │
│     ├─ Run local EasyOCR                                 │
│     └─ Return plate number                               │
│                                                             │
│  4. Occupancy & Line Crossing                            │
│     ├─ Track centroid movement                           │
│     ├─ Detect line crossing (Entry/Exit)               │
│     └─ Update occupancy count                            │
│                                                             │
│  5. Database Logging                                      │
│     ├─ Log recognized faces → attendance_records        │
│     ├─ Log vehicles → vehicle_logs                       │
│     └─ Log occupancy → occupancy_logs                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Step 1: Install Dependencies

### Python Packages
```bash
pip install ultralytics opencv-python numpy easyocr boto3 python-dotenv sqlalchemy
```

### Download YOLOv8 Model
The model auto-downloads on first run. To pre-download:
```bash
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

Model sizes:
- `yolov8n.pt` (13MB) - Nano, fastest ✅ Recommended
- `yolov8s.pt` (23MB) - Small
- `yolov8m.pt` (50MB) - Medium
- `yolov8l.pt` (100MB) - Large

---

## Step 2: AWS Setup

### A. Create IAM User with Rekognition Access

1. Go to AWS Console → IAM → Users
2. Create new user: `factory-ai-app`
3. Attach policies:
   - `AmazonRekognitionFullAccess`
   - OR create custom policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "rekognition:SearchFacesByImage",
        "rekognition:IndexFaces",
        "rekognition:DeleteFaces",
        "rekognition:DescribeCollection",
        "rekognition:CreateCollection"
      ],
      "Resource": "*"
    }
  ]
}
```

4. Create access key → Copy `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`

### B. Configure .env File

```bash
cp .env.template .env
```

Edit `.env`:
```
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_COLLECTION_ID=factory-employees
```

### C. Verify AWS Connection

```bash
python -c "
from unified_inference import AWSFaceRecognition
aws = AWSFaceRecognition()
print('✅ AWS connected!')
"
```

---

## Step 3: Database Setup

### Create Tables

```bash
python -c "from database_models import init_db; init_db()"
```

Output: `✅ Database tables created`

### For PostgreSQL (Production)

```bash
# Install PostgreSQL driver
pip install psycopg2

# Update .env
DATABASE_URL=postgresql://user:password@localhost:5432/factory_ai

# Create tables
python -c "from database_models import init_db; init_db()"
```

---

## Step 4: Start the Backend

### Run FastAPI Server

```bash
cd backend

# With hot-reload (development)
python -m uvicorn main_integration:app --reload --port 8000

# Without reload (production)
python -m uvicorn main_integration:app --host 0.0.0.0 --port 8000
```

### Verify Startup

```
✅ YOLO model loaded
✅ AWS Rekognition initialized
✅ EasyOCR initialized
✅ Database tables created
✅ All components initialized
INFO: Application startup complete
```

---

## Step 5: Test the Inference Pipeline

### Test 1: Health Check

```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "occupancy": true,
    "video": true,
    "vehicle": true,
    "identity": true,
    "attendance": true
  }
}
```

### Test 2: Process a Sample Image

```python
import requests
import base64

# Read and encode image
with open('sample_frame.jpg', 'rb') as f:
    frame_base64 = base64.b64encode(f.read()).decode()

# Send to backend
response = requests.post(
    'http://localhost:8000/api/process',
    json={'frame': frame_base64}
)

print(response.json())
```

### Test 3: Enroll an Employee

```bash
curl -X POST http://localhost:8000/api/enroll-employee \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": "E001",
    "employee_name": "John Doe",
    "frame": "base64_photo_here"
  }'
```

---

## API Response Format

### POST /api/process

**Request:**
```json
{
  "frame": "base64_encoded_image"
}
```

**Response:**
```json
{
  "success": true,
  "frame_id": 123,
  "timestamp": "2025-12-20T14:30:45.123Z",
  
  "occupancy": 42,
  "entries": 150,
  "exits": 108,
  "entries_this_frame": 2,
  "exits_this_frame": 1,
  
  "faces_recognized": [
    {
      "track_id": 1,
      "name": "John Doe",
      "confidence": 95.5,
      "source": "aws"  // or "cache"
    }
  ],
  
  "vehicles_detected": [
    {
      "track_id": 2,
      "type": "car",
      "plate": "KA01AB1234",
      "confidence": 0.87
    }
  ],
  
  "people_count": 5,
  "vehicle_count": 2,
  "processing_time_ms": 145.32
}
```

---

## Performance & Costs

### Processing Speed (Per Frame)

| Model | FPS | Hardware |
|-------|-----|----------|
| YOLOv8n | 60-90 | CPU |
| YOLOv8n | 120+ | GPU |
| AWS Rekognition | N/A | Cloud |
| EasyOCR | 5-10 | CPU |

**Typical frame:** 150ms per frame = 6-7 FPS per camera on CPU

### AWS Costs

**Per 1000 image searches (face matching):**
```
$1.00
```

**Example:**
- 1 camera, 7 FPS = 604,800 images/day
- New faces only 10% = 60,480 AWS calls/day
- Cost = ~$60.48/month per camera
```

**Optimization:**
- Local cache reduces AWS calls by 70-90%
- Share employee dataset across cameras
- Batch process during off-hours

---

## Configuration Tuning

### Face Recognition

```python
# In unified_inference.py

# Increase confidence threshold (stricter matching)
confidence_threshold=0.90  # Default: 0.85

# Increase cache TTL (more reuse, lower AWS cost)
cache_ttl_seconds=1800  # Default: 600 (10 mins)
```

### Occupancy Counting

```python
# Change virtual line position
self.line_y = 350  # Pixels from top

# Multi-line support for better accuracy
self.line_y = [300, 350, 400]  # Entry, Center, Exit
```

### Vehicle Detection

```python
# Confidence threshold for vehicle detection
conf_threshold=0.5  # Higher = stricter, fewer detections
```

---

## Troubleshooting

### Issue 1: AWS Authentication Error

```
❌ botocore.exceptions.NoCredentialsError
```

**Solution:**
```bash
# Verify .env file
echo $AWS_ACCESS_KEY_ID
echo $AWS_SECRET_ACCESS_KEY

# Or use AWS CLI
aws configure
```

### Issue 2: YOLO Model Too Slow

```
❌ Processing frame takes > 500ms
```

**Solution:**
- Use smaller model: `yolov8n.pt` instead of `yolov8m.pt`
- Run on GPU: Install `torch` with CUDA
- Reduce frame resolution: 480p instead of 1080p

### Issue 3: Low Face Recognition Accuracy

```
❌ Known employees not recognized
```

**Solution:**
- Increase confidence threshold: `confidence_threshold = 0.80`
- Enroll multiple photos per employee (different angles)
- Ensure good lighting in enrollment photos
- Calibrate camera angle for best face capture

### Issue 4: Line Crossing Not Detecting

```
❌ Occupancy not changing
```

**Solution:**
- Adjust `line_y` coordinate to match actual crossing area
- Ensure people fully cross the line (not just touch it)
- Reduce person detection threshold if people being missed

---

## Database Queries

### Get Today's Check-Ins

```python
from database_models import SessionLocal, AttendanceRecord
from datetime import date

db = SessionLocal()
today = date.today()

checkins = db.query(AttendanceRecord).filter(
    AttendanceRecord.check_in_time >= f"{today} 00:00:00"
).all()

for record in checkins:
    print(f"{record.employee_name}: {record.check_in_time}")
```

### Get Vehicle Entry Count

```python
from database_models import SessionLocal, VehicleLog
from datetime import datetime, timedelta

db = SessionLocal()
today = datetime.now() - timedelta(days=1)

vehicles = db.query(VehicleLog).filter(
    VehicleLog.entry_time >= today
).count()

print(f"Vehicles entered today: {vehicles}")
```

### Get Peak Occupancy Hour

```python
from database_models import SessionLocal, OccupancyDailyAggregate
from datetime import date

db = SessionLocal()
today = date.today()

peak = db.query(OccupancyDailyAggregate).filter(
    OccupancyDailyAggregate.occupancy_date == str(today)
).order_by(
    OccupancyDailyAggregate.max_occupancy.desc()
).first()

print(f"Peak: {peak.max_occupancy} people at hour {peak.hour}")
```

---

## Production Deployment

### Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main_integration:app", "--host", "0.0.0.0", "--port", "8000"]
```

### AWS EC2 + RDS

```bash
# Create RDS PostgreSQL database
# Update DATABASE_URL in .env

# SSH into EC2
ssh -i key.pem ubuntu@instance-ip

# Clone repo
git clone <repo>
cd factory-ai-backend

# Install and run
pip install -r requirements.txt
python -m uvicorn main_integration:app --host 0.0.0.0 --port 8000
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: factory-ai-backend
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: backend
        image: factory-ai:latest
        ports:
        - containerPort: 8000
        env:
        - name: AWS_ACCESS_KEY_ID
          valueFrom:
            secretKeyRef:
              name: aws-credentials
              key: access-key
```

---

## Monitoring & Logging

### Real-time Logs

```bash
# Watch inference pipeline
tail -f backend.log | grep "Frame processed"

# Watch AWS costs
grep "aws_cost" backend.log
```

### Performance Metrics

```python
# Query system metrics
from database_models import SessionLocal, SystemMetric

db = SessionLocal()
metrics = db.query(SystemMetric).all()

avg_time = sum(m.processing_time_ms for m in metrics) / len(metrics)
print(f"Average processing: {avg_time:.1f}ms")

aws_calls = sum(m.aws_calls for m in metrics)
print(f"AWS Rekognition calls: {aws_calls}")
```

---

## Summary

✅ **You now have:**
- Real YOLOv8 detection + AWS Rekognition integration
- Face caching to reduce costs
- Line crossing for occupancy
- License plate reading with EasyOCR
- Database logging for all events
- Production-ready FastAPI endpoint

**Next steps:**
1. Configure `.env` with AWS credentials
2. Run `python -c "from database_models import init_db; init_db()"`
3. Start: `python -m uvicorn main_integration:app --reload`
4. Test: Send frames to `/api/process`
5. Deploy with Docker or Kubernetes

