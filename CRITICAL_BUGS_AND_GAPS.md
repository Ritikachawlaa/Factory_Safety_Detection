# CRITICAL BUGS & GAPS - PRIORITIZED FIX LIST

**For:** Commercial Pilot Release  
**Created:** December 20, 2025  
**Updated:** January 2025  

---

## PRIORITY MATRIX

```
             Impact
        HIGH    MED    LOW
      +-------+-------+------+
HIGH  | P0 P0 | P1 P1 | P2 P2|  Effort
      +-------+-------+------+
MED   | P0 P1 | P2 P2 | P3 P3|
      +-------+-------+------+
LOW   | P1 P2 | P3 P3 | P3 P3|
      +-------+-------+------+
```

---

## 🔴 BLOCKING ISSUES (MUST FIX BEFORE PILOT)

### P0.1: RTSP Stream Conversion Missing
**Severity:** 🔴 BLOCKER  
**Module:** System-Wide (Frontend + Backend)  
**Impact:** HIGH - Customer cannot see any camera feeds  
**Effort:** 3-4 days  
**Status:** ❌ Not Started

**Description:**
- System config allows RTSP URLs but no conversion to HLS/MJPEG
- Angular dashboard has no video playback capability for RTSP
- Only local webcam (getUserMedia) works
- Fatal for commercial deployment

**Current Evidence:**
```typescript
// frontend/camera-config.service.ts validates but doesn't use RTSP
validateRtspUrl(url: string): { valid: boolean; error?: string } {
    const rtspPattern = /^rtsp:\/\/.+/i;
    return rtspPattern.test(url) ? { valid: true } : { valid: false };
}

// But nowhere uses this RTSP URL for streaming
// Only WebRTC/getUserMedia streams are played
```

**Required Changes:**

1. **Add FFmpeg/RTSP-to-HLS Service** (Backend)
   ```python
   # backend/services/stream_converter.py (new file)
   class RTSPToHLSConverter:
       def start_stream_conversion(self, rtsp_url: str, output_dir: str):
           """Convert RTSP stream to HLS"""
           cmd = [
               'ffmpeg',
               '-i', rtsp_url,
               '-c:v', 'libx264',
               '-preset', 'veryfast',
               '-c:a', 'aac',
               '-f', 'hls',
               '-hls_time', '2',
               '-hls_list_size', '3',
               f'{output_dir}/stream.m3u8'
           ]
           subprocess.Popen(cmd)
   ```

2. **Add Stream Health Check Endpoint** (Backend)
   ```python
   @app.get("/api/stream/{camera_id}/health")
   def check_stream_health(camera_id: str):
       """Check if RTSP stream is alive"""
       return {
           "status": "alive|dead",
           "bitrate": 2500,  # kbps
           "latency": 500,   # ms
           "dropped_frames": 0
       }
   ```

3. **Add HLS Playback in Angular** (Frontend)
   ```typescript
   // frontend/components/camera-player.component.ts
   import * as HLS from 'hls.js';
   
   playStream(cameraId: string) {
       const video = this.videoElement.nativeElement;
       const hlsUrl = `/api/stream/${cameraId}/playlist.m3u8`;
       
       if (HLS.isSupported()) {
           const hls = new HLS();
           hls.loadSource(hlsUrl);
           hls.attachMedia(video);
       } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
           video.src = hlsUrl;
       }
   }
   ```

**Testing Needed:**
- [ ] FFmpeg conversion works with various RTSP sources
- [ ] HLS playback latency < 3 seconds
- [ ] Stream handles network drops gracefully
- [ ] Works on Chrome, Firefox, Safari, Edge

**Files to Modify:**
- Add: `backend/services/stream_converter.py` (200 lines)
- Add: `backend/detection_system/stream_endpoints.py` (150 lines)
- Modify: `frontend/src/app/components/camera-player/camera-player.component.ts` (100 lines)
- Modify: `backend/requirements.txt` (add ffmpeg-python)

---

### P0.2: Background Scheduler Not Integrated
**Severity:** 🔴 BLOCKER  
**Module:** System-Wide  
**Impact:** HIGH - Data loss after 90 days, occupancy aggregation broken  
**Effort:** 2-3 hours  
**Status:** ❌ Not Started

**Description:**
- Cleanup functions exist but never called → unbounded DB growth
- Occupancy aggregation methods exist but never called → occupancy history broken
- After 90 days: database > 1GB, performance degrades
- After 1 month: occupancy counts unreliable (no aggregation)

**Current Evidence:**
```python
# backend/detection_system/attendance_models.py:597
def delete_old_records(self, days: int = 90):
    """Delete records older than specified days"""
    # Function written but NEVER CALLED

# backend/detection_system/occupancy_service.py:500
def aggregate_hourly(self):
    # Method exists but never scheduled
```

**Required Changes:**

```python
# backend/main_unified.py or backend/detection_system/scheduler.py (new)

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

logger = logging.getLogger(__name__)

def setup_scheduler(app):
    """Initialize background scheduler on app startup"""
    scheduler = BackgroundScheduler()
    
    # Cleanup tasks (run at 2 AM daily)
    scheduler.add_job(
        cleanup_identity_logs,
        CronTrigger(hour=2, minute=0),
        id='cleanup_identity_logs',
        name='Clean identity access logs (90-day retention)',
        replace_existing=True
    )
    
    scheduler.add_job(
        cleanup_vehicle_logs,
        CronTrigger(hour=2, minute=15),
        id='cleanup_vehicle_logs',
        name='Clean vehicle access logs (90-day retention)',
        replace_existing=True
    )
    
    scheduler.add_job(
        cleanup_attendance_logs,
        CronTrigger(hour=2, minute=30),
        id='cleanup_attendance_logs',
        name='Clean attendance logs (90-day retention)',
        replace_existing=True
    )
    
    scheduler.add_job(
        cleanup_occupancy_logs,
        CronTrigger(hour=2, minute=45),
        id='cleanup_occupancy_logs',
        name='Clean occupancy logs (90-day retention)',
        replace_existing=True
    )
    
    # Aggregation tasks (occupancy)
    scheduler.add_job(
        occupancy_service.aggregate_hourly,
        CronTrigger(minute=5),  # 5 min past each hour
        id='occupancy_hourly_agg',
        name='Occupancy hourly aggregation',
        replace_existing=True
    )
    
    scheduler.add_job(
        occupancy_service.aggregate_daily,
        CronTrigger(hour=1, minute=0),  # 1 AM daily
        id='occupancy_daily_agg',
        name='Occupancy daily aggregation',
        replace_existing=True
    )
    
    scheduler.add_job(
        occupancy_service.aggregate_monthly,
        CronTrigger(day=1, hour=2, minute=0),  # 1st of month, 2 AM
        id='occupancy_monthly_agg',
        name='Occupancy monthly aggregation',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("✅ Background scheduler started with 6 jobs")
    
    return scheduler

# In FastAPI startup
@app.on_event("startup")
async def startup_event():
    global scheduler
    scheduler = setup_scheduler(app)

@app.on_event("shutdown")
async def shutdown_event():
    if scheduler:
        scheduler.shutdown()
```

**Dependencies:**
```
# Add to requirements.txt
apscheduler>=3.10.0
```

**Testing:**
- [ ] Scheduler starts on app startup
- [ ] Jobs execute at correct times
- [ ] Cleanup removes old records
- [ ] Aggregation updates hourly/daily/monthly tables
- [ ] Database size remains stable after 90 days

**Files to Modify:**
- Add: `backend/detection_system/scheduler.py` (100 lines)
- Modify: `backend/main_unified.py` or `backend/app/main.py` (20 lines)
- Modify: `backend/requirements.txt` (1 line)

---

### P0.3: Early Exit Detection Logic Missing
**Severity:** 🔴 BLOCKER  
**Module:** Module 3 (Attendance)  
**Impact:** HIGH - Cannot enforce shift compliance, payroll issues  
**Effort:** 2-3 hours  
**Status:** ❌ Not Started

**Description:**
- Model has `early_exit` boolean field
- NO business logic to detect or set it
- Early exits not flagged → cannot enforce shift discipline
- Factory owner cannot track employee departures

**Current Evidence:**
```python
# backend/detection_system/attendance_models.py:212
class AttendanceRecord(Base):
    check_in_time = Column(Time, nullable=True)
    exit_time = Column(Time, nullable=True)
    early_exit = Column(Boolean, default=False)  # Field created but unused
    
    # NO method to set early_exit based on shift end time
```

**Service Logic (Missing):**
```python
# backend/detection_system/attendance_service.py
def check_out(self, employee_id: int, camera_id: str, timestamp: datetime):
    employee = session.query(Employee).get(employee_id)
    shift = employee.assigned_shift
    
    # MISSING: Flag early exit
    current_time = timestamp.time()
    early_exit_threshold = shift.end_time  # - timedelta(minutes=5)?
    
    if current_time < early_exit_threshold:
        # MISSING: Set early_exit = True
        # MISSING: Log warning
        pass
```

**Required Fix:**
```python
# backend/detection_system/attendance_service.py

def check_out(self, employee_id: int, camera_id: str, timestamp: datetime, session: Session):
    """
    Record employee check-out / shift exit
    Flags early exits if before shift end time
    """
    try:
        employee = session.query(Employee).get(employee_id)
        if not employee:
            logger.warning(f"Employee {employee_id} not found for check-out")
            return None
        
        shift = employee.assigned_shift
        if not shift:
            logger.warning(f"No shift assigned to {employee.name}")
            return None
        
        # Get current time
        exit_time = timestamp.time()
        
        # Determine if early exit
        is_early_exit = False
        if exit_time < shift.end_time:
            # Allow grace period (5 minutes early is OK)
            grace_end = (
                datetime.combine(date.today(), shift.end_time) 
                - timedelta(minutes=5)
            ).time()
            is_early_exit = exit_time < grace_end
        
        # Create attendance record
        record = AttendanceRecord(
            employee_id=employee_id,
            date=timestamp.date(),
            exit_time=exit_time,
            early_exit=is_early_exit,
            status=AttendanceStatus.EARLY_EXIT if is_early_exit else AttendanceStatus.PRESENT,
            camera_id=camera_id,
            timestamp=timestamp
        )
        
        if is_early_exit:
            logger.warning(
                f"🚨 EARLY EXIT: {employee.name} exited at {exit_time} "
                f"(shift ends at {shift.end_time})"
            )
        
        session.add(record)
        session.commit()
        
        return record
    
    except Exception as e:
        logger.error(f"Error recording check-out: {str(e)}")
        session.rollback()
        return None
```

**Testing:**
- [ ] Early exit flagged when employee leaves <5 min before shift end
- [ ] Normal exit NOT flagged when leaving at/after end time
- [ ] Grace period respected (5 min before end = normal, not early)
- [ ] Correct warning logged for early exits
- [ ] Works with different shift times

**Files to Modify:**
- Modify: `backend/detection_system/attendance_service.py` (add check_out method, ~40 lines)
- Modify: `backend/detection_system/attendance_endpoints.py` (add endpoint, ~30 lines)

---

### P0.4: Double-Entry Prevention (Attendance)
**Severity:** 🔴 BLOCKER  
**Module:** Module 3 (Attendance)  
**Impact:** HIGH - Attendance counts inflated, wage overpayment  
**Effort:** 2-3 hours  
**Status:** ❌ Not Started

**Description:**
- Employee scanned by Camera A at gate
- 2 seconds later detected by Camera B (internal)
- Both recorded as separate entries → employee counted twice for same arrival
- Payroll: paid for 2 entries instead of 1

**Current Evidence:**
```python
# backend/detection_system/attendance_service.py (hypothetical check_in)
def check_in(self, employee_id: int, camera_id: str, timestamp: datetime):
    # NO check for duplicate
    # Just creates record blindly
    record = AttendanceRecord.create(
        employee_id=employee_id,
        check_in_time=timestamp.time(),
        camera_id=camera_id,
        timestamp=timestamp
    )
    return record  # Always succeeds
```

**Required Fix:**
```python
def check_in(self, employee_id: int, camera_id: str, timestamp: datetime, session: Session):
    """
    Record employee check-in / shift entry
    Prevents duplicate entries within 30 seconds
    """
    try:
        employee = session.query(Employee).get(employee_id)
        if not employee:
            logger.warning(f"Employee {employee_id} not found")
            return None
        
        today = timestamp.date()
        
        # Check for duplicate entry in last 30 seconds
        recent_checkin = session.query(AttendanceRecord).filter(
            AttendanceRecord.employee_id == employee_id,
            AttendanceRecord.date == today,
            AttendanceRecord.check_in_time.isnot(None),
            AttendanceRecord.timestamp >= timestamp - timedelta(seconds=30)
        ).first()
        
        if recent_checkin:
            logger.info(
                f"⏭️ DUPLICATE ENTRY BLOCKED: {employee.name} "
                f"(previous check-in {(timestamp - recent_checkin.timestamp).total_seconds():.0f}s ago)"
            )
            return None  # Reject duplicate
        
        # Check for existing check-in today
        existing_checkin = session.query(AttendanceRecord).filter(
            AttendanceRecord.employee_id == employee_id,
            AttendanceRecord.date == today,
            AttendanceRecord.check_in_time.isnot(None)
        ).first()
        
        if existing_checkin:
            # Already checked in today - this might be actual exit + re-entry
            # Log but don't block (could be lunch return)
            logger.info(f"ℹ️ RE-ENTRY: {employee.name} checked in again (possible lunch return)")
        
        # Create new check-in record
        record = AttendanceRecord(
            employee_id=employee_id,
            date=today,
            check_in_time=timestamp.time(),
            camera_id=camera_id,
            timestamp=timestamp,
            status=AttendanceStatus.PRESENT
        )
        
        session.add(record)
        session.commit()
        
        logger.info(f"✅ CHECK-IN: {employee.name} at {timestamp.time()}")
        return record
    
    except Exception as e:
        logger.error(f"Error recording check-in: {str(e)}")
        session.rollback()
        return None
```

**Testing:**
- [ ] First check-in succeeds
- [ ] Second check-in within 30 sec → BLOCKED
- [ ] Second check-in after 30 sec → ALLOWED (re-entry)
- [ ] Multiple camera detections within 30s → only 1 recorded
- [ ] Re-entry after >1 hour → ALLOWED (lunch return)

**Files to Modify:**
- Modify: `backend/detection_system/attendance_service.py` (add check_in method, ~50 lines)
- Modify: `backend/detection_system/attendance_endpoints.py` (add endpoint, ~30 lines)

---

## 🟠 CRITICAL ISSUES (MUST FIX BEFORE FIRST CUSTOMER)

### P1.1: ANPR Confidence Threshold Too Low
**Severity:** 🟠 CRITICAL  
**Module:** Module 2 (Vehicle & Gate)  
**Impact:** HIGH - 5-10% false positive rate on license plates  
**Effort:** 4-6 hours (includes testing)  
**Status:** ❌ Not Started

**Description:**
- Current threshold: 0.6 (60% confidence)
- Production standard: 0.85+ (85%)
- False positives: "ABC1234" mismatched to wrong vehicle
- Security/safety issue: wrong vehicles get gate access

**Current Evidence:**
```python
# backend/services/vehicle_gate_service.py:159
class ANPRProcessor:
    def __init__(self, confidence_threshold: float = 0.6):  # TOO LOW!
        self.confidence_threshold = confidence_threshold
```

**Required Fix:**

Option 1: Increase threshold (quick fix)
```python
# Change default to 0.85
def __init__(self, confidence_threshold: float = 0.85):  # Higher threshold
    self.confidence_threshold = confidence_threshold
```

Option 2: Multi-frame averaging (robust fix)
```python
class ANPRProcessor:
    def __init__(self, confidence_threshold: float = 0.80):
        self.confidence_threshold = confidence_threshold
        self.frame_history = {}  # plate_id -> [detections]
    
    def recognize_plate_with_averaging(self, plate_image: np.ndarray, 
                                      vehicle_id: int) -> Tuple[str, float]:
        """
        Recognize plate with multi-frame averaging for robustness
        """
        plate_text, confidence = self.recognize_plate(plate_image)
        
        if not plate_text:
            return None, 0.0
        
        # Add to history
        if vehicle_id not in self.frame_history:
            self.frame_history[vehicle_id] = []
        
        self.frame_history[vehicle_id].append({
            'text': plate_text,
            'confidence': confidence,
            'timestamp': time.time()
        })
        
        # Keep only last 5 frames (2-3 seconds)
        self.frame_history[vehicle_id] = [
            f for f in self.frame_history[vehicle_id]
            if time.time() - f['timestamp'] < 3.0
        ][-5:]
        
        # Check if all recent frames agree
        if len(self.frame_history[vehicle_id]) >= 3:
            texts = [f['text'] for f in self.frame_history[vehicle_id]]
            confidences = [f['confidence'] for f in self.frame_history[vehicle_id]]
            
            # If all 3+ frames same text and high confidence
            if len(set(texts)) == 1 and min(confidences) >= 0.80:
                avg_confidence = np.mean(confidences)
                logger.info(f"✅ VERIFIED PLATE: {plate_text} (avg conf: {avg_confidence:.2f})")
                return plate_text, avg_confidence
            else:
                logger.warning(f"❌ INCONSISTENT DETECTIONS: {texts}")
                return None, 0.0
        
        return None, 0.0
```

**Testing Protocol:**
1. Test against 100 license plates (US, India, EU formats)
2. Measure false positive rate (target: <1%)
3. Measure false negative rate (target: <2%)
4. Test with degraded images (low light, motion blur, etc.)

**Files to Modify:**
- Modify: `backend/services/vehicle_gate_service.py` (80-100 lines)
- Add: `backend/scripts/test_anpr_accuracy.py` (test suite, 200 lines)

---

### P1.2: No Plate Format Validation
**Severity:** 🟠 CRITICAL  
**Module:** Module 2 (Vehicle & Gate)  
**Impact:** MEDIUM - Garbage data in database  
**Effort:** 2-3 hours  
**Status:** ❌ Not Started

**Description:**
- ANPR accepts ANY text as plate ("A", "123456", "GARBAGE")
- No validation against known plate formats
- Database polluted with invalid plates
- Comparisons fail: "ABC1234" vs "ABC 1234" treated as different

**Current Evidence:**
```python
# backend/services/vehicle_gate_service.py:279
def recognize_plate(self, plate_image: np.ndarray):
    # ...
    plate_text = plate_text.replace(' ', '').upper()
    return plate_text, confidence  # Any string accepted
```

**Required Fix:**
```python
# backend/services/plate_validator.py (new file)

import re
from typing import Optional, Tuple

class PlateValidator:
    """Validate license plate format by region"""
    
    # Plate format patterns by region
    PATTERNS = {
        'US': [
            r'^[A-Z]{2,3}\d{4}$',          # ABC1234
            r'^[A-Z]{3}\d{3}$',             # ABC123
            r'^[A-Z]{1}\d{1}[A-Z]{3}\d{3}$', # A1BCD123
        ],
        'INDIA': [
            r'^[A-Z]{2}\d{2}[A-Z]{2}\d{4}$',  # MH01AB1234
            r'^[A-Z]{2}\d{2}[A-Z]{1}\d{5}$',  # MH01A12345
        ],
        'EU': [
            r'^[A-Z]{2}\d{2}[A-Z]{3}$',  # AB12CDE
            r'^[A-Z]{3}\d{3}[A-Z]{2}$',  # ABC123DE
        ],
        'UK': [
            r'^[A-Z]{2}\d{2}[A-Z]{3}$',  # AB02CDE
        ],
    }
    
    @staticmethod
    def validate_plate(plate_text: str, region: str = 'INDIA') -> Tuple[bool, str]:
        """
        Validate plate format
        
        Args:
            plate_text: Recognized plate text
            region: Plate region ('INDIA', 'US', 'EU', 'UK')
        
        Returns:
            (is_valid, normalized_plate)
        """
        if not plate_text or len(plate_text) < 4:
            return False, ""
        
        # Clean input
        plate_text = plate_text.strip().upper()
        
        # Check against patterns for region
        patterns = PlateValidator.PATTERNS.get(region, [])
        
        for pattern in patterns:
            if re.match(pattern, plate_text):
                return True, plate_text
        
        return False, ""
    
    @staticmethod
    def normalize_plate(plate_text: str) -> str:
        """Normalize plate for database comparison"""
        return plate_text.strip().upper().replace(' ', '')

# Usage in ANPR processor
from plate_validator import PlateValidator

class ANPRProcessor:
    def recognize_plate(self, plate_image: np.ndarray, region: str = 'INDIA'):
        plate_text, confidence = self._ocr_recognize(plate_image)
        
        if not plate_text:
            return None, 0.0
        
        # Validate format
        is_valid, normalized = PlateValidator.validate_plate(plate_text, region)
        
        if not is_valid:
            logger.warning(f"❌ Invalid plate format: {plate_text} (region: {region})")
            return None, 0.0
        
        logger.info(f"✅ Valid plate: {normalized} (conf: {confidence:.2f})")
        return normalized, confidence
```

**Testing:**
- [ ] Valid US plates accepted (ABC1234, AB123CD)
- [ ] Valid India plates accepted (MH01AB1234)
- [ ] Invalid plates rejected ("ABC", "12345", "GARBAGE")
- [ ] Plates normalized correctly (spaces removed)
- [ ] Region-specific validation works

**Files to Create:**
- Add: `backend/services/plate_validator.py` (100 lines)

**Files to Modify:**
- Modify: `backend/services/vehicle_gate_service.py` (20 lines)

---

### P1.3: AWS Rekognition No Retry Logic
**Severity:** 🟠 CRITICAL  
**Module:** Module 1 (Identity)  
**Impact:** MEDIUM - ~0.5% identity checks fail due to AWS timeouts  
**Effort:** 2-3 hours  
**Status:** ❌ Not Started

**Description:**
- AWS API calls fail (timeout, throttle) → immediate failure
- No exponential backoff retry
- ~0.5% of face identifications fail unnecessarily
- Employee marked as "Unknown" when should be recognized

**Current Evidence:**
```python
# backend/services/identity_service.py:128
def search_faces_by_image(self, image_bytes: bytes):
    response = self.client.search_faces_by_image(  # Single attempt
        CollectionId=REKOGNITION_COLLECTION_ID,
        Image={'Bytes': image_bytes},
        FaceMatchThreshold=FACE_MATCH_THRESHOLD,
        MaxFaces=1
    )  # If fails here → exception, no retry
```

**Required Fix:**
```python
# backend/services/identity_service.py

import time
from botocore.exceptions import ClientError, ConnectionError

class AWSRecognitionClient:
    def search_faces_by_image_with_retry(self, 
                                        image_bytes: bytes,
                                        max_retries: int = 3,
                                        backoff_factor: float = 2.0) -> Dict:
        """
        Search for faces with exponential backoff retry
        
        Args:
            image_bytes: Raw image bytes
            max_retries: Maximum retry attempts
            backoff_factor: Exponential backoff multiplier
        
        Returns:
            Face search results
        """
        
        for attempt in range(max_retries):
            try:
                self._check_rate_limit()
                
                response = self.client.search_faces_by_image(
                    CollectionId=REKOGNITION_COLLECTION_ID,
                    Image={'Bytes': image_bytes},
                    FaceMatchThreshold=FACE_MATCH_THRESHOLD,
                    MaxFaces=1
                )
                
                logger.info(f"✅ AWS Rekognition search succeeded (attempt {attempt + 1})")
                return self._parse_response(response)
            
            except ClientError as e:
                error_code = e.response['Error']['Code']
                
                # Throttle error - retry with backoff
                if error_code == 'ThrottlingException':
                    if attempt < max_retries - 1:
                        wait_time = backoff_factor ** attempt
                        logger.warning(
                            f"⚠️ AWS Throttled, retrying in {wait_time:.1f}s "
                            f"(attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"❌ Max retries exceeded for throttling")
                        raise
                
                # Rate limit error - retry with longer backoff
                elif error_code == 'ProvisionedThroughputExceededException':
                    if attempt < max_retries - 1:
                        wait_time = (backoff_factor ** attempt) * 2
                        logger.warning(
                            f"⚠️ Rate limit exceeded, retrying in {wait_time:.1f}s"
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"❌ Rate limit max retries exceeded")
                        raise
                
                # Other errors - don't retry
                else:
                    logger.error(f"❌ AWS error ({error_code}): {e.response['Error']['Message']}")
                    raise
            
            except (ConnectionError, TimeoutError) as e:
                if attempt < max_retries - 1:
                    wait_time = backoff_factor ** attempt
                    logger.warning(
                        f"⚠️ Connection error, retrying in {wait_time:.1f}s: {str(e)}"
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"❌ Connection failed after {max_retries} attempts")
                    raise
        
        raise Exception("AWS Rekognition search failed after all retries")
    
    def _parse_response(self, response: Dict) -> Dict:
        """Parse AWS response into standard format"""
        matched_faces = []
        for face_match in response.get('FaceMatches', []):
            face = face_match['Face']
            confidence = face_match['Similarity']
            
            matched_faces.append({
                'external_id': face.get('ExternalImageId', 'Unknown'),
                'face_id': face.get('FaceId'),
                'confidence': confidence
            })
        
        return {
            'matched_faces': matched_faces,
            'unmatched_faces': response.get('UnmatchedFaces', []),
            'error': None
        }
```

**Testing:**
- [ ] Success on first attempt → no retries
- [ ] Throttle error → retry with backoff
- [ ] Max retries exceeded → raise error
- [ ] Connection timeout → retry with backoff
- [ ] Success on retry 2/3 → returns correct result

**Files to Modify:**
- Modify: `backend/services/identity_service.py` (~60 lines)

---

### P1.4: Grace Period Not Enforced in Check-In
**Severity:** 🟠 CRITICAL  
**Module:** Module 3 (Attendance)  
**Impact:** HIGH - Late employees marked as "present", payroll issues  
**Effort:** 1-2 hours  
**Status:** ❌ Not Started

**Description:**
- Shift model has `is_late()` method
- Check-in service doesn't use it
- All check-ins marked as "present" regardless of time
- Factory cannot enforce punctuality

**Current Evidence:**
```python
# Model has method (unused)
class Shift(Base):
    def is_late(self, check_in_time: time) -> bool:
        grace_delta = timedelta(minutes=self.grace_period_minutes)
        grace_time = (datetime.combine(date.today(), self.start_time) 
                     + grace_delta).time()
        return check_in_time > grace_time

# Service doesn't use it
def check_in(employee_id, timestamp):
    record = AttendanceRecord.create(
        status="present"  # Always "present"!
    )
```

**Required Fix:**
```python
# backend/detection_system/attendance_service.py

def check_in(self, employee_id: int, camera_id: str, timestamp: datetime, session: Session):
    """
    Record employee check-in
    Automatically flags as "late" if after grace period
    """
    try:
        employee = session.query(Employee).get(employee_id)
        shift = employee.assigned_shift
        
        check_in_time = timestamp.time()
        
        # CRITICAL: Determine if late
        is_late = shift.is_late(check_in_time)
        status = AttendanceStatus.LATE if is_late else AttendanceStatus.PRESENT
        
        record = AttendanceRecord(
            employee_id=employee_id,
            date=timestamp.date(),
            check_in_time=check_in_time,
            status=status,  # NOW uses grace period!
            camera_id=camera_id,
            timestamp=timestamp
        )
        
        if is_late:
            logger.warning(
                f"🚨 LATE: {employee.name} at {check_in_time} "
                f"(shift: {shift.start_time}, grace: {shift.grace_period_minutes} min)"
            )
        
        session.add(record)
        session.commit()
        return record
    
    except Exception as e:
        logger.error(f"Error in check-in: {str(e)}")
        session.rollback()
        return None
```

**Testing:**
- [ ] On-time entry → status="present"
- [ ] Within grace period → status="present"
- [ ] After grace period → status="late"
- [ ] Log warning for late entries

**Files to Modify:**
- Modify: `backend/detection_system/attendance_service.py` (~30 lines)

---

### P1.5: Occupancy Aggregation Not Scheduled
**Severity:** 🟠 CRITICAL  
**Module:** Module 4 (Occupancy)  
**Impact:** HIGH - Historical occupancy data unavailable  
**Effort:** 1-2 hours  
**Status:** ❌ Not Started

**Description:**
- Aggregation methods exist (hourly, daily, monthly)
- Never called by scheduler
- Occupancy history empty → compliance reports unavailable
- Occupancy raw logs grow unbounded

**Current Evidence:**
```python
# Methods exist but never called
class TimeSeriesAggregator:
    def aggregate_hourly(self):  # Written but never scheduled
    def aggregate_daily(self):   # Written but never scheduled
    def aggregate_monthly(self):  # Written but never scheduled
```

**Required Fix:**
(Same as P0.2 - include these jobs in scheduler setup)

```python
scheduler.add_job(
    occupancy_service.aggregate_hourly,
    CronTrigger(minute=5),  # 5 min past each hour
    id='occupancy_hourly_agg'
)

scheduler.add_job(
    occupancy_service.aggregate_daily,
    CronTrigger(hour=1, minute=0),  # 1 AM
    id='occupancy_daily_agg'
)

scheduler.add_job(
    occupancy_service.aggregate_monthly,
    CronTrigger(day=1, hour=2, minute=0),  # 1st of month
    id='occupancy_monthly_agg'
)
```

---

## 🟡 IMPORTANT ISSUES (FIX BEFORE FIRST CUSTOMER)

### P2.1: Occupancy Drift Over Time
**Severity:** 🟡 IMPORTANT  
**Module:** Module 4 (Occupancy)  
**Impact:** MEDIUM - Count becomes wrong after weeks  
**Effort:** 2-3 hours  
**Status:** ❌ Not Started

**Description:**
- Line crossing detection misses <1% of crossings
- Over time, occupancy count drifts
- After 2 weeks: count might be 5-10 off
- Manual calibration needed frequently

**Solution:**
```python
# 1. Floor occupancy at 0 (never go negative)
self.current_occupancy = max(0, self.current_occupancy - 1)

# 2. Add calibration endpoint
@app.post("/api/occupancy/{camera_id}/calibrate")
def calibrate_occupancy(camera_id: str, actual_count: int):
    counter = get_occupancy_counter(camera_id)
    counter.current_occupancy = actual_count
    logger.info(f"Manual calibration: {actual_count}")

# 3. Log when occupancy becomes unreliable
if self.current_occupancy < 0:
    logger.error(f"Occupancy invalid: {self.current_occupancy}, resetting")
    self.current_occupancy = 0
```

---

### P2.2: No Cross-Camera Duplicate Detection
**Severity:** 🟡 IMPORTANT  
**Module:** Module 4 (Occupancy)  
**Impact:** MEDIUM - Count can be 2x actual (multi-camera rooms)  
**Effort:** 3-4 hours  
**Status:** ❌ Not Started

**Description:**
- 2 cameras in same room
- Person in both cameras → counted twice
- MultiCameraAggregator just sums all cameras

**Solution:**
- Use person tracking IDs across cameras
- Deduplicate by person, not camera count

---

### P2.3: No Input Validation/Security
**Severity:** 🟡 IMPORTANT  
**Module:** System-Wide  
**Impact:** MEDIUM - SQL injection, XSS possible  
**Effort:** 4-6 hours  
**Status:** ❌ Not Started

**Description:**
- No input validation on API endpoints
- No regex validation for plate text
- No XSS protection in frontend
- No CSRF tokens

**Solution:**
- Add Pydantic validators to all models
- Add input sanitization
- Add CORS/CSRF protection

---

## SUMMARY TABLE

| Bug ID | Title | Severity | Effort | Status |
|--------|-------|----------|--------|--------|
| P0.1 | RTSP Stream Conversion | 🔴 BLOCKER | 3-4d | ❌ |
| P0.2 | Background Scheduler | 🔴 BLOCKER | 2-3h | ❌ |
| P0.3 | Early Exit Detection | 🔴 BLOCKER | 2-3h | ❌ |
| P0.4 | Double-Entry Prevention | 🔴 BLOCKER | 2-3h | ❌ |
| P1.1 | ANPR Confidence | 🟠 CRITICAL | 4-6h | ❌ |
| P1.2 | Plate Validation | 🟠 CRITICAL | 2-3h | ❌ |
| P1.3 | AWS Retry Logic | 🟠 CRITICAL | 2-3h | ❌ |
| P1.4 | Grace Period Enforcement | 🟠 CRITICAL | 1-2h | ❌ |
| P1.5 | Occupancy Aggregation | 🟠 CRITICAL | 1-2h | ❌ |
| P2.1 | Occupancy Drift | 🟡 IMPORTANT | 2-3h | ❌ |
| P2.2 | Cross-Camera Dedup | 🟡 IMPORTANT | 3-4h | ❌ |
| P2.3 | Input Validation | 🟡 IMPORTANT | 4-6h | ❌ |

**Total Effort to Production:** ~25-35 hours (~1 week with 1 developer)

---

## DEPLOYMENT GATE CHECKLIST

Before releasing to first customer:
- [ ] All P0 blockers fixed and tested
- [ ] All P1 critical issues fixed
- [ ] All P2 important issues fixed (at least P2.1)
- [ ] Unit tests written (min 50% coverage)
- [ ] Integration tests passed
- [ ] Load testing completed (1000 people, 100 vehicles/day)
- [ ] Security audit passed
- [ ] Database backup/restore tested
- [ ] Runbooks written for common issues
- [ ] Support team trained
