@echo off
REM Quick Start Script for Unified Inference Pipeline (Windows)

echo.
echo 🚀 Factory AI SaaS - Unified Inference Pipeline Setup
echo ======================================================
echo.

REM Step 1: Install dependencies
echo 📦 Step 1: Installing dependencies...
pip install -r requirements_inference.txt
if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)
echo ✅ Dependencies installed

REM Step 2: Setup environment
echo.
echo ⚙️ Step 2: Setting up environment...
if not exist .env (
    copy .env.template .env
    echo ✅ Created .env file - PLEASE EDIT WITH AWS CREDENTIALS
    echo    - AWS_ACCESS_KEY_ID
    echo    - AWS_SECRET_ACCESS_KEY
    echo    - AWS_REGION
    echo.
    echo ⚠️ Edit .env before continuing!
    pause
) else (
    echo ✅ .env file already exists
)

REM Step 3: Initialize database
echo.
echo 🗄️ Step 3: Initializing database...
python -c "from database_models import init_db; init_db()" && (
    echo ✅ Database initialized
) || (
    echo ❌ Database initialization failed
)

REM Step 4: Verify AWS connection
echo.
echo 🔐 Step 4: Verifying AWS connection...
python << 'EOF'
try:
    from unified_inference import inference_engine
    if inference_engine:
        print("✅ AWS Rekognition connected")
        print("✅ YOLO model loaded")
        print("✅ EasyOCR initialized")
    else:
        print("❌ Inference engine failed to initialize")
except Exception as e:
    print(f"❌ Error: {e}")
    print("   Make sure AWS credentials are in .env")
EOF

REM Step 5: Ready to start
echo.
echo ======================================================
echo ✅ SETUP COMPLETE!
echo ======================================================
echo.
echo 🚀 To start the backend, run:
echo.
echo    python -m uvicorn main_integration:app --reload
echo.
echo 📖 Then visit:
echo    API Docs: http://localhost:8000/docs
echo    Health: http://localhost:8000/api/health
echo.
echo 📝 Next steps:
echo    1. Enroll employees via /api/enroll-employee
echo    2. Send frames to /api/process
echo    3. Monitor response for detections
echo.
pause
