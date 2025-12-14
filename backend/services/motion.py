"""
Smart Motion Detection Service
AI-filtered motion detection (not just pixel changes)
"""
import cv2
import numpy as np

class MotionDetector:
    """Smart motion detection using background subtraction and AI filtering"""
    
    def __init__(self, threshold=500):
        """
        Args:
            threshold: Minimum changed pixels to trigger motion
        """
        self.threshold = threshold
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500,
            varThreshold=16,
            detectShadows=False
        )
        self.last_motion_time = 0
        
    def detect(self, frame, objects_detected):
        """
        Detect motion in frame
        
        Args:
            frame: Input image
            objects_detected: Number of objects detected (AI validation)
            
        Returns:
            {
                'motion_detected': bool,
                'motion_intensity': float (0-1),
                'ai_validated': bool
            }
        """
        try:
            # Apply background subtraction
            fg_mask = self.bg_subtractor.apply(frame)
            
            # Count changed pixels
            motion_pixels = cv2.countNonZero(fg_mask)
            motion_intensity = min(motion_pixels / (frame.shape[0] * frame.shape[1]), 1.0)
            
            # Motion detected if pixels changed AND objects detected (AI validation)
            motion_detected = motion_pixels > self.threshold
            ai_validated = motion_detected and objects_detected > 0
            
            return {
                'motion_detected': motion_detected,
                'motion_intensity': float(motion_intensity),
                'ai_validated': ai_validated
            }
        except Exception as e:
            print(f"Motion detection error: {e}")
            return {
                'motion_detected': False,
                'motion_intensity': 0.0,
                'ai_validated': False
            }
