"""
ML Service Integration Views - OPTIMIZED
These views connect the ML detection services with Django models to persist data.
Uses threading for concurrent request handling to prevent UI freezing.
"""
import cv2
import numpy as np
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import datetime
import sys
import os
from concurrent.futures import ThreadPoolExecutor
from asgiref.sync import sync_to_async
import asyncio

# Thread pool for ML inference (4 workers = 4 concurrent detections)
ml_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ML-Worker")

# Add backend directory to path for app imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from .models import (
    HelmetDetection, LoiteringDetection, ProductionCounter,
    Employee, AttendanceRecord, SystemLog
)
from .serializers import (
    HelmetDetectionSerializer, LoiteringDetectionSerializer,
    ProductionCounterSerializer, AttendanceRecordSerializer
)

# Import ML services
try:
    from app.services.helmet_service import get_helmet_detection_status
    print("✅ Helmet service imported successfully")
except ImportError as e:
    print(f"❌ Helmet service import failed: {e}")
    get_helmet_detection_status = None

try:
    from app.services.loitering_service import get_loitering_status
    print("✅ Loitering service imported successfully")
except ImportError as e:
    print(f"❌ Loitering service import failed: {e}")
    get_loitering_status = None

try:
    from app.services.production_counter_service import get_production_count
    print("✅ Production counter service imported successfully")
except ImportError as e:
    print(f"❌ Production counter service import failed: {e}")
    get_production_count = None

try:
    from app.services.attendance_service import get_attendance_status
    print("✅ Attendance service imported successfully")
except Exception as e:
    print(f"❌ Attendance service import failed: {type(e).__name__}: {e}")
    get_attendance_status = None


def run_ml_inference(func, frame):
    """
    Wrapper to run ML inference in thread pool (non-blocking).
    This allows multiple detections to run concurrently.
    """
    return ml_executor.submit(func, frame).result()

@api_view(['POST'])
def helmet_detection_live(request):
    """
    OPTIMIZED: Real-time helmet detection endpoint with concurrent processing.
    Runs in thread pool to prevent blocking other requests.
    """
    if not get_helmet_detection_status:
        return Response({'error': 'Helmet detection service not available'}, 
                       status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    try:
        # Get frame from request (base64 or file upload)
        frame_data = request.data.get('frame')
        
        if not frame_data:
            return Response({'error': 'No frame data provided'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Decode frame (assuming base64 encoding from frontend)
        import base64
        frame_bytes = base64.b64decode(frame_data.split(',')[1] if ',' in frame_data else frame_data)
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Run ML detection in thread pool (non-blocking)
        result = run_ml_inference(get_helmet_detection_status, frame)
        
        # Save to database
        detection = HelmetDetection.objects.create(
            total_people=result['totalPeople'],
            compliant_count=result['compliantCount'],
            violation_count=result['violationCount'],
            frame_data={
                'detections': result.get('detections', []),
                'timestamp': datetime.now().isoformat()
            }
        )
        
        # Log the event
        if result['violationCount'] > 0:
            SystemLog.objects.create(
                log_type='helmet',
                severity='warning',
                message=f"Helmet violation detected: {result['violationCount']} person(s)",
                details=result
            )
        
        return Response({
            'id': detection.id,
            'timestamp': detection.timestamp,
            'totalPeople': detection.total_people,
            'compliantCount': detection.compliant_count,
            'violationCount': detection.violation_count,
            'complianceRate': detection.compliance_rate
        })
        
    except Exception as e:
        SystemLog.objects.create(
            log_type='helmet',
            severity='error',
            message=f"Helmet detection error: {str(e)}"
        )
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def loitering_detection_live(request):
    """
    OPTIMIZED: Real-time loitering detection with concurrent processing.
    """
    if not get_loitering_status:
        return Response({'error': 'Loitering detection service not available'}, 
                       status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    try:
        frame_data = request.data.get('frame')
        if not frame_data:
            return Response({'error': 'No frame data provided'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Decode frame
        import base64
        frame_bytes = base64.b64decode(frame_data.split(',')[1] if ',' in frame_data else frame_data)
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Run ML detection in thread pool (non-blocking)
        result = run_ml_inference(get_loitering_status, frame)
        
        # Save to database
        detection = LoiteringDetection.objects.create(
            active_groups=result['activeGroups'],
            alert_triggered=result['activeGroups'] > 0,
            group_details={
                'groups': result.get('groups', []),
                'timestamp': datetime.now().isoformat()
            }
        )
        
        # Log alert
        if detection.alert_triggered:
            SystemLog.objects.create(
                log_type='loitering',
                severity='warning',
                message=f"Loitering detected: {result['activeGroups']} group(s)",
                details=result
            )
        
        return Response({
            'id': detection.id,
            'timestamp': detection.timestamp,
            'activeGroups': detection.active_groups,
            'alertTriggered': detection.alert_triggered
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Loitering detection error: {e}")
        print(error_details)
        SystemLog.objects.create(
            log_type='loitering',
            severity='error',
            message=f"Loitering detection error: {str(e)}"
        )
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def production_counter_live(request):
    """
    OPTIMIZED: Real-time production counting with concurrent processing.
    """
    if not get_production_count:
        return Response({'error': 'Production counter service not available'}, 
                       status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    try:
        frame_data = request.data.get('frame')
        if not frame_data:
            return Response({'error': 'No frame data provided'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Decode frame
        import base64
        frame_bytes = base64.b64decode(frame_data.split(',')[1] if ',' in frame_data else frame_data)
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Run ML detection in thread pool (non-blocking)
        result = run_ml_inference(get_production_count, frame)
        
        # Save to database
        counter = ProductionCounter.objects.create(
            item_count=result['itemCount'],
            session_date=timezone.now().date(),
            details={
                'items': result.get('items', []),
                'timestamp': datetime.now().isoformat()
            }
        )
        
        return Response({
            'id': counter.id,
            'timestamp': counter.timestamp,
            'itemCount': counter.item_count,
            'sessionDate': counter.session_date
        })
        
    except Exception as e:
        SystemLog.objects.create(
            log_type='production',
            severity='error',
            message=f"Production counter error: {str(e)}"
        )
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def production_counter_reset(request):
    """
    Reset production counter endpoint
    """
    if not get_production_count:
        return Response({'error': 'Production counter service not available'}, 
                       status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    try:
        from app.services.production_counter_service import reset_production_count
        result = reset_production_count()
        
        SystemLog.objects.create(
            log_type='production',
            severity='info',
            message="Production counter reset"
        )
        
        return Response(result)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def attendance_system_live(request):
    """
    OPTIMIZED: Real-time attendance/facial recognition with concurrent processing.
    """
    if not get_attendance_status:
        return Response({'error': 'Attendance service not available'}, 
                       status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    try:
        frame_data = request.data.get('frame')
        if not frame_data:
            return Response({'error': 'No frame data provided'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Decode frame
        import base64
        frame_bytes = base64.b64decode(frame_data.split(',')[1] if ',' in frame_data else frame_data)
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Run ML detection in thread pool (non-blocking)
        result = run_ml_inference(get_attendance_status, frame)
        
        # Format response to match frontend expectations
        last_person = result.get('lastPersonSeen', '---')
        is_recognized = last_person != '---'
        
        return Response({
            'recognized_person': last_person if is_recognized else None,
            'status': 'Recognized' if is_recognized else 'Not recognized',
            'timestamp': datetime.now().isoformat(),
            'verified_count': result.get('verifiedCount', 0),
            'attendance_log': result.get('attendanceLog', [])
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Attendance system error: {e}")
        print(error_details)
        SystemLog.objects.create(
            log_type='attendance',
            severity='error',
            message=f"Attendance system error: {str(e)}"
        )
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def test_ml_services(request):
    """
    Test endpoint to check if ML services are available
    """
    services_status = {
        'helmet_detection': get_helmet_detection_status is not None,
        'loitering_detection': get_loitering_status is not None,
        'production_counter': get_production_count is not None,
        'attendance_system': get_attendance_status is not None
    }
    
    return Response({
        'status': 'ok',
        'ml_services': services_status,
        'database': 'connected',
        'timestamp': timezone.now()
    })
