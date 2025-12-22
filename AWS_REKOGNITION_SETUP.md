# 🚀 AWS Rekognition Setup Guide

## Step 1: AWS Account & IAM Setup

### 1.1 Create AWS Account
```
1. Go to https://aws.amazon.com
2. Click "Create an AWS Account"
3. Fill email, password, account name
4. Add payment method (credit card)
5. Verify phone number
⏱️ Time: 10 minutes
```

### 1.2 Create IAM User (Best Practice)

**Don't use root account.** Create a dedicated user:

```bash
# In AWS Console:
1. Go to IAM → Users
2. Click "Create user"
3. Name: rekognition-user
4. ✅ Check "Provide user access to the AWS Management Console"
5. ✅ Check "I want to create an IAM user"
6. Click Next
7. Click Attach policies directly
8. Search: "AmazonRekognition"
9. ✅ Select "AmazonRekognitionFullAccess"
10. Click Next → Create user
11. Download CSV file (IMPORTANT - save this!)
```

**CSV file contains:**
```
Access key ID:     AKIA...
Secret access key: ...
```

**Keep this safe!** You'll need it.

---

## Step 2: Install AWS CLI

### 2.1 Install

```bash
pip install awscli boto3 pillow
```

### 2.2 Configure AWS Credentials

```bash
aws configure
```

When prompted, paste:
```
AWS Access Key ID: [Paste from CSV]
AWS Secret Access Key: [Paste from CSV]
Default region name: us-east-1
Default output format: json
```

✅ Credentials saved to: `~/.aws/credentials`

### 2.3 Verify Setup

```bash
aws sts get-caller-identity
```

Should output:
```json
{
    "UserId": "AIDAI...",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/rekognition-user"
}
```

---

## Step 3: Create Rekognition Collection

```bash
# Create collection for storing known faces
aws rekognition create-collection --collection-id employees

# Verify
aws rekognition describe-collection --collection-id employees
```

Output:
```json
{
    "CollectionArn": "arn:aws:rekognition:us-east-1:...",
    "CollectionName": "employees",
    "FaceCount": 0,
    "FaceModelVersion": "6.0"
}
```

✅ Collection created!

---

## Step 4: Register Ritika's Face

### 4.1 Prepare Photo

**Requirements:**
- 📸 Clear photo of Ritika
- 👤 Face occupies at least 40x40 pixels
- 💡 Good lighting (no shadows on face)
- 📐 Frontal view (looking at camera)
- 📄 JPEG or PNG format

**Where to get:**
- Use a recent photo from your database
- Or take a new photo with good lighting
- Save as: `ritika.jpg`

### 4.2 Index Face

**Option A: Local file**
```bash
aws rekognition index-faces \
  --collection-id employees \
  --image '{"Bytes": ..., "Format": "jpg"}' \
  --external-image-id "Ritika"

# Easier way - use Python script below
```

**Option B: Use Python (Recommended)**

```python
# File: index_faces.py
import boto3

rekognition = boto3.client('rekognition', region_name='us-east-1')

# Register Ritika
with open('ritika.jpg', 'rb') as f:
    response = rekognition.index_faces(
        CollectionId='employees',
        Image={'Bytes': f.read()},
        ExternalImageId='Ritika'
    )

print(response)
# Output: FaceRecords with indexed face ID

# List all faces in collection
response = rekognition.list_faces(CollectionId='employees')
for face in response['Faces']:
    print(f"- {face['ExternalImageId']}")
```

Run:
```bash
python index_faces.py

# Output:
# - Ritika
```

✅ Ritika's face registered!

---

## Step 5: Update Backend Code

### 5.1 Update requirements.txt

Add to `backend/requirements.txt`:
```
boto3>=1.26.0
pillow>=9.0.0
```

Install:
```bash
pip install -r requirements.txt
```

### 5.2 Update Detection Pipeline

Edit `backend/services/detection_pipeline.py`:

```python
# At top, add:
from services.aws_recognition import AWSRecognizer

# In __init__, replace:
# self.face_detector = FaceRecognizer()
# With:
self.use_aws = True  # Set to False to use DeepFace
if self.use_aws:
    self.face_detector = AWSRecognizer(collection_id='employees')
else:
    self.face_detector = FaceRecognizer()

# In load_models, add:
if self.use_aws:
    print("✅ AWS Rekognition Ready")
else:
    print("✅ DeepFace Ready")
```

### 5.3 Update Face Detection Call

In `process_frame` method, the call is the same:

```python
# This works for BOTH DeepFace and AWS:
face_result = self.face_detector.recognize_faces(frame, face_boxes)
```

✅ No other changes needed! Session tracking stays the same.

---

## Step 6: Test AWS Integration

### 6.1 Test Offline First

```python
# File: test_aws_recognition.py
from services.aws_recognition import AWSRecognizer
import cv2

# Initialize
aws_recognizer = AWSRecognizer(collection_id='employees')

# Load test image
frame = cv2.imread('test_ritika.jpg')

# Detect faces
faces = aws_recognizer.detect_faces(frame)
print(f"Detected {len(faces)} faces")

# Recognize
result = aws_recognizer.recognize_faces(frame, faces)
print(f"Recognized: {result['recognized']}")
print(f"Unknown: {result['unknown']}")
```

Run:
```bash
python test_aws_recognition.py
```

Expected output:
```
✅ AWS DETECT_FACES: Found 1 faces
   ✅ MATCHED: Ritika (Similarity: 98.5%)
✅ AWS RECOGNITION RESULT: recognized=['Ritika'], unknown=0
```

### 6.2 Test with Live System

```bash
cd backend
python main_unified.py
```

Check console for:
```
✅ AWS Rekognition Ready
[PIPELINE] Detected 1 faces
   ✅ MATCHED: Ritika (Similarity: 97.3%)
✅ RECOGNIZED MATCH: Track ID 1 (known: Ritika)
```

---

## Cost Optimization

### Problem
```
1 FPS = 86,400 frames/day = $172.8/day = $5,184/month 😱
```

### Solution
Only process when face detected:

```python
# In main_unified.py:
def process_frame(frame):
    # Step 1: Detect with Haar Cascade (FREE)
    haar_faces = detect_with_haar(frame)
    
    if haar_faces:
        # Step 2: Only then use AWS Rekognition (PAID)
        result = aws_recognizer.recognize_faces(frame, haar_faces)
    else:
        # No faces detected, skip AWS call
        result = {'recognized': [], 'unknown': 0}
    
    return result

# Result:
# 10% of frames have faces → 0.1 × 86,400 × $0.002 = $17.28/day = $518/month
```

---

## Troubleshooting

### Issue: "Invalid credentials"
```
Solution: 
1. Check AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
2. Run: aws sts get-caller-identity
3. If fails, re-run: aws configure
```

### Issue: "Collection not found"
```
Solution:
1. Verify collection exists: aws rekognition list-collections
2. If missing, create: aws rekognition create-collection --collection-id employees
```

### Issue: "Similarity too low"
```
Solution:
1. Use better photo of Ritika
2. Take new photo with good lighting (no shadows)
3. Ensure face is clearly visible
4. Lower threshold: confidence_threshold = 70  # Default is 80
```

### Issue: "Resource limit exceeded"
```
Solution:
1. You're calling API too fast
2. Add delay: time.sleep(0.1)  # 100ms between calls
3. Or use cost optimization (only process when faces detected)
```

---

## Costs Summary

| Scenario | Daily Cost | Monthly Cost |
|----------|-----------|-------------|
| 30 FPS continuous | $172.80 | $5,184 |
| 1 FPS continuous | $5.76 | $172.80 |
| 0.5 FPS (every 2s) | $2.88 | $86.40 |
| **Smart: Only when faces** | $0.17 | $5.18 |

---

## Next Steps

1. ✅ Create AWS account
2. ✅ Create IAM user
3. ✅ Create Rekognition collection
4. ✅ Register Ritika's face
5. ✅ Update backend code
6. ✅ Test with live system
7. ✅ Monitor AWS costs in CloudWatch

---

## Files to Check

- `backend/services/aws_recognition.py` - AWS integration
- `backend/services/detection_pipeline.py` - Pipeline with AWS support
- `backend/main_unified.py` - No changes needed
- `index_faces.py` - Script to add more people

All session tracking and UI works exactly the same! 🎯
