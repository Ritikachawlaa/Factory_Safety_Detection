# 🔑 .ENV Setup Guide

## What is .env?

A `.env` file stores sensitive credentials (API keys, passwords) locally on your machine. It's NOT uploaded to git, keeping your secrets safe.

---

## Step 1: Edit the .env File

**File:** `backend/.env`

Open it and paste your AWS credentials:

```env
# ========================================
# AWS Credentials (from IAM user)
# ========================================
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=us-east-1

# ========================================
# AWS Rekognition Settings
# ========================================
AWS_REKOGNITION_COLLECTION_ID=employees

# ========================================
# System Configuration
# ========================================
DETECTION_FPS=0.5
SESSION_TIMEOUT=30
FACE_DISTANCE_THRESHOLD=0.85
```

---

## Step 2: Where to Get Your Credentials

### From AWS IAM User

1. Log into **AWS Console**
2. Go to **IAM** → **Users** → **Your User** (e.g., "rekognition-user")
3. Click **Security credentials** tab
4. Find **Access keys** section
5. You have 2 options:
   - **Use existing key:** Copy Access Key ID + Secret Key
   - **Create new key:** Click "Create access key"
     - Copy the CSV file (last chance to get Secret Key!)
     - Contains:
       ```
       Access Key ID,Secret Access Key
       AKIAIOSFODNN7EXAMPLE,wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
       ```

### Format

```env
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

---

## Step 3: Verify Setup

Run this command to test:

```bash
cd backend
python -c "from config.aws_config import AWSConfig; AWSConfig.validate()"
```

**Expected output:**
```
✅ AWS Configuration loaded successfully
   Region: us-east-1
   Collection: employees
   FPS: 0.5
```

**If error:**
```
❌ AWS_ACCESS_KEY_ID not set in .env file
```
→ Check your .env file, copy-paste values again

---

## Step 4: Use in Code

The backend automatically loads .env on startup.

**In `main_unified.py`:**
```python
from services.aws_recognition import AWSRecognizer

# Automatically loads credentials from .env
aws_recognizer = AWSRecognizer()  # Uses AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, etc. from .env
```

**In `cost_optimized_recognition.py`:**
```python
# Also automatically loads from .env
aws_recognizer = AWSRecognizer()
```

---

## ⚠️ Security Best Practices

### What You MUST Do

1. ✅ **Never commit .env to git**
   - `.gitignore` already includes `.env`
   - Verify: `git status` should NOT show `.env`

2. ✅ **Don't share .env file**
   - Don't paste it in chat, email, Slack, etc.
   - Treat like a password

3. ✅ **Keep only 1-2 access keys**
   - Delete old/unused keys from AWS IAM
   - Rotate keys every 6 months

4. ✅ **Check permissions**
   - IAM user should have ONLY `AmazonRekognitionFullAccess`
   - No other permissions needed

### What NOT to Do

```
❌ AWS_ACCESS_KEY_ID=secret_key_here         ← Don't hardcode
❌ export AWS_ACCESS_KEY_ID=...              ← Don't in shell profile
❌ git add .env                               ← Don't commit
❌ Share .env with team                       ← Keep secret
```

---

## Step 5: What to Do If Compromised

If you accidentally:
1. Committed .env to git
2. Shared credentials somewhere
3. Exposed keys on screen

**Immediately:**
```
1. Go to AWS IAM
2. Delete the compromised Access Key
3. Create a new Access Key
4. Update .env with new key
5. Redeploy system
```

This prevents bad actors from using the old key.

---

## Example .env File (SANITIZED)

```env
# AWS Credentials
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=us-east-1

# Rekognition
AWS_REKOGNITION_COLLECTION_ID=employees

# System
DETECTION_FPS=0.5
SESSION_TIMEOUT=30
FACE_DISTANCE_THRESHOLD=0.85

# Database
DATABASE_URL=sqlite:///factory.db

# API
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false

# Logging
LOG_LEVEL=INFO
```

Replace the `EXAMPLE` values with your actual credentials.

---

## Troubleshooting

### Issue: "AWS credentials not found in .env file"

**Cause:** Missing AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY

**Fix:**
1. Open `backend/.env`
2. Check if AWS_ACCESS_KEY_ID line exists
3. Check if AWS_SECRET_ACCESS_KEY line exists
4. If missing, add them
5. Save file
6. Restart backend

### Issue: "Unable to locate credentials"

**Cause:** .env not being read (old code without dotenv)

**Fix:**
```bash
# Update backend code
pip install python-dotenv

# Verify aws_recognition.py has:
# from dotenv import load_dotenv
# load_dotenv()
```

### Issue: "InvalidSignatureException" or "InvalidUserID"

**Cause:** Wrong Access Key ID or Secret Key

**Fix:**
1. Copy credentials EXACTLY from AWS IAM
2. No extra spaces
3. No quotes
4. Check for accidental characters

---

## Quick Summary

| Step | Action | Time |
|------|--------|------|
| 1 | Open `backend/.env` | 1 min |
| 2 | Copy AWS credentials from IAM | 2 min |
| 3 | Paste into .env | 1 min |
| 4 | Run validation command | 1 min |
| 5 | Start backend | 2 min |
| **Total** | **Ready to use** | **7 min** |

---

## You're Set! 🎉

Your backend now:
- ✅ Loads credentials from .env
- ✅ Keeps secrets safe
- ✅ Ready to connect to AWS Rekognition
- ✅ Works with cost-optimized pipeline

**Next:** Start the backend!
```bash
python main_unified.py
```
