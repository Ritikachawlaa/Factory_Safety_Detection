# 🚀 FastAPI Backend - Factory Safety Detection System

## Overview

This is a complete FastAPI backend that handles:
- ✅ Real-time ML inference (YOLO + DeepFace)
- ✅ Data persistence (JSON-based storage)
- ✅ API documentation (auto-generated)
- ✅ CORS support for Angular frontend
- ✅ Concurrent request handling

## Installation

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Verify Installation

```bash
pip list | grep -E "fastapi|uvicorn|ultralytics|opencv|deepface"
```

## Running the Server

### Method 1: Direct Python Execution

```bash
cd backend
python -m app.main
```

### Method 2: Using Uvicorn

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Method 3: Background/Production Mode

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Access Points

- **Main API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## API Endpoints

### Core Detection Endpoints

#### Helmet Detection
- `GET /api/status/helmet` - Get current status
- `POST /api/live/helmet/` - Process webcam frame
- `GET /api/stats/helmet/` - Get statistics
- `GET /api/helmet-detection/` - Get historical records

#### Loitering Detection
- `GET /api/status/loitering` - Get current status
- `POST /api/live/loitering/` - Process webcam frame
- `GET /api/stats/loitering/` - Get statistics

#### Production Counter
- `GET /api/status/counting` - Get current count
- `POST /api/live/production/` - Process webcam frame
- `POST /api/live/production/reset/` - Reset counter
- `GET /api/production/today/` - Get today's summary

#### Attendance System
- `GET /api/status/attendance` - Get current status
- `POST /api/live/attendance/` - Process webcam frame
- `GET /api/stats/attendance/` - Get statistics

### Management Endpoints

#### Employee Management
- `GET /api/employees/` - List all employees
- `POST /api/employees/` - Create employee
- `GET /api/employees/{id}` - Get employee by ID
- `GET /api/employees/search/?q=name` - Search employees

#### System Logs
- `GET /api/system-logs/` - Get system logs (default limit: 50)

#### Configuration
- `GET /api/config/system/` - Get system config
- `POST /api/config/system/` - Update system config
- `GET /api/config/modules/` - Get module config
- `POST /api/config/modules/` - Update module config

#### Violations
- `GET /api/violations/helmet/` - Get helmet violations
- `GET /api/violations/loitering/` - Get loitering alerts

## Data Storage

All data is stored in JSON files in the `backend/data/` directory:

```
backend/data/
├── helmet_detections.json       # Helmet detection records
├── loitering_detections.json    # Loitering incident logs
├── production_counts.json       # Production counter data
├── employees.json               # Employee database
├── system_logs.json             # System event logs
├── system_config.json           # System configuration
└── module_config.json           # Module settings
```

## Request/Response Examples

### POST /api/live/helmet/

**Request**:
```json
{
  "frame": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAA..."
}
```

**Response**:
```json
{
  "timestamp": "2025-12-14T10:30:00",
  "totalPeople": 5,
  "compliantCount": 4,
  "violationCount": 1,
  "complianceRate": 80.0
}
```

### POST /api/employees/

**Request**:
```json
{
  "employee_id": "EMP001",
  "first_name": "John",
  "last_name": "Doe",
  "department": "Manufacturing",
  "position": "Operator",
  "is_active": true
}
```

**Response**:
```json
{
  "id": 1,
  "employee_id": "EMP001",
  "first_name": "John",
  "last_name": "Doe",
  "department": "Manufacturing",
  "position": "Operator",
  "is_active": true,
  "created_at": "2025-12-14T10:30:00"
}
```

## Key Features

### 1. Auto-Generated Documentation
FastAPI automatically generates interactive API documentation:
- **Swagger UI**: Try out APIs directly in the browser
- **ReDoc**: Clean, readable API documentation
- **OpenAPI Schema**: Standard API specification

### 2. Type Safety & Validation
- Pydantic models for request/response validation
- Automatic type checking
- Clear error messages

### 3. Async Support
- Non-blocking I/O operations
- High concurrency handling
- Efficient resource usage

### 4. Concurrent ML Inference
- ThreadPoolExecutor with 4 workers
- Prevents blocking on ML operations
- Multiple simultaneous detections

### 5. CORS Support
- Configured for Angular frontend (localhost:4200)
- Easy to update for production

## Configuration

### Update CORS Origins

Edit `backend/app/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://your-production-domain.com"],  # Update this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Enable GPU Acceleration

Edit service files in `backend/app/services/`:

```python
# Change from:
device='cpu'

# To:
device='cuda'
half=True
```

## Migrating from Django

### What Was Removed
- ❌ Django ORM
- ❌ Django REST Framework
- ❌ Django Admin Panel
- ❌ Django Channels
- ❌ PostgreSQL dependencies

### What Replaced It
- ✅ FastAPI with Pydantic
- ✅ JSON file storage
- ✅ Swagger UI for API testing
- ✅ Native WebSocket support (ready to implement)
- ✅ Optional database support (SQLAlchemy)

## Future Enhancements

### Add Database Support (Optional)

1. Install dependencies:
```bash
pip install sqlalchemy psycopg2-binary alembic
```

2. Create database models using SQLAlchemy
3. Replace JSON storage with database queries

### Implement WebSocket

FastAPI has native WebSocket support:

```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_json()
        # Process and send back results
        await websocket.send_json({"result": data})
```

### Add Authentication

```python
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
import jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Authenticate user and return JWT token
    pass
```

## Troubleshooting

### Port Already in Use

```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

### ML Models Not Found

Ensure models are in `backend/models/`:
```
backend/models/
├── best_helmet.pt
├── best_product.pt
└── (DeepFace models auto-download)
```

### CORS Errors

Check that frontend URL matches CORS configuration in `main.py`.

## Development vs Production

### Development (Current)
```bash
uvicorn app.main:app --reload --port 8000
```

### Production
```bash
# Use multiple workers
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Or use Gunicorn + Uvicorn workers
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## Performance Tips

1. **Enable GPU**: Change `device='cpu'` to `device='cuda'`
2. **Adjust Workers**: More workers = more concurrent requests
3. **Optimize Frame Size**: Reduce image resolution before sending
4. **Batch Processing**: Process multiple frames together
5. **Caching**: Cache ML model outputs for similar frames

## Support

For issues or questions:
1. Check FastAPI docs: https://fastapi.tiangolo.com
2. Check Swagger UI: http://localhost:8000/docs
3. Review system logs: `backend/data/system_logs.json`

---

**Version**: 2.0.0  
**Last Updated**: December 14, 2025  
**Backend Framework**: FastAPI  
**Python**: 3.8+
