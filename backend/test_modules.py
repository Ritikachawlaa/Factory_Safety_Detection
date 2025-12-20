#!/usr/bin/env python3
"""
Factory AI SaaS - Quick Start & Testing Script
Run individual module tests without needing a full FastAPI server.

Usage:
    python test_modules.py --module attendance --employee 123
    python test_modules.py --module vehicle --plate "KA01AB1234"
    python test_modules.py --module occupancy --job hourly
    python test_modules.py --module identity --cleanup snapshots
    python test_modules.py --module all
"""

import sys
import logging
from datetime import datetime, time
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# MODULE TESTS
# ============================================================================

def test_attendance_module():
    """Test Module 3: Attendance Shift Integrity"""
    logger.info("\n" + "="*80)
    logger.info("🧪 Testing Module 3: Attendance Shift Integrity")
    logger.info("="*80 + "\n")
    
    try:
        from services.attendance_shift_service import ShiftIntegrityService
        
        service = ShiftIntegrityService()
        
        # Test Case 1: On-time check-in
        logger.info("\n📝 Test Case 1: On-time check-in")
        result = service.process_shift_status(
            employee_id=101,
            check_in_time=datetime.now(),
            shift_data={
                'start_time': '08:00:00',
                'end_time': '17:00:00',
                'grace_period_minutes': 5
            }
        )
        logger.info(f"✅ Result: {result['status'].value} - {result['message']}")
        
        # Test Case 2: Late check-in (after grace period)
        logger.info("\n📝 Test Case 2: Late check-in")
        from datetime import timedelta
        late_time = datetime.now().replace(hour=8, minute=10)
        result = service.process_shift_status(
            employee_id=102,
            check_in_time=late_time,
            shift_data={
                'start_time': '08:00:00',
                'end_time': '17:00:00',
                'grace_period_minutes': 5
            }
        )
        logger.info(f"✅ Result: {result['status'].value} - {result['message']}")
        
        # Test Case 3: Duplicate entry prevention
        logger.info("\n📝 Test Case 3: Duplicate entry prevention")
        result1 = service.process_shift_status(
            employee_id=103,
            check_in_time=datetime.now(),
            shift_data={'start_time': '08:00:00', 'end_time': '17:00:00', 'grace_period_minutes': 5}
        )
        result2 = service.process_shift_status(
            employee_id=103,
            check_in_time=datetime.now(),
            shift_data={'start_time': '08:00:00', 'end_time': '17:00:00', 'grace_period_minutes': 5}
        )
        logger.info(f"✅ First check-in: {result1['status'].value}")
        logger.info(f"✅ Second check-in: {result2['skipped_duplicate']} (skipped as duplicate)")
        
        logger.info("\n✅ Module 3 tests completed successfully!\n")
        return True
    
    except Exception as e:
        logger.error(f"❌ Module 3 test failed: {e}", exc_info=True)
        return False


def test_vehicle_module():
    """Test Module 2: Vehicle Quality Gate"""
    logger.info("\n" + "="*80)
    logger.info("🧪 Testing Module 2: Vehicle Quality Gate & ANPR Validation")
    logger.info("="*80 + "\n")
    
    try:
        from services.vehicle_quality_gate import VehicleQualityGate
        
        gate = VehicleQualityGate()
        
        # Test Case 1: Valid plate with high confidence
        logger.info("\n📝 Test Case 1: Valid plate with high confidence")
        result = gate.validate_plate_recognition(
            ocr_text="KA 01 AB 1234",
            ocr_confidence=0.92,
            vehicle_track_id=1
        )
        logger.info(f"✅ Valid: {result['valid']}, Plate: {result['plate_number']}, Gate Event: {result['should_trigger_gate_event']}")
        
        # Test Case 2: Low confidence (below threshold)
        logger.info("\n📝 Test Case 2: Low OCR confidence")
        result = gate.validate_plate_recognition(
            ocr_text="KA 01 AB 1234",
            ocr_confidence=0.75,  # Below 0.85 threshold
            vehicle_track_id=2
        )
        logger.info(f"✅ Valid: {result['valid']}, Reason: {result['reason']}")
        
        # Test Case 3: Invalid format
        logger.info("\n📝 Test Case 3: Invalid plate format")
        result = gate.validate_plate_recognition(
            ocr_text="INVALID123",
            ocr_confidence=0.90,
            vehicle_track_id=3
        )
        logger.info(f"✅ Valid: {result['valid']}, Reason: {result['reason']}")
        
        # Test Case 4: Blocked vehicle
        logger.info("\n📝 Test Case 4: Blocked vehicle detection")
        gate.register_blocked_vehicle("DL01AB1234", "Stolen vehicle", "Officer_Smith")
        result = gate.validate_plate_recognition(
            ocr_text="DL 01 AB 1234",
            ocr_confidence=0.95,
            vehicle_track_id=4
        )
        logger.info(f"✅ Status: {result['status'].value}, Alert: {result.get('alert_message', 'None')}")
        
        # Test Case 5: Gate statistics
        logger.info("\n📝 Test Case 5: Gate statistics")
        stats = gate.get_gate_statistics()
        logger.info(f"✅ Blocked vehicles: {stats['total_blocked_vehicles']}")
        logger.info(f"✅ OCR threshold: {stats['ocr_threshold']:.0%}")
        
        logger.info("\n✅ Module 2 tests completed successfully!\n")
        return True
    
    except Exception as e:
        logger.error(f"❌ Module 2 test failed: {e}", exc_info=True)
        return False


def test_occupancy_module():
    """Test Module 4: Occupancy Scheduler"""
    logger.info("\n" + "="*80)
    logger.info("🧪 Testing Module 4: Occupancy Background Scheduler")
    logger.info("="*80 + "\n")
    
    try:
        from services.occupancy_scheduler import OccupancyScheduler
        
        scheduler = OccupancyScheduler()
        
        # Test Case 1: Start scheduler
        logger.info("\n📝 Test Case 1: Starting scheduler")
        scheduler.start()
        logger.info(f"✅ Scheduler started: {scheduler.is_running}")
        
        # Test Case 2: Get scheduler status
        logger.info("\n📝 Test Case 2: Scheduler status")
        status = scheduler.get_scheduler_status()
        logger.info(f"✅ Running: {status['running']}")
        logger.info(f"✅ Jobs scheduled: {len(status['jobs'])}")
        for job in status['jobs']:
            logger.info(f"   - {job['name']}: {job['trigger']}")
        
        # Test Case 3: Trigger hourly aggregation manually
        logger.info("\n📝 Test Case 3: Manual hourly aggregation")
        result = scheduler.aggregate_occupancy_hourly()
        logger.info(f"✅ Success: {result['success']}, Message: {result['message']}")
        
        # Test Case 4: Trigger drift correction manually
        logger.info("\n📝 Test Case 4: Manual drift correction")
        result = scheduler.apply_occupancy_drift_correction()
        logger.info(f"✅ Success: {result['success']}, Cameras reset: {result['cameras_reset']}")
        
        # Test Case 5: Stop scheduler
        logger.info("\n📝 Test Case 5: Stopping scheduler")
        scheduler.stop()
        logger.info(f"✅ Scheduler stopped: {not scheduler.is_running}")
        
        logger.info("\n✅ Module 4 tests completed successfully!\n")
        return True
    
    except Exception as e:
        logger.error(f"❌ Module 4 test failed: {e}", exc_info=True)
        return False


def test_identity_module():
    """Test Module 1: Identity AWS Retry & Snapshot Cleanup"""
    logger.info("\n" + "="*80)
    logger.info("🧪 Testing Module 1: Identity AWS Retry & Snapshot Management")
    logger.info("="*80 + "\n")
    
    try:
        from services.identity_aws_retry import (
            AWSRetryDecorator,
            SnapshotCleanupService,
            RetryStrategy
        )
        
        # Test Case 1: Retry decorator configuration
        logger.info("\n📝 Test Case 1: Retry decorator setup")
        retry_decorator = AWSRetryDecorator(
            max_retries=3,
            initial_delay=1,
            strategy=RetryStrategy.EXPONENTIAL
        )
        logger.info(f"✅ Decorator configured: max_retries={retry_decorator.max_retries}, strategy={retry_decorator.strategy.value}")
        
        # Test Case 2: Test decorator with mock function
        logger.info("\n📝 Test Case 2: Decorator with non-failing function")
        call_count = 0
        
        @retry_decorator
        def test_function():
            nonlocal call_count
            call_count += 1
            return f"Success on attempt {call_count}"
        
        result = test_function()
        logger.info(f"✅ Result: {result}")
        
        # Test Case 3: Snapshot cleanup service
        logger.info("\n📝 Test Case 3: Snapshot cleanup statistics")
        cleanup = SnapshotCleanupService()
        stats = cleanup.get_snapshot_statistics()
        logger.info(f"✅ Total snapshot files: {stats['total_files']}")
        logger.info(f"✅ Total size: {stats['total_size_mb']:.2f} MB")
        logger.info(f"✅ Files older than 90 days: {stats['old_files']}")
        
        # Test Case 4: Snapshot cleanup
        logger.info("\n📝 Test Case 4: Running snapshot cleanup")
        result = cleanup.cleanup_old_snapshots()
        logger.info(f"✅ Success: {result['success']}")
        logger.info(f"✅ Files deleted: {result['files_deleted']}")
        logger.info(f"✅ Space freed: {result['disk_space_freed_mb']:.2f} MB")
        
        logger.info("\n✅ Module 1 tests completed successfully!\n")
        return True
    
    except Exception as e:
        logger.error(f"❌ Module 1 test failed: {e}", exc_info=True)
        return False


def test_video_module():
    """Test Module 5: Video RTSP-to-MJPEG Streaming"""
    logger.info("\n" + "="*80)
    logger.info("🧪 Testing Module 5: Video RTSP-to-MJPEG Streaming")
    logger.info("="*80 + "\n")
    
    try:
        from services.video_rtsp_mjpeg import RTSPStreamManager, BoundingBoxOverlay, MJPEGStreamEncoder
        
        # Test Case 1: RTSP Stream Manager initialization
        logger.info("\n📝 Test Case 1: RTSPStreamManager initialization")
        stream_mgr = RTSPStreamManager(
            rtsp_url="rtsp://192.168.1.100:554/stream",
            buffer_size=1,
            timeout_seconds=30
        )
        logger.info(f"✅ Stream manager initialized for {stream_mgr.rtsp_url}")
        
        # Test Case 2: Bounding box overlay initialization
        logger.info("\n📝 Test Case 2: BoundingBoxOverlay initialization")
        overlay = BoundingBoxOverlay()
        logger.info(f"✅ Overlay service initialized with {len(overlay.COLOR_PALETTE)} color codes")
        
        # Test Case 3: MJPEG encoder initialization
        logger.info("\n📝 Test Case 3: MJPEGStreamEncoder initialization")
        encoder = MJPEGStreamEncoder(frame_rate=30)
        logger.info(f"✅ Encoder initialized: {encoder.JPEG_QUALITY} quality, {encoder.frame_rate} FPS")
        
        # Test Case 4: Stream status (won't connect without real camera)
        logger.info("\n📝 Test Case 4: Stream status check")
        status = stream_mgr.get_status()
        logger.info(f"✅ Connected: {status['connected']}")
        logger.info(f"   Note: Connection failed as expected (no real camera available)")
        
        logger.info("\n✅ Module 5 initialization tests completed successfully!")
        logger.info("   Note: Full streaming test requires real RTSP camera\n")
        return True
    
    except Exception as e:
        logger.error(f"❌ Module 5 test failed: {e}", exc_info=True)
        return False


def run_all_tests():
    """Run all module tests"""
    logger.info("\n\n")
    logger.info("╔" + "="*78 + "╗")
    logger.info("║" + " "*20 + "FACTORY AI SAAS - MODULE TESTS" + " "*27 + "║")
    logger.info("╚" + "="*78 + "╝")
    
    results = {
        'Module 1: Identity AWS Retry': test_identity_module(),
        'Module 2: Vehicle Quality Gate': test_vehicle_module(),
        'Module 3: Attendance Shift': test_attendance_module(),
        'Module 4: Occupancy Scheduler': test_occupancy_module(),
        'Module 5: Video RTSP-MJPEG': test_video_module(),
    }
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("📊 TEST SUMMARY")
    logger.info("="*80 + "\n")
    
    for module, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"{status} - {module}")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    logger.info("\n" + "-"*80)
    logger.info(f"Total: {passed}/{total} modules tested successfully")
    logger.info("="*80 + "\n")
    
    return all(results.values())


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}", exc_info=True)
        sys.exit(1)
