"""
AWS Configuration - Load from .env file
"""

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class AWSConfig:
    """AWS configuration from environment variables"""
    
    # AWS Credentials
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    
    # Rekognition Settings
    AWS_REKOGNITION_COLLECTION_ID = os.getenv('AWS_REKOGNITION_COLLECTION_ID', 'employees')
    
    # System Settings
    DETECTION_FPS = float(os.getenv('DETECTION_FPS', '0.5'))
    SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', '30'))
    FACE_DISTANCE_THRESHOLD = float(os.getenv('FACE_DISTANCE_THRESHOLD', '0.85'))
    
    @classmethod
    def validate(cls):
        """Validate that all required credentials are set"""
        if not cls.AWS_ACCESS_KEY_ID:
            raise ValueError("❌ AWS_ACCESS_KEY_ID not set in .env file")
        if not cls.AWS_SECRET_ACCESS_KEY:
            raise ValueError("❌ AWS_SECRET_ACCESS_KEY not set in .env file")
        if not cls.AWS_REKOGNITION_COLLECTION_ID:
            raise ValueError("❌ AWS_REKOGNITION_COLLECTION_ID not set in .env file")
        
        print("✅ AWS Configuration loaded successfully")
        print(f"   Region: {cls.AWS_REGION}")
        print(f"   Collection: {cls.AWS_REKOGNITION_COLLECTION_ID}")
        print(f"   FPS: {cls.DETECTION_FPS}")
        return True


# Usage in code:
# from config.aws_config import AWSConfig
# AWSConfig.validate()
# access_key = AWSConfig.AWS_ACCESS_KEY_ID
