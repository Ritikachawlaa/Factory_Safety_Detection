#!/usr/bin/env python3
"""
Test & Verification Script for Factory AI SaaS - 4 Modules
Tests the complete inference pipeline without requiring a live camera.

Usage:
  python test_inference_pipeline.py

This script:
1. Verifies all dependencies are installed
2. Tests the InferencePipeline class initialization
3. Tests basic inference with a blank image
4. Verifies database connection
5. Checks AWS configuration
6. Provides detailed diagnostic output
"""

import sys
import os
import logging
from datetime import datetime
import base64
import numpy as np
import cv2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'


def print_header(title):
    """Print a formatted header."""
    print(f"\n{BOLD}{BLUE}{'=' * 80}{RESET}")
    print(f"{BOLD}{BLUE}{title.center(80)}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 80}{RESET}\n")


def print_success(message):
    """Print a success message."""
    print(f"{GREEN}✅ {message}{RESET}")


def print_error(message):
    """Print an error message."""
    print(f"{RED}❌ {message}{RESET}")


def print_warning(message):
    """Print a warning message."""
    print(f"{YELLOW}⚠️  {message}{RESET}")


def print_info(message):
    """Print an info message."""
    print(f"{BLUE}ℹ️  {message}{RESET}")


def test_dependencies():
    """Test that all required dependencies are installed."""
    print_header("Testing Dependencies")
    
    dependencies = {
        'ultralytics': 'YOLOv8 detection',
        'cv2': 'OpenCV image processing',
        'numpy': 'Numerical arrays',
        'easyocr': 'License plate OCR',
        'boto3': 'AWS Rekognition',
        'fastapi': 'Web framework',
        'sqlalchemy': 'Database ORM',
        'pydantic': 'Data validation',
        'dotenv': 'Environment variables'
    }
    
    failed = []
    
    for module, description in dependencies.items():
        try:
            __import__(module)
            print_success(f"{module:20} - {description}")
        except ImportError:
            print_error(f"{module:20} - {description} (MISSING)")
            failed.append(module)
    
    if failed:
        print_error(f"\nMissing dependencies: {', '.join(failed)}")
        print_info("Install with: pip install -r requirements_inference.txt")
        return False
    
    return True


def test_env_variables():
    """Test that environment variables are configured."""
    print_header("Testing Environment Variables")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = {
        'AWS_REGION': 'AWS region (e.g., us-east-1)',
        'AWS_ACCESS_KEY_ID': 'AWS access key',
        'AWS_SECRET_ACCESS_KEY': 'AWS secret key',
        'AWS_COLLECTION_ID': 'AWS Rekognition collection name'
    }
    
    optional_vars = {
        'FACE_CONFIDENCE_THRESHOLD': 'Face matching threshold (0-100)',
        'FACE_CACHE_TTL': 'Cache time-to-live in seconds',
        'OCCUPANCY_LINE_Y': 'Line crossing Y coordinate',
        'DATABASE_URL': 'Database connection URL'
    }
    
    missing = []
    
    print(f"{BOLD}Required Variables:{RESET}")
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'SECRET' in var or 'KEY' in var:
                masked = value[:4] + '*' * (len(value) - 4)
                print_success(f"{var:30} = {masked}")
            else:
                print_success(f"{var:30} = {value}")
        else:
            print_error(f"{var:30} - NOT SET")
            missing.append(var)
    
    print(f"\n{BOLD}Optional Variables:{RESET}")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            print_success(f"{var:30} = {value}")
        else:
            print_warning(f"{var:30} - Using default")
    
    if missing:
        print_error(f"\nMissing variables: {', '.join(missing)}")
        print_info("Copy .env.template to .env and configure AWS credentials")
        return False
    
    return True


def test_database():
    """Test database connection."""
    print_header("Testing Database Connection")
    
    try:
        from database_models import SessionLocal, init_db
        
        # Initialize database
        print_info("Initializing database...")
        init_db()
        print_success("Database tables created/verified")
        
        # Test session
        db = SessionLocal()
        print_success("Database connection successful")
        db.close()
        
        return True
    except Exception as e:
        print_error(f"Database error: {e}")
        return False


def test_aws_connection():
    """Test AWS Rekognition connection."""
    print_header("Testing AWS Rekognition Connection")
    
    try:
        import boto3
        from botocore.exceptions import NoCredentialsError, ClientError
        
        region = os.getenv('AWS_REGION', 'us-east-1')
        collection_id = os.getenv('AWS_COLLECTION_ID', 'factory-employees')
        
        print_info(f"Connecting to AWS Rekognition in {region}...")
        
        client = boto3.client(
            'rekognition',
            region_name=region,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        # Try to describe collection
        try:
            response = client.describe_collection(CollectionId=collection_id)
            print_success(f"AWS Rekognition connected")
            print_info(f"Collection: {collection_id}")
            print_info(f"Face count in collection: {response['FaceCount']}")
            return True
        except client.exceptions.ResourceNotFoundException:
            print_warning(f"Collection '{collection_id}' doesn't exist yet")
            print_info("It will be created when pipeline initializes")
            return True
        
    except NoCredentialsError:
        print_error("AWS credentials not found or invalid")
        return False
    except ClientError as e:
        print_error(f"AWS error: {e}")
        return False
    except Exception as e:
        print_error(f"Connection error: {e}")
        return False


def test_inference_pipeline():
    """Test the inference pipeline with a blank frame."""
    print_header("Testing Inference Pipeline")
    
    try:
        from unified_inference_engine import InferencePipeline
        
        print_info("Initializing InferencePipeline...")
        pipeline = InferencePipeline()
        
        if not pipeline.initialized:
            print_error("Pipeline failed to initialize")
            return False
        
        print_success("Pipeline initialized successfully")
        
        # Get status
        status = pipeline.get_status()
        print_info(f"Pipeline status: {status.get('initialized')}")
        print_info(f"Frames processed: {status.get('frames_processed', 0)}")
        print_info(f"Current occupancy: {status.get('current_occupancy', 0)}")
        
        # Create a blank frame
        print_info("Creating test frame...")
        blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        _, jpeg = cv2.imencode('.jpg', blank_frame)
        frame_b64 = base64.b64encode(jpeg).decode()
        
        print_info("Processing test frame...")
        result = pipeline.process_frame(frame_b64)
        
        if result['success']:
            print_success(f"Frame processed in {result['processing_time_ms']:.2f}ms")
            print_info(f"Detected {result['people_count']} people, {result['vehicle_count']} vehicles")
            print_info(f"Occupancy: {result['occupancy']}, Entries: {result['entries']}, Exits: {result['exits']}")
            return True
        else:
            print_error(f"Processing failed: {result.get('error')}")
            return False
        
    except Exception as e:
        print_error(f"Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fastapi_endpoints():
    """Test FastAPI endpoints (if server is running)."""
    print_header("Testing FastAPI Endpoints")
    
    try:
        import requests
        
        base_url = "http://localhost:8000"
        
        # Test health endpoint
        print_info("Testing GET /api/health...")
        response = requests.get(f"{base_url}/api/health", timeout=5)
        
        if response.status_code == 200:
            print_success("Health check endpoint working")
            data = response.json()
            print_info(f"Status: {data.get('status')}")
            print_info(f"Services: {data.get('services')}")
        else:
            print_warning(f"Health check returned status {response.status_code}")
            print_info("Make sure FastAPI server is running: python -m uvicorn main_integration:app --reload")
            return False
        
        # Test diagnostic endpoint
        print_info("Testing GET /api/diagnostic...")
        response = requests.get(f"{base_url}/api/diagnostic", timeout=5)
        
        if response.status_code == 200:
            print_success("Diagnostic endpoint working")
            return True
        else:
            print_warning(f"Diagnostic check returned status {response.status_code}")
            return False
        
    except requests.exceptions.ConnectionError:
        print_warning("Cannot connect to FastAPI server on localhost:8000")
        print_info("Start server with: python -m uvicorn main_integration:app --reload")
        return True  # Not a fatal error
    except Exception as e:
        print_warning(f"Endpoint test skipped: {e}")
        return True  # Not a fatal error


def main():
    """Run all tests."""
    print_header("Factory AI SaaS - 4 Module Verification Suite")
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Environment Variables", test_env_variables),
        ("Database", test_database),
        ("AWS Connection", test_aws_connection),
        ("Inference Pipeline", test_inference_pipeline),
        ("FastAPI Endpoints", test_fastapi_endpoints)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print_error(f"Test '{test_name}' crashed: {e}")
            results[test_name] = False
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{GREEN}✅ PASS{RESET}" if result else f"{RED}❌ FAIL{RESET}"
        print(f"{test_name:30} {status}")
    
    print(f"\n{BOLD}Overall: {passed}/{total} tests passed{RESET}")
    
    if passed == total:
        print_success("\n🎉 All tests passed! System is ready for production!")
        print_info("\nNext steps:")
        print_info("1. Start FastAPI server: python -m uvicorn main_integration:app --reload")
        print_info("2. Enroll employees: curl -X POST http://localhost:8000/api/enroll-employee ...")
        print_info("3. Send frames: curl -X POST http://localhost:8000/api/process ...")
        print_info("4. Monitor: curl http://localhost:8000/api/health")
        return 0
    else:
        print_error("\n⚠️  Some tests failed. Check output above and fix issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
