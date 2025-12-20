"""
Video RTSP-to-Web MJPEG Streaming Wrapper
Converts RTSP streams to MJPEG (Motion JPEG) format for browser viewing.
Overlays AI model predictions (bounding boxes) on the video frames.

Key Features:
- RTSP stream capture using OpenCV
- Real-time bounding box overlay from detection models
- MJPEG streaming via FastAPI StreamingResponse
- Frame rate control and quality optimization
- Graceful error handling and reconnection logic
"""

import logging
import cv2
import io
import time
import numpy as np
from typing import Optional, Generator, Dict, List, Tuple
from datetime import datetime
from threading import Lock
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RTSPStreamManager:
    """
    Manages RTSP stream connections and frame capture.
    Handles reconnection, frame buffering, and error recovery.
    """
    
    def __init__(
        self,
        rtsp_url: str,
        buffer_size: int = 1,
        reconnect_attempts: int = 3,
        timeout_seconds: int = 30
    ):
        """
        Initialize RTSP stream manager.
        
        Args:
            rtsp_url: RTSP stream URL (e.g., rtsp://camera_ip:554/stream)
            buffer_size: Frame buffer size (1 = always get latest)
            reconnect_attempts: Max reconnection attempts before giving up
            timeout_seconds: OpenCV cap timeout
        """
        self.rtsp_url = rtsp_url
        self.buffer_size = buffer_size
        self.reconnect_attempts = reconnect_attempts
        self.timeout_seconds = timeout_seconds
        
        self.cap = None
        self.is_connected = False
        self.frame_count = 0
        self.connection_errors = 0
        self.last_frame = None
        self.frame_lock = Lock()
        
        logger.info(f"✅ RTSPStreamManager initialized for {rtsp_url}")
    
    def connect(self) -> bool:
        """
        Connect to RTSP stream (non-blocking).
        
        Returns:
            True if connection object created (actual connection tested on first frame)
        """
        try:
            logger.info(f"🔌 Connecting to RTSP stream: {self.rtsp_url}")
            
            # Create video capture object (doesn't actually connect yet)
            self.cap = cv2.VideoCapture(self.rtsp_url)
            
            # Set camera properties for better performance
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, self.buffer_size)
            self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
            self.cap.set(cv2.CAP_PROP_FPS, 30)  # Request 30 FPS
            self.cap.set(cv2.CAP_PROP_CONNECT_TIMEOUT, 5000)  # 5 second timeout
            
            # Don't test connection here - let it happen on first frame read
            # This prevents blocking during startup
            self.is_connected = True
            logger.info(f"✅ RTSP stream handler created (actual connection on first frame)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating RTSP capture: {e}")
            self.is_connected = False
            return False
            
            return True
        
        except Exception as e:
            logger.error(f"❌ Failed to connect to RTSP stream: {e}")
            self.is_connected = False
            return False
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        Get the latest frame from the stream.
        
        Returns:
            Frame as numpy array, or None if stream is disconnected
        """
        if not self.is_connected or self.cap is None:
            return None
        
        try:
            ret, frame = self.cap.read()
            
            if not ret:
                self._handle_connection_error()
                return self.last_frame  # Return cached frame
            
            self.frame_count += 1
            
            with self.frame_lock:
                self.last_frame = frame
            
            return frame
        
        except Exception as e:
            logger.error(f"❌ Error reading frame: {e}")
            self._handle_connection_error()
            return self.last_frame
    
    def _handle_connection_error(self) -> None:
        """Handle connection error and attempt reconnection."""
        self.connection_errors += 1
        logger.warning(f"⚠️ Connection error #{self.connection_errors}")
        
        if self.connection_errors >= self.reconnect_attempts:
            logger.error(f"❌ Max reconnection attempts ({self.reconnect_attempts}) exceeded")
            self.disconnect()
            return
        
        # Attempt to reconnect
        time.sleep(2)
        self.connect()
    
    def disconnect(self) -> None:
        """Disconnect from RTSP stream."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        
        self.is_connected = False
        logger.info(f"✅ Disconnected from RTSP stream (read {self.frame_count} frames)")
    
    def get_status(self) -> Dict:
        """Get current stream status."""
        if not self.cap:
            return {'connected': False}
        
        return {
            'connected': self.is_connected,
            'url': self.rtsp_url,
            'frames_read': self.frame_count,
            'connection_errors': self.connection_errors,
            'width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': self.cap.get(cv2.CAP_PROP_FPS)
        }


class BoundingBoxOverlay:
    """
    Overlays bounding boxes and detection metadata on video frames.
    Supports multiple detection types with different colors.
    """
    
    # Color scheme for different detection types
    COLOR_PALETTE = {
        'person': (0, 255, 0),      # Green
        'helmet': (0, 255, 255),    # Yellow
        'vehicle': (255, 0, 0),     # Blue
        'face': (255, 0, 255),      # Magenta
        'pallet': (0, 165, 255),    # Orange
        'danger': (0, 0, 255),      # Red
        'alert': (0, 0, 255)        # Red
    }
    
    # Font settings
    FONT = cv2.FONT_HERSHEY_SIMPLEX
    FONT_SCALE = 0.5
    FONT_THICKNESS = 1
    BOX_THICKNESS = 2
    
    def __init__(self):
        """Initialize bounding box overlay service."""
        logger.info("✅ BoundingBoxOverlay initialized")
    
    def draw_boxes(
        self,
        frame: np.ndarray,
        detections: List[Dict]
    ) -> np.ndarray:
        """
        Draw bounding boxes on frame.
        
        Args:
            frame: Input frame
            detections: List of detection dicts with keys:
                - bbox: (x1, y1, x2, y2)
                - class_name: str (e.g., 'person', 'vehicle')
                - confidence: float (0.0-1.0)
                - track_id: Optional[int]
        
        Returns:
            Frame with drawn boxes
        """
        if frame is None or len(detections) == 0:
            return frame
        
        frame_copy = frame.copy()
        
        for detection in detections:
            try:
                bbox = detection.get('bbox', [])
                class_name = detection.get('class_name', 'unknown')
                confidence = detection.get('confidence', 0.0)
                track_id = detection.get('track_id', None)
                
                if len(bbox) < 4:
                    continue
                
                x1, y1, x2, y2 = map(int, bbox[:4])
                
                # Get color for this class
                color = self.COLOR_PALETTE.get(class_name, (200, 200, 200))
                
                # Draw bounding box
                cv2.rectangle(frame_copy, (x1, y1), (x2, y2), color, self.BOX_THICKNESS)
                
                # Prepare label text
                label = f"{class_name} {confidence:.2%}"
                if track_id is not None:
                    label += f" #{track_id}"
                
                # Draw label background
                label_size = cv2.getTextSize(
                    label, self.FONT, self.FONT_SCALE, self.FONT_THICKNESS
                )[0]
                
                label_x = x1
                label_y = max(y1 - 5, label_size[1] + 5)
                
                cv2.rectangle(
                    frame_copy,
                    (label_x, label_y - label_size[1] - 5),
                    (label_x + label_size[0], label_y),
                    color,
                    -1  # Filled rectangle
                )
                
                # Draw label text
                cv2.putText(
                    frame_copy,
                    label,
                    (label_x, label_y - 3),
                    self.FONT,
                    self.FONT_SCALE,
                    (255, 255, 255),  # White text
                    self.FONT_THICKNESS
                )
            
            except Exception as e:
                logger.debug(f"⚠️ Error drawing detection: {e}")
                continue
        
        return frame_copy
    
    def draw_info_panel(
        self,
        frame: np.ndarray,
        info: Dict
    ) -> np.ndarray:
        """
        Draw information panel on frame.
        
        Args:
            frame: Input frame
            info: Information dict with keys like:
                - timestamp: str
                - fps: float
                - detections: int
                - camera_id: str
        
        Returns:
            Frame with info panel
        """
        if frame is None:
            return frame
        
        frame_copy = frame.copy()
        frame_height, frame_width = frame_copy.shape[:2]
        
        # Panel position and size
        panel_height = 30
        panel_y = frame_height - panel_height
        
        # Draw semi-transparent background
        overlay = frame_copy.copy()
        cv2.rectangle(overlay, (0, panel_y), (frame_width, frame_height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.3, frame_copy, 0.7, 0, frame_copy)
        
        # Prepare info text
        timestamp = info.get('timestamp', '')
        fps = info.get('fps', 0)
        detections = info.get('detections', 0)
        camera_id = info.get('camera_id', 'CAM-0')
        
        info_text = f"{camera_id} | {timestamp} | FPS: {fps:.1f} | Objects: {detections}"
        
        # Draw text
        cv2.putText(
            frame_copy,
            info_text,
            (10, frame_height - 8),
            self.FONT,
            self.FONT_SCALE,
            (0, 255, 0),  # Green text
            self.FONT_THICKNESS
        )
        
        return frame_copy


class MJPEGStreamEncoder:
    """
    Encodes frames as MJPEG (Motion JPEG) for streaming to browsers.
    Yields frames in multipart/x-mixed-replace format.
    """
    
    # JPEG quality (0-100)
    JPEG_QUALITY = 80
    BOUNDARY = b'frame'
    CONTENT_TYPE = b'image/jpeg'
    
    def __init__(self, frame_rate: int = 30):
        """
        Initialize MJPEG encoder.
        
        Args:
            frame_rate: Target frames per second
        """
        self.frame_rate = frame_rate
        self.frame_delay = 1.0 / frame_rate
        logger.info(f"✅ MJPEGStreamEncoder initialized ({frame_rate} FPS)")
    
    def encode_frame_to_jpeg(self, frame: np.ndarray) -> bytes:
        """
        Encode frame to JPEG bytes.
        
        Args:
            frame: Input frame (BGR numpy array)
        
        Returns:
            JPEG bytes
        """
        try:
            # Encode frame as JPEG
            encode_param = [cv2.IMWRITE_JPEG_QUALITY, self.JPEG_QUALITY]
            success, jpeg_data = cv2.imencode('.jpg', frame, encode_param)
            
            if not success:
                logger.error("❌ Failed to encode frame as JPEG")
                return b''
            
            return jpeg_data.tobytes()
        
        except Exception as e:
            logger.error(f"❌ Error encoding JPEG: {e}")
            return b''
    
    def generate_mjpeg_stream(
        self,
        frame_generator: callable,
        max_frames: Optional[int] = None
    ) -> Generator[bytes, None, None]:
        """
        Generate MJPEG stream from frame generator.
        Yields multipart/x-mixed-replace boundary + JPEG frame.
        
        Args:
            frame_generator: Function that returns (frame, detections) tuples
            max_frames: Max frames to stream (None = infinite)
        
        Yields:
            MJPEG chunk bytes
        """
        frame_count = 0
        
        while max_frames is None or frame_count < max_frames:
            try:
                # Get next frame from generator
                frame, detections = frame_generator()
                
                if frame is None:
                    logger.warning("⚠️ No frame available, waiting...")
                    import time
                    time.sleep(self.frame_delay)
                    continue
                
                # Encode frame
                jpeg_bytes = self.encode_frame_to_jpeg(frame)
                
                if not jpeg_bytes:
                    continue
                
                # Yield MJPEG boundary + frame
                yield (
                    b'--' + self.BOUNDARY + b'\r\n' +
                    b'Content-Type: ' + self.CONTENT_TYPE + b'\r\n' +
                    b'Content-Length: ' + str(len(jpeg_bytes)).encode() + b'\r\n' +
                    b'Content-Disposition: inline; filename=frame.jpg\r\n' +
                    b'\r\n' +
                    jpeg_bytes +
                    b'\r\n'
                )
                
                frame_count += 1
                
                # Rate control
                import time
                time.sleep(self.frame_delay)
            
            except Exception as e:
                logger.error(f"❌ Error in MJPEG stream: {e}")
                import time
                time.sleep(1)
                continue


# ============================================================================
# FASTAPI INTEGRATION
# ============================================================================

class VideoStreamingService:
    """
    High-level service for video streaming with AI overlays.
    Coordinates RTSP capture, detection, and MJPEG encoding.
    """
    
    def __init__(
        self,
        rtsp_url: str,
        camera_id: str = "CAM-0",
        detection_model=None
    ):
        """
        Initialize video streaming service.
        
        Args:
            rtsp_url: RTSP stream URL
            camera_id: Camera identifier
            detection_model: Optional AI model for detections
        """
        self.rtsp_url = rtsp_url
        self.camera_id = camera_id
        self.detection_model = detection_model
        
        self.stream_manager = RTSPStreamManager(rtsp_url)
        self.overlay = BoundingBoxOverlay()
        self.encoder = MJPEGStreamEncoder(frame_rate=30)
        
        logger.info(f"✅ VideoStreamingService initialized for {camera_id}")
    
    def start_stream(self) -> bool:
        """Start RTSP stream connection."""
        return self.stream_manager.connect()
    
    def stop_stream(self) -> None:
        """Stop RTSP stream connection."""
        self.stream_manager.disconnect()
    
    def generate_video_stream(self) -> Generator[bytes, None, None]:
        """
        Generate MJPEG stream for FastAPI response.
        
        Yields:
            MJPEG chunk bytes
        """
        def frame_generator():
            """Inner generator for frame + detections."""
            frame = self.stream_manager.get_frame()
            
            if frame is None:
                return None, []
            
            # Run detection model if available
            detections = []
            if self.detection_model:
                try:
                    detections = self.detection_model.predict(frame)
                except Exception as e:
                    logger.debug(f"⚠️ Detection error: {e}")
            
            # Draw overlays
            frame = self.overlay.draw_boxes(frame, detections)
            
            # Draw info panel
            frame = self.overlay.draw_info_panel(
                frame,
                {
                    'timestamp': datetime.now().strftime("%H:%M:%S"),
                    'fps': self.stream_manager.cap.get(cv2.CAP_PROP_FPS) if self.stream_manager.cap else 0,
                    'detections': len(detections),
                    'camera_id': self.camera_id
                }
            )
            
            return frame, detections
        
        # Generate MJPEG stream
        yield from self.encoder.generate_mjpeg_stream(frame_generator)


def get_video_streaming_service(
    rtsp_url: str,
    camera_id: str = "CAM-0",
    detection_model=None
) -> VideoStreamingService:
    """
    Factory function to create VideoStreamingService instance.
    
    Usage in FastAPI:
        @app.get("/api/video_feed")
        async def video_feed(service: VideoStreamingService = Depends(get_video_streaming_service)):
            await service.start_stream()
            return StreamingResponse(
                service.generate_video_stream(),
                media_type="multipart/x-mixed-replace; boundary=frame"
            )
    """
    return VideoStreamingService(
        rtsp_url=rtsp_url,
        camera_id=camera_id,
        detection_model=detection_model
    )
