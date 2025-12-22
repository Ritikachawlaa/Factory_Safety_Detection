"""
AWS Rekognition Integration for Face Recognition
Replaces DeepFace with AWS Rekognition API
Loads credentials from .env file
"""
import boto3
import numpy as np
from PIL import Image
import io
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AWSRecognizer:
    """AWS Rekognition face detection and recognition"""
    
    def __init__(self, collection_id=None, region=None):
        # Load from .env if not provided
        self.collection_id = collection_id or os.getenv('AWS_REKOGNITION_COLLECTION_ID', 'employees')
        self.region = region or os.getenv('AWS_REGION', 'us-east-1')
        
        # Get AWS credentials from .env
        aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        
        if not aws_access_key or not aws_secret_key:
            raise ValueError(
                "❌ AWS credentials not found in .env file\n"
                "Please add AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY to .env"
            )
        
        # Initialize AWS client with credentials from .env
        self.client = boto3.client(
            'rekognition',
            region_name=self.region,
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key
        )
        # Lower threshold to 50% - AWS is very strict, need lenient matching
        # This prevents "Unknown" when it's clearly the same person
        self.confidence_threshold = 50  # 50% similarity for match (very lenient)
        
        print(f"✅ AWS Rekognition initialized")
        print(f"   Region: {self.region}")
        print(f"   Collection: {self.collection_id}")
        print(f"   Threshold: {self.confidence_threshold}% (very lenient for accuracy)")
        
    def detect_faces(self, frame):
        """
        Detect faces in frame using AWS Rekognition
        Args:
            frame: numpy array (BGR format from OpenCV)
        Returns:
            List of face boxes: [{'x1': int, 'y1': int, 'x2': int, 'y2': int}, ...]
        """
        try:
            # Convert frame to image bytes
            frame_rgb = frame[:, :, ::-1]  # BGR to RGB
            pil_image = Image.fromarray(frame_rgb)
            
            # Convert to bytes
            img_bytes = io.BytesIO()
            pil_image.save(img_bytes, format='JPEG')
            img_bytes.seek(0)
            
            # Call AWS Rekognition
            response = self.client.detect_faces(
                Image={'Bytes': img_bytes.getvalue()},
                Attributes=['ALL']
            )
            
            faces = []
            for face_detail in response.get('FaceDetails', []):
                # Get bounding box
                bbox = face_detail['BoundingBox']
                h, w = frame.shape[:2]
                
                x1 = int(bbox['Left'] * w)
                y1 = int(bbox['Top'] * h)
                x2 = int((bbox['Left'] + bbox['Width']) * w)
                y2 = int((bbox['Top'] + bbox['Height']) * h)
                
                faces.append({
                    'x1': x1,
                    'y1': y1,
                    'x2': x2,
                    'y2': y2,
                    'confidence': face_detail.get('Confidence', 0),
                    'face_data': face_detail  # Store for additional analysis
                })
            
            print(f"✅ AWS DETECT_FACES: Found {len(faces)} faces")
            return faces
            
        except Exception as e:
            print(f"❌ AWS Detection Error: {e}")
            return []
    
    def recognize_faces(self, frame, face_boxes=None):
        """
        Recognize faces by searching collection
        Args:
            frame: numpy array (BGR)
            face_boxes: List of detected face boxes (if None, will auto-detect)
        Returns:
            {
                'recognized': ['Ritika', 'John'],
                'unknown': 2,
                'face_bboxes': [box1, box2, ...]
            }
        """
        try:
            # If no face boxes provided, detect them first
            if not face_boxes:
                print("   🔍 AWS: Detecting faces...")
                face_boxes = self.detect_faces(frame)
                print(f"   ✅ AWS: Found {len(face_boxes)} faces")
            
            recognized_names = []
            unknown_count = 0
            all_bboxes = []
            
            for idx, face_box in enumerate(face_boxes):
                # Extract face crop
                x1, y1, x2, y2 = face_box['x1'], face_box['y1'], face_box['x2'], face_box['y2']
                
                # Store bbox for response
                all_bboxes.append({
                    'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                    'confidence': face_box.get('confidence', 0.95)
                })
                
                # Skip if face region EXTREMELY small (long-distance optimization)
                # AWS needs minimum 10px to work (was 20px)
                # Allows detection of faces very far from camera
                if (x2 - x1) < 10 or (y2 - y1) < 10:
                    print(f"   ⚠️  Face {idx} too small (<10px), skipping recognition")
                    unknown_count += 1
                    continue
                
                # Warn if small but still process
                if (x2 - x1) < 20 or (y2 - y1) < 20:
                    print(f"   🔍 Face {idx} small ({x2-x1}x{y2-y1}px) - long-distance, processing anyway...")
                
                face_crop = frame[y1:y2, x1:x2]
                
                # Convert to image bytes
                face_rgb = face_crop[:, :, ::-1]  # BGR to RGB
                pil_image = Image.fromarray(face_rgb)
                
                img_bytes = io.BytesIO()
                pil_image.save(img_bytes, format='JPEG')
                img_bytes.seek(0)
                
                # Search in collection
                response = self.client.search_faces_by_image(
                    CollectionId=self.collection_id,
                    Image={'Bytes': img_bytes.getvalue()},
                    MaxFaces=1,
                    FaceMatchThreshold=self.confidence_threshold
                )
                
                # Check if match found
                if response.get('FaceMatches'):
                    match = response['FaceMatches'][0]
                    face_record = match['Face']
                    external_id = face_record.get('ExternalImageId', 'Unknown')
                    similarity = match['Similarity']
                    
                    print(f"   ✅ MATCHED: {external_id} (Similarity: {similarity:.1f}%)")
                    recognized_names.append(external_id)
                else:
                    print(f"   ❓ NO MATCH: Face {idx} (Similarity < {self.confidence_threshold}%)")
                    unknown_count += 1
            
            result = {
                'recognized': recognized_names,
                'unknown': unknown_count,
                'face_bboxes': all_bboxes  # Return all detected bboxes
            }
            
            print(f"✅ AWS RECOGNITION RESULT: recognized={recognized_names}, unknown={unknown_count}")
            return result
            
        except Exception as e:
            print(f"❌ AWS Recognition Error: {e}")
            return {
                'recognized': [],
                'unknown': len(face_boxes),
                'face_bboxes': face_boxes
            }
    
    def index_face(self, image_path, external_id):
        """
        Add a new face to collection (e.g., new employee)
        Args:
            image_path: Path to image file
            external_id: Name or ID to associate with face
        """
        try:
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            
            response = self.client.index_faces(
                CollectionId=self.collection_id,
                Image={'Bytes': image_bytes},
                ExternalImageId=external_id
            )
            
            print(f"✅ INDEXED: {external_id}")
            return True
            
        except Exception as e:
            print(f"❌ Index Error: {e}")
            return False
    
    def delete_face_from_collection(self, face_id):
        """Remove a face from collection"""
        try:
            self.client.delete_faces(
                CollectionId=self.collection_id,
                FaceIds=[face_id]
            )
            print(f"✅ DELETED: {face_id}")
            return True
        except Exception as e:
            print(f"❌ Delete Error: {e}")
            return False
    
    def list_collection_faces(self):
        """List all faces in collection"""
        try:
            response = self.client.list_faces(
                CollectionId=self.collection_id,
                MaxResults=100
            )
            
            faces = response.get('Faces', [])
            print(f"📋 COLLECTION '{self.collection_id}' has {len(faces)} faces:")
            for face in faces:
                print(f"   - {face['ExternalImageId']} (ID: {face['FaceId'][:8]}...)")
            
            return faces
        except Exception as e:
            print(f"❌ List Error: {e}")
            return []
