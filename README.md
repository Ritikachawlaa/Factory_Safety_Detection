# 🏭 Factory Safety Detector

A comprehensive real-time factory safety monitoring system using AI/ML for helmet detection, loitering detection, production counting, and attendance tracking.

## 📁 Project Structure

```
factory_safety_detector/
│
├── backend/                      # Backend API & ML Models
│   ├── app/                      # FastAPI application
│   ├── models/                   # YOLO & ML models
│   ├── database/                 # Employee photos
│   ├── config/                   # Configuration files
│   ├── scripts/                  # Standalone scripts
│   └── requirements.txt          # Python dependencies
│
├── frontend/                     # Angular Frontend
│   ├── src/                      # Source code
│   ├── package.json              # Node dependencies
│   └── angular.json              # Angular config
│
├── start.bat                     # Windows quick start
├── start.ps1                     # PowerShell quick start
└── *.md                          # Documentation
```

## 🚀 Quick Start

### Option 1: Automatic Start (Recommended)

**PowerShell:**
```powershell
.\start.ps1
```

**Command Prompt:**
```cmd
start.bat
```

This will:
- Start backend on http://localhost:8000
- Start frontend on http://localhost:4200
- Open browser automatically

### Option 2: Manual Start

**Terminal 1 - Backend:**
```powershell
cd backend
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```powershell
cd frontend
npm install  # First time only
ng serve
```

**Access:** http://localhost:4200

## 📋 Prerequisites

### Backend
- Python 3.8+
- Webcam or video source
- Python packages (see backend/requirements.txt)

### Frontend
- Node.js 18+
- npm 9+
- Angular CLI 17+

## 🔧 Installation

### 1. Backend Setup

```powershell
cd backend
pip install -r requirements.txt
```

### 2. Frontend Setup

```powershell
cd frontend
npm install -g @angular/cli
npm install
```

### 3. Employee Database (Optional)

Add employee photos to `backend/database/employees/`:
- Format: `firstname.jpg` or `firstname.png`
- Example: `john.jpg`, `mary.png`

## 🎯 Features

### 🪖 Helmet Detection
- Real-time helmet compliance monitoring
- Counts people with/without helmets
- Calculates compliance percentage
- Visual alerts for violations

### 👥 Loitering Detection
- Tracks groups of people
- Monitors proximity and duration
- Configurable thresholds
- Alert system for violations

### 📦 Production Counter
- Counts boxes crossing detection line
- Tracks multiple box types
- Real-time counting
- Cumulative statistics

### ✓ Attendance System
- Face recognition based tracking
- Employee verification
- Timestamped activity logs
- Daily attendance records

## 📊 System Architecture

```
Camera/Video → ML Models → FastAPI → Angular → Browser
    ↓            ↓           ↓         ↓        ↓
  Frames      YOLO/      JSON      HTTP    Dashboard
             DeepFace    API      Client   Display
```

## 🌐 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Health check |
| `GET /api/status/helmet` | Helmet detection data |
| `GET /api/status/loitering` | Loitering detection data |
| `GET /api/status/counting` | Production counter data |
| `GET /api/status/attendance` | Attendance system data |

API Docs: http://localhost:8000/docs

## 📖 Documentation

- **INSTALLATION.md** - Quick installation guide
- **SETUP_GUIDE.md** - Detailed setup instructions
- **FRONTEND_INTEGRATION_GUIDE.md** - Technical integration details
- **ARCHITECTURE.md** - System architecture diagrams
- **backend/README.md** - Backend documentation
- **frontend/README.md** - Frontend documentation

## 🎨 Technology Stack

### Backend
- FastAPI - Web framework
- Ultralytics YOLO - Object detection
- DeepFace - Face recognition
- OpenCV - Video processing
- Uvicorn - ASGI server

### Frontend
- Angular 17 - Web framework
- TypeScript - Programming language
- RxJS - Reactive programming
- HttpClient - API communication

## 🔒 Security Notes

**Current Configuration (Development):**
- CORS allows all origins
- No authentication
- HTTP (not HTTPS)

**For Production:**
- Change CORS to specific domains
- Add authentication
- Use HTTPS
- Implement rate limiting
- Secure employee database

## 🐛 Troubleshooting

### Backend Issues
```powershell
# Model not found
# Ensure models exist in backend/models/

# Camera not working
# Try different VIDEO_SOURCE (0, 1, 2)

# Import errors
cd backend
pip install -r requirements.txt
```

### Frontend Issues
```powershell
# Dependencies not installed
cd frontend
npm install

# Port already in use
ng serve --port 4300

# Connection refused
# Ensure backend is running on port 8000
```

## 📈 Performance Tips

1. Use GPU for faster ML inference
2. Reduce video resolution
3. Adjust polling intervals
4. Use lighter YOLO models
5. Close unused browser tabs

## 🎓 Getting Started Tutorial

1. **Install Dependencies**
   ```powershell
   cd backend
   pip install -r requirements.txt
   cd ../frontend
   npm install
   cd ..
   ```

2. **Add Employee Photos** (optional)
   - Add photos to `backend/database/employees/`
   - Format: `firstname.jpg`

3. **Start Services**
   ```powershell
   .\start.ps1
   ```

4. **Open Dashboard**
   - Browser opens automatically
   - Or visit: http://localhost:4200

5. **Monitor Systems**
   - View real-time statistics
   - Check compliance rates
   - Review activity logs

## 🔄 Update Frequency

- Helmet Detection: 2 seconds
- Loitering Detection: 2 seconds
- Production Counter: 2 seconds
- Attendance System: 5 seconds

## 📞 Support

For issues:
1. Check documentation in `*.md` files
2. Verify all prerequisites are installed
3. Check terminal output for errors
4. Test API endpoints directly
5. Check browser console (F12)

## 📝 Version

**v1.0** - Initial release with complete frontend-backend integration

## 🎉 Ready to Use!

Run the quick start script and visit http://localhost:4200

```powershell
.\start.ps1
```

Enjoy your Factory Safety Detector! 🚀
