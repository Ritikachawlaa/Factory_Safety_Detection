# ⚡ AWS Rekognition - Quick Start (5 Minutes)

## 1. Get AWS Credentials (5 min)

```bash
# Create AWS account at https://aws.amazon.com
# Create IAM user with Rekognition access
# Download CSV with credentials
```

## 2. Configure AWS CLI (2 min)

```bash
pip install awscli boto3 pillow

aws configure
# Paste Access Key ID from CSV
# Paste Secret Access Key from CSV
# Region: us-east-1
# Format: json
```

## 3. Create Collection (1 min)

```bash
aws rekognition create-collection --collection-id employees
```

## 4. Add Ritika's Face (1 min)

```bash
cd backend

# Option A: Use helper script
python manage_faces.py add /path/to/ritika.jpg Ritika

# Option B: Use AWS CLI directly
aws rekognition index-faces \
  --collection-id employees \
  --image '{"Bytes":binary}' \
  --external-image-id "Ritika"
```

## 5. Update Backend (Already Done!)

Files created:
- ✅ `backend/services/aws_recognition.py` - AWS integration
- ✅ `backend/manage_faces.py` - Face management script

No code changes needed in `main_unified.py` - just works!

## 6. Enable AWS in Pipeline (Optional)

Edit `backend/services/detection_pipeline.py`:

```python
# Line ~23, in __init__:
self.use_aws = True  # Change False to True

# That's it!
```

## 7. Restart Backend

```bash
cd backend
python main_unified.py
```

Check console:
```
✅ AWS Rekognition Ready
[PIPELINE] Detected 1 faces
   ✅ MATCHED: Ritika (Similarity: 98.5%)
```

---

## Helpful Commands

### List all registered people
```bash
python manage_faces.py list
```

### Add another person
```bash
python manage_faces.py add photo.jpg PersonName
```

### Test if photo matches
```bash
python manage_faces.py test test_photo.jpg Ritika
```

### Delete a person
```bash
python manage_faces.py delete Ritika
```

---

## Cost Check

**Remember:** You only pay for API calls

```
Ritika detected → $0.002 (detect + recognize)
Ritika not in frame → $0  (no API calls)
System not running → $0
```

**Optimize:**
- Process 1 frame per 2 seconds (0.5 FPS) instead of 30 FPS
- Cost: $86/month → $2.88/month

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Invalid credentials" | Run `aws configure` again |
| "Collection not found" | Run `aws rekognition create-collection --collection-id employees` |
| "Face not detected" | Use clearer photo with face 40x40+ pixels |
| "No match found" | Similarity too high - lower threshold in `aws_recognition.py` line 13 |

---

## When Ready

✅ AWS credentials configured
✅ Collection created  
✅ Ritika's face indexed
✅ Backend updated (optional)
✅ System running

**Now test:** Show Ritika to camera - should see 98%+ accuracy! 🎯
