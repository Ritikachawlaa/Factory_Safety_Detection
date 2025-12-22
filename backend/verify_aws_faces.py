"""
Verify and re-register faces in AWS Rekognition collection
Use this to debug if faces are properly indexed
"""
import boto3
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Get AWS config
aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
region = os.getenv('AWS_REGION', 'us-east-1')
collection_id = os.getenv('AWS_REKOGNITION_COLLECTION_ID', 'employees')

# Initialize AWS client
client = boto3.client(
    'rekognition',
    region_name=region,
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key
)

def list_faces_in_collection():
    """List all faces currently in the collection"""
    print(f"\n📊 Faces in collection '{collection_id}':")
    print("=" * 60)
    
    try:
        response = client.list_faces(CollectionId=collection_id)
        faces = response.get('Faces', [])
        
        if not faces:
            print("❌ NO FACES FOUND IN COLLECTION!")
            print("   This explains why Ritika is not being recognized")
            return False
        
        for face in faces:
            face_id = face['FaceId']
            external_id = face['ExternalImageId']
            print(f"   ✅ Face ID: {face_id[:20]}... | Name: {external_id}")
        
        print(f"\n✅ Total faces in collection: {len(faces)}")
        return len(faces) > 0
        
    except Exception as e:
        print(f"❌ Error listing faces: {e}")
        return False

def register_ritika():
    """Register Ritika's face from database"""
    print(f"\n📸 Registering Ritika...")
    print("=" * 60)
    
    # Find Ritika's image in database
    database_path = Path(__file__).parent / 'database' / 'employees'
    ritika_images = list(database_path.glob('Ritika.*'))
    
    if not ritika_images:
        print(f"❌ Ritika's image not found in {database_path}")
        print("   Please add Ritika.jpg or Ritika.png to backend/database/employees/")
        return False
    
    ritika_image = ritika_images[0]
    print(f"   Found: {ritika_image.name}")
    
    try:
        # Read image
        with open(ritika_image, 'rb') as f:
            image_bytes = f.read()
        
        # Index face in collection
        response = client.index_faces(
            CollectionId=collection_id,
            Image={'Bytes': image_bytes},
            ExternalImageId='Ritika'
        )
        
        faces = response.get('FaceRecords', [])
        if faces:
            face_id = faces[0]['Face']['FaceId']
            print(f"   ✅ SUCCESS! Face indexed with ID: {face_id[:20]}...")
            print(f"   ✅ Name: Ritika")
            return True
        else:
            print(f"❌ Failed to index face")
            return False
            
    except Exception as e:
        print(f"❌ Error registering Ritika: {e}")
        return False

def test_ritika_recognition(test_image_path=None):
    """Test if Ritika can be recognized"""
    print(f"\n🔍 Testing Ritika recognition...")
    print("=" * 60)
    
    # If no test image provided, use the database image
    if not test_image_path:
        database_path = Path(__file__).parent / 'database' / 'employees'
        ritika_images = list(database_path.glob('Ritika.*'))
        if not ritika_images:
            print("❌ No test image found")
            return False
        test_image_path = ritika_images[0]
    
    print(f"   Testing with: {test_image_path.name}")
    
    try:
        with open(test_image_path, 'rb') as f:
            image_bytes = f.read()
        
        # Search for face in collection
        response = client.search_faces_by_image(
            CollectionId=collection_id,
            Image={'Bytes': image_bytes},
            MaxFaces=1,
            FaceMatchThreshold=50  # 50% threshold
        )
        
        matches = response.get('FaceMatches', [])
        
        if matches:
            match = matches[0]
            external_id = match['Face']['ExternalImageId']
            similarity = match['Similarity']
            print(f"   ✅ MATCH FOUND!")
            print(f"      Name: {external_id}")
            print(f"      Similarity: {similarity:.1f}%")
            return True
        else:
            print(f"   ❌ NO MATCH FOUND!")
            print(f"   Ritika is in collection, but similarity < 50%")
            print(f"   This means her photo quality may be poor")
            return False
            
    except Exception as e:
        print(f"❌ Error testing recognition: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("AWS REKOGNITION FACE VERIFICATION TOOL")
    print("=" * 60)
    
    print("\n1️⃣  Checking faces in collection...")
    has_faces = list_faces_in_collection()
    
    if not has_faces:
        print("\n2️⃣  Registering Ritika...")
        registered = register_ritika()
        
        if registered:
            print("\n3️⃣  Testing recognition...")
            test_ritika_recognition()
    else:
        print("\n2️⃣  Testing recognition...")
        test_ritika_recognition()
    
    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)

if __name__ == '__main__':
    main()
