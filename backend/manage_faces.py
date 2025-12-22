#!/usr/bin/env python3
"""
Helper script to manage AWS Rekognition collection
- Index new faces (employees)
- List existing faces
- Delete faces
- Test recognition
"""

import boto3
import sys
import os
from pathlib import Path

class FaceCollectionManager:
    def __init__(self, collection_id='employees', region='us-east-1'):
        self.collection_id = collection_id
        self.client = boto3.client('rekognition', region_name=region)
    
    def index_face(self, image_path, person_name):
        """Add a face to collection"""
        try:
            if not os.path.exists(image_path):
                print(f"❌ File not found: {image_path}")
                return False
            
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            
            response = self.client.index_faces(
                CollectionId=self.collection_id,
                Image={'Bytes': image_bytes},
                ExternalImageId=person_name
            )
            
            faces = response.get('FaceRecords', [])
            if faces:
                print(f"✅ INDEXED: {person_name}")
                print(f"   Face ID: {faces[0]['Face']['FaceId'][:8]}...")
                return True
            else:
                print(f"❌ No faces detected in {image_path}")
                return False
        
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def list_faces(self):
        """List all faces in collection"""
        try:
            response = self.client.list_faces(
                CollectionId=self.collection_id,
                MaxResults=100
            )
            
            faces = response.get('Faces', [])
            if not faces:
                print(f"📋 Collection '{self.collection_id}' is empty")
                return []
            
            print(f"📋 Collection '{self.collection_id}' has {len(faces)} faces:")
            for face in faces:
                print(f"   - {face['ExternalImageId']:<20} (ID: {face['FaceId'][:8]}...)")
            
            return faces
        
        except Exception as e:
            print(f"❌ Error: {e}")
            return []
    
    def delete_face(self, face_id):
        """Remove a face from collection"""
        try:
            self.client.delete_faces(
                CollectionId=self.collection_id,
                FaceIds=[face_id]
            )
            print(f"✅ DELETED: {face_id[:8]}...")
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def delete_by_name(self, person_name):
        """Delete all faces for a person"""
        try:
            response = self.client.list_faces(CollectionId=self.collection_id)
            
            deleted = 0
            for face in response.get('Faces', []):
                if face.get('ExternalImageId') == person_name:
                    self.client.delete_faces(
                        CollectionId=self.collection_id,
                        FaceIds=[face['FaceId']]
                    )
                    deleted += 1
            
            if deleted > 0:
                print(f"✅ DELETED {deleted} face(s) for {person_name}")
            else:
                print(f"❌ No faces found for {person_name}")
            
            return deleted > 0
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def test_recognition(self, image_path, person_name):
        """Test if an image matches a person in collection"""
        try:
            if not os.path.exists(image_path):
                print(f"❌ File not found: {image_path}")
                return False
            
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            
            response = self.client.search_faces_by_image(
                CollectionId=self.collection_id,
                Image={'Bytes': image_bytes},
                MaxFaces=1,
                FaceMatchThreshold=80
            )
            
            matches = response.get('FaceMatches', [])
            if matches:
                match = matches[0]
                matched_name = match['Face']['ExternalImageId']
                similarity = match['Similarity']
                
                if matched_name == person_name:
                    print(f"✅ MATCH! Similarity: {similarity:.1f}%")
                    return True
                else:
                    print(f"❌ MISMATCH! Matched: {matched_name} (Similarity: {similarity:.1f}%)")
                    return False
            else:
                print(f"❌ NO MATCH found for {person_name}")
                return False
        
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

def main():
    manager = FaceCollectionManager()
    
    if len(sys.argv) < 2:
        print("📖 Face Collection Manager\n")
        print("Usage:")
        print("  python manage_faces.py list")
        print("  python manage_faces.py add <image_path> <person_name>")
        print("  python manage_faces.py delete <person_name>")
        print("  python manage_faces.py test <image_path> <person_name>")
        print("\nExamples:")
        print("  python manage_faces.py add ritika.jpg Ritika")
        print("  python manage_faces.py list")
        print("  python manage_faces.py test test_ritika.jpg Ritika")
        print("  python manage_faces.py delete Ritika")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'list':
        manager.list_faces()
    
    elif command == 'add':
        if len(sys.argv) < 4:
            print("❌ Usage: python manage_faces.py add <image_path> <person_name>")
            return
        image_path = sys.argv[2]
        person_name = sys.argv[3]
        manager.index_face(image_path, person_name)
    
    elif command == 'delete':
        if len(sys.argv) < 3:
            print("❌ Usage: python manage_faces.py delete <person_name>")
            return
        person_name = sys.argv[2]
        manager.delete_by_name(person_name)
    
    elif command == 'test':
        if len(sys.argv) < 4:
            print("❌ Usage: python manage_faces.py test <image_path> <person_name>")
            return
        image_path = sys.argv[2]
        person_name = sys.argv[3]
        manager.test_recognition(image_path, person_name)
    
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == '__main__':
    main()
