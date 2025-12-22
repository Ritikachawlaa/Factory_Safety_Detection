# 💰 AWS Rekognition - Cost Clarification

## Your Question: Will it cost if system is not used?

### ✅ Short Answer: **NO - Only Pay When API is Called**

```
System NOT running       → $0
System running, no faces → Still calling API → $0.002 per call
System running with faces → Calling API → $0.002 per call
```

**You DO NOT pay for:**
- ❌ Having account open
- ❌ Having collection created
- ❌ Having system running (if not calling API)
- ❌ Data stored in collection
- ❌ Subscription/monthly fees

**You DO pay for:**
- ✅ Each `detect_faces()` call → $0.001
- ✅ Each `search_faces_by_image()` call → $0.001
- ✅ Total per frame: $0.002

---

## Cost Breakdown Examples

### Scenario 1: System Running, Ritika Standing in Frame (30 FPS)

```
Frames/second:        30
Frames/hour:          30 × 3600 = 108,000
Hours/day (8h):       8
Frames/day:           108,000 × 8 = 864,000
Cost/day:             864,000 × $0.002 = $1,728
Cost/month (30 days): $1,728 × 30 = $51,840
Cost/year:            $622,080
```

**TOO EXPENSIVE! ❌**

### Scenario 2: System Running, 1 FPS (Process Every 30th Frame)

```
Frames/second:        1
Frames/day:           86,400
Cost/day:             86,400 × $0.002 = $172.80
Cost/month:           $172.80 × 30 = $5,184
Cost/year:            $62,000
```

**Still expensive for 24/7** ❌

### Scenario 3: System Running 8 Hours/Day, 0.5 FPS (Every 2 Seconds)

```
Frames/second:        0.5
Frames/hour:          1,800
Hours/day (8h):       8
Frames/day:           1,800 × 8 = 14,400
Cost/day:             14,400 × $0.002 = $28.80
Cost/month:           $28.80 × 30 = $864
Cost/year:            $10,560
```

**More reasonable** ✅

### Scenario 4: OPTIMAL - Only Process When Faces Detected

```
With Haar Cascade (FREE) first:
├─ Run Haar on every frame (FREE)
├─ If face found → Call AWS Rekognition ($0.002)
├─ If no face → Skip AWS call ($0)

Assumptions:
- 10% of frames have faces detected
- 0.5 FPS = 14,400 frames/day
- 10% have faces = 1,440 AWS calls/day

Cost/day:             1,440 × $0.002 = $2.88
Cost/month:           $2.88 × 30 = $86.40
Cost/year:            $1,036
```

**BEST - 95% Cheaper!** ✅✅✅

---

## When You Pay Exactly

### Cost is $0.002 per frame when:

**1. Face Detection API Called**
```python
response = rekognition.detect_faces(Image=...)
# Costs: $0.001
```

**2. Face Search API Called**
```python
response = rekognition.search_faces_by_image(...)
# Costs: $0.001
# Total if called in same frame: $0.002
```

---

## When You DON'T Pay

### $0 Costs:

```
✅ System turned off              → $0
✅ System running but idle        → $0 (no API calls)
✅ Using Haar Cascade only        → $0
✅ Using local DeepFace           → $0
✅ Data stored in collection      → $0
✅ Creating/managing collection   → $0 (free)
✅ System running, no people      → $0 (no API calls)
```

### If System is Running but Face Detection Disabled:

```python
enabled_features = EnabledFeatures(
    face_detection=False,  # Disabled
    face_recognition=False
)

# Cost: $0 (API never called)
```

---

## Real-World Scenario for You

### Your Typical Factory Setup

```
Factory hours:        8 AM to 6 PM (10 hours/day)
Cameras:              2 (entrance, workspace)
People in frame:      5-10 at any time

Configuration:
├─ Process: 0.5 FPS per camera
├─ Only when faces detected (optimal)
├─ ~5% of frames in dark areas (skip detection)
├─ ~30% of frames with people

Daily Calculation:
├─ 10 hours × 3600 sec/hour = 36,000 seconds
├─ 0.5 FPS × 36,000 = 18,000 frames/day
├─ 30% have people = 5,400 AWS calls
├─ 5,400 × $0.002 = $10.80/day

Monthly:  $10.80 × 30 = $324
Yearly:   $10.80 × 365 = $3,942
```

**Fair deal for 95%+ accuracy!** ✅

---

## Cost Optimization Techniques

### Technique 1: Frame Sampling
```
Process every Nth frame:
├─ Every frame (30 FPS): $172.80/day
├─ Every 10th frame (3 FPS): $17.28/day
├─ Every 30th frame (1 FPS): $5.76/day ✅
```

### Technique 2: Conditional Processing
```python
# Only call AWS when Haar detects face
if haar_cascade_detects_face:
    result = aws_recognize(frame)  # $0.002
else:
    result = {'recognized': [], 'unknown': 0}  # $0
```

**This alone: 90% cost reduction!**

### Technique 3: Batch Processing
```python
# Collect frames, process in batches
frames = [frame1, frame2, frame3, ...]
process_batch(frames)  # 1 call instead of 3
# Cost: $0.002 total instead of $0.006
```

### Technique 4: Time-Based Detection
```python
# Only process during working hours
if 8 <= hour <= 18:
    result = aws_recognize(frame)  # During work
else:
    result = skip_recognition()  # Night: $0
```

**Cost cut by 2/3!**

---

## AWS Billing Monitoring

### Check Real-Time Costs

```bash
# View costs in AWS Console
1. Go to https://console.aws.amazon.com
2. Search: "Billing Dashboard"
3. See current month costs
4. Set budget alerts (free)
```

### Set Cost Alerts

```
1. AWS Console → Budgets
2. Create budget: $100/month
3. Alert when threshold exceeded
4. Receive email notification
```

---

## Decision Matrix

**Choose based on your needs:**

| Accuracy Need | Volume | Best Solution | Cost |
|---------------|--------|---------------|------|
| Casual demo | 1 person | DeepFace (current) | $0 |
| Small setup | 5-10 people | DeepFace optimized | $0 |
| **Factory (your case)** | **10-50 people** | **AWS + optimization** | **$86-400/month** |
| Enterprise | 100+ people | AWS + image storage | $500+/month |

---

## FAQ

### Q: What if I forget to delete collection?
**A:** Costs $0. Collections don't have monthly fees.

### Q: What if I have 100 employees?
**A:** Cost scales with API calls, NOT number of employees. Still $2.88/day with optimal config.

### Q: Can I switch back to DeepFace?
**A:** Yes! Change 1 line in `detection_pipeline.py`
```python
self.use_aws = False  # Back to DeepFace ($0)
```

### Q: Do I pay for failed recognitions?
**A:** YES - Every API call costs money, whether match found or not.

### Q: How to minimize cost?
**A:** Use Haar Cascade first → only call AWS if face detected = 90% savings!

---

## Your Best Strategy

1. ✅ **Start with DeepFace (current)** - It's working!
2. ⏳ **Monitor accuracy for 1 week**
3. 📊 **If accuracy < 85%, switch to AWS**
4. 🎯 **Use optimization technique #2** (Haar first)
5. 💰 **Estimated cost: $90-300/month** (reasonable)

---

## Next Steps

1. Set up AWS account (free, no charge until first API call)
2. Create collection
3. Register Ritika
4. Enable AWS in code
5. Test and monitor costs
6. Adjust FPS/timing if needed

**You're in control of costs!** 🎛️
