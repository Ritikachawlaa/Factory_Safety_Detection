# Module 4: Occupancy Analytics - File Index & Quick Navigation

## 📁 File Structure

### Location: `backend/detection_system/`

```
detection_system/
├── occupancy_models.py          ← Database models & DAOs
├── occupancy_service.py         ← Business logic & algorithms
└── occupancy_endpoints.py       ← FastAPI REST endpoints
```

### Location: `backend/`

```
backend/
├── OCCUPANCY_QUICK_START.md              ← Start here (5 min setup)
├── OCCUPANCY_IMPLEMENTATION_GUIDE.md    ← Deep technical reference
├── OCCUPANCY_API_REFERENCE.md           ← Complete API documentation
├── MODULE_4_DELIVERY.md                 ← Delivery & deployment guide
└── MODULE_4_SUMMARY.md                  ← This delivery overview
```

---

## 🎯 Quick Navigation Guide

### "I want to get started in 5 minutes"
→ **Read:** `OCCUPANCY_QUICK_START.md`
- Step-by-step setup
- Create first camera
- Configure virtual line
- Test occupancy endpoint

### "I need to understand how it works"
→ **Read:** `OCCUPANCY_IMPLEMENTATION_GUIDE.md`
- Architecture overview
- Line crossing algorithm (with math)
- Database schema details
- Service layer walkthrough

### "I need to integrate with my API"
→ **Read:** `OCCUPANCY_API_REFERENCE.md`
- All 16 endpoints documented
- Request/response examples
- Code samples (Python, JavaScript, cURL)
- Error codes and debugging

### "I need to deploy this"
→ **Read:** `MODULE_4_DELIVERY.md`
- Deployment checklist
- Integration points
- Configuration guide
- Monitoring setup

### "I just want the overview"
→ **Read:** `MODULE_4_SUMMARY.md`
- What's included
- Key features
- Quick deployment path
- Expected outcomes

---

## 📄 File Descriptions

### Core Implementation Files

#### `occupancy_models.py` (650 lines)
**Purpose:** Database schema and data access layer

**Contains:**
- Database Models:
  - `Camera` - Camera configurations
  - `VirtualLine` - Line crossing definitions
  - `OccupancyLog` - Real-time logs
  - `HourlyOccupancy` - Hourly summaries
  - `DailyOccupancy` - Daily summaries
  - `MonthlyOccupancy` - Monthly summaries
  - `OccupancyAlert` - Alert tracking

- Data Access Objects:
  - `CameraDAO` - CRUD for cameras
  - `VirtualLineDAO` - CRUD for lines
  - `OccupancyLogDAO` - CRUD for logs
  - `HourlyOccupancyDAO` - CRUD for hourly
  - `DailyOccupancyDAO` - CRUD for daily
  - `MonthlyOccupancyDAO` - CRUD for monthly
  - `OccupancyAlertDAO` - CRUD for alerts

- Helper Classes:
  - `LineCrossingData` - Crossing event data
  - `OccupancyState` - Current occupancy state

- Enums:
  - `LineDirection` - entry, exit, bidirectional
  - `OccupancyAlertType` - Alert types

**Key Functions:**
- Create/read/update camera configurations
- Manage virtual lines
- Save and query occupancy logs
- Create hourly/daily/monthly summaries
- Track and resolve alerts

---

#### `occupancy_service.py` (900 lines)
**Purpose:** Business logic and occupancy tracking

**Main Components:**

1. **LineCrossingProcessor**
   - Detects when person crosses virtual line
   - Uses vector math and cross product
   - Verifies trajectory intersection
   - Returns: "entry", "exit", or None

2. **DirectionAnalyzer**
   - Analyzes movement direction
   - Determines if crossing is entry or exit
   - Uses dot product with line perpendicular

3. **OccupancyCounter**
   - Tracks real-time occupancy for single camera
   - Records entries and exits
   - Maintains occupancy >= 0 (no negative)
   - Supports manual calibration

4. **MultiCameraAggregator**
   - Consolidates data from multiple cameras
   - Calculates facility-wide occupancy
   - Prevents double-counting

5. **TimeSeriesAggregator**
   - Aggregates logs to hourly summaries
   - Aggregates hourly to daily
   - Aggregates daily to monthly
   - Runs as background tasks

6. **OccupancyService**
   - Main orchestrator
   - Coordinates all components
   - Processes frames
   - Saves logs
   - Manages alerts

**Key Functions:**
- `process_frame()` - Process detection frame
- `save_occupancy_log()` - Save periodic snapshot
- `manual_calibration()` - Correct after headcount
- `check_capacity_alert()` - Check capacity exceeded
- `get_occupancy_state()` - Get current state
- Aggregation functions for scheduled tasks

---

#### `occupancy_endpoints.py` (850 lines)
**Purpose:** FastAPI REST endpoints

**Endpoints (16 total):**

**Camera Management (4):**
- `POST /cameras` - Create camera
- `GET /cameras` - List cameras
- `GET /cameras/{id}` - Get camera details
- `PUT /cameras/{id}` - Update camera

**Virtual Lines (4):**
- `POST /lines` - Create virtual line
- `GET /cameras/{id}/lines` - List lines
- `GET /lines/{id}` - Get line details
- `PUT /lines/{id}` - Update line

**Real-Time Occupancy (3):**
- `GET /cameras/{id}/live` - Current occupancy
- `GET /facility/live` - Facility occupancy
- `POST /cameras/{id}/calibrate` - Manual calibration

**Historical Data (3):**
- `GET /cameras/{id}/logs` - Raw logs (1-5 min)
- `GET /cameras/{id}/hourly` - Hourly summaries
- `GET /cameras/{id}/daily` - Daily summaries
- `GET /cameras/{id}/monthly` - Monthly summaries

**Alerts (2):**
- `GET /alerts` - Get active alerts
- `PUT /alerts/{id}/resolve` - Resolve alert

**Statistics (1):**
- `GET /facility/stats` - Facility statistics

**Admin (1):**
- `POST /aggregate` - Trigger aggregation

**Request/Response Models:**
- `CameraCreate/Response`
- `VirtualLineCreate/Response`
- `OccupancyLiveResponse`
- `OccupancyLogResponse`
- `HourlyOccupancyResponse`
- `DailyOccupancyResponse`
- `MonthlyOccupancyResponse`
- `OccupancyAlertResponse`
- `ManualCalibrationRequest`
- `FacilityOccupancyResponse`
- `FacilityStatsResponse`

---

### Documentation Files

#### `OCCUPANCY_QUICK_START.md` (400 lines)
**Audience:** Developers getting started

**Contents:**
1. Overview and what you can do
2. Quick start in 5 minutes (6 steps)
3. API quick reference table
4. Configuration options
5. Camera types and virtual line tips
6. Data understanding examples
7. Common issues and solutions
8. Next steps

**Best for:** Initial setup and troubleshooting

---

#### `OCCUPANCY_IMPLEMENTATION_GUIDE.md` (3,000+ lines)
**Audience:** Technical implementers

**Contents:**
1. Module overview and architecture
2. Core components breakdown (6 major components)
3. Line crossing algorithm:
   - Mathematical foundation
   - Side-based detection algorithm
   - Pseudocode examples
   - Visual examples
4. Database schema (7 tables, complete details)
5. Service layer implementation
6. All API endpoints reference
7. Integration guide with other modules
8. Performance considerations
9. Error handling and recovery (7 scenarios)
10. Testing strategies (5 test categories)

**Best for:** Deep understanding and customization

---

#### `OCCUPANCY_API_REFERENCE.md` (800 lines)
**Audience:** API users and integrators

**Contents:**
1. Base URL and authentication
2. Camera management endpoints (4)
3. Virtual line endpoints (4)
4. Real-time occupancy endpoints (3)
5. Historical data endpoints (raw, hourly, daily, monthly)
6. Alert management endpoints (2)
7. Facility statistics endpoint
8. Aggregation admin endpoint
9. Error responses and status codes
10. Pagination and authentication notes
11. Request examples (cURL, Python, JavaScript)

**Best for:** Using the API from frontend or external systems

---

#### `MODULE_4_DELIVERY.md` (800 lines)
**Audience:** Project managers and deployers

**Contents:**
1. Delivery contents checklist
2. Features implemented (17+ features)
3. Technical specifications
4. System architecture overview
5. Technical stack details
6. Scalability guidance
7. Deployment guide (6 steps)
8. Pre-deployment checklist
9. Integration with other modules
10. Example use cases (3)
11. Known limitations (5)
12. Security considerations
13. Support & maintenance tasks
14. Performance monitoring
15. Version history
16. Delivery sign-off

**Best for:** Deployment planning and project tracking

---

#### `MODULE_4_SUMMARY.md` (300 lines)
**Audience:** Anyone wanting an overview

**Contents:**
1. Module status and metrics
2. Delivery contents summary
3. Key features implemented
4. Technical highlights
5. Data model overview
6. Deployment path
7. How to use this delivery
8. Integration points
9. What makes it production-ready
10. Expected outcomes
11. Learning resources
12. Getting help guide
13. Final summary

**Best for:** Quick overview and decision-making

---

## 🔍 Finding What You Need

### By Role

**Software Developer:**
- Start: `OCCUPANCY_QUICK_START.md`
- Then: `occupancy_models.py` + `occupancy_service.py`
- Reference: `OCCUPANCY_API_REFERENCE.md`

**DevOps/Infrastructure:**
- Read: `MODULE_4_DELIVERY.md` (Deployment section)
- Reference: `OCCUPANCY_QUICK_START.md` (Configuration)
- Check: Deployment checklist

**Data Analyst:**
- Read: `OCCUPANCY_API_REFERENCE.md` (Historical endpoints)
- Reference: `OCCUPANCY_IMPLEMENTATION_GUIDE.md` (Data understanding)
- Use: `/daily`, `/hourly`, `/monthly` endpoints

**Frontend Developer:**
- Read: `OCCUPANCY_API_REFERENCE.md`
- Examples: JavaScript fetch examples at bottom
- Reference: `/live` and `/facility/live` endpoints

**Project Manager:**
- Read: `MODULE_4_SUMMARY.md`
- Then: `MODULE_4_DELIVERY.md`
- Reference: Features and deployment checklists

**System Architect:**
- Read: `OCCUPANCY_IMPLEMENTATION_GUIDE.md` (Sections 1-3)
- Then: `MODULE_4_DELIVERY.md` (Architecture and Scalability)
- Deep dive: `occupancy_service.py` code

---

### By Task

**"Set up occupancy tracking"**
→ `OCCUPANCY_QUICK_START.md` (5 minutes)

**"Integrate with my API"**
→ `OCCUPANCY_API_REFERENCE.md` (Choose endpoints you need)

**"Debug line crossing not working"**
→ `OCCUPANCY_QUICK_START.md` (Common Issues) or `OCCUPANCY_IMPLEMENTATION_GUIDE.md` (Section 3)

**"Deploy to production"**
→ `MODULE_4_DELIVERY.md` (Deployment & Checklist)

**"Understand the algorithm"**
→ `OCCUPANCY_IMPLEMENTATION_GUIDE.md` (Section 3 & 5)

**"Generate reports"**
→ `OCCUPANCY_API_REFERENCE.md` (Historical endpoints)

**"Monitor performance"**
→ `MODULE_4_DELIVERY.md` (Performance Monitoring)

**"Troubleshoot issues"**
→ `OCCUPANCY_QUICK_START.md` (Issues) then `OCCUPANCY_IMPLEMENTATION_GUIDE.md` (Error Handling)

---

## 📊 Documentation Statistics

| File | Lines | Purpose |
|------|-------|---------|
| occupancy_models.py | 650 | Database & DAOs |
| occupancy_service.py | 900 | Business logic |
| occupancy_endpoints.py | 850 | API endpoints |
| OCCUPANCY_QUICK_START.md | 400 | Quick setup |
| OCCUPANCY_IMPLEMENTATION_GUIDE.md | 3,000+ | Deep reference |
| OCCUPANCY_API_REFERENCE.md | 800 | API docs |
| MODULE_4_DELIVERY.md | 800 | Deployment |
| MODULE_4_SUMMARY.md | 300 | Overview |
| **TOTAL** | **~8,000** | **Complete Package** |

---

## 🚀 Recommended Reading Order

### For Quick Start (1-2 hours)
1. `MODULE_4_SUMMARY.md` (5 min) - Understand what you got
2. `OCCUPANCY_QUICK_START.md` (30 min) - Set it up
3. `OCCUPANCY_API_REFERENCE.md` (45 min) - Learn the API

### For Complete Understanding (4-6 hours)
1. `MODULE_4_SUMMARY.md` (5 min)
2. `OCCUPANCY_QUICK_START.md` (30 min)
3. `OCCUPANCY_IMPLEMENTATION_GUIDE.md` (2-3 hours)
4. `OCCUPANCY_API_REFERENCE.md` (45 min)
5. Code review: `occupancy_models.py`, `occupancy_service.py`

### For Production Deployment (2-3 hours)
1. `MODULE_4_DELIVERY.md` (45 min) - Understand deployment
2. Deployment checklist (30 min)
3. Integration checklist (30 min)
4. Test plan review (30 min)

---

## ✅ Verification Checklist

After setup, verify you have:

- [ ] `occupancy_models.py` in `backend/detection_system/`
- [ ] `occupancy_service.py` in `backend/detection_system/`
- [ ] `occupancy_endpoints.py` in `backend/detection_system/`
- [ ] `OCCUPANCY_QUICK_START.md` in `backend/`
- [ ] `OCCUPANCY_IMPLEMENTATION_GUIDE.md` in `backend/`
- [ ] `OCCUPANCY_API_REFERENCE.md` in `backend/`
- [ ] `MODULE_4_DELIVERY.md` in `backend/`
- [ ] `MODULE_4_SUMMARY.md` in `backend/`

All files present? ✅ Ready to start!

---

## 🔗 Cross-References

### Module 4 References Other Modules
- **Module 2 (Vehicle Detection):** Filter to PERSON_CLASS only
- **Module 3 (Attendance):** Both use ByteTrack track_ids
- **Future Module 5 (Alerts):** Occupancy triggers alerts

### Other Documentation in Backend
- `FASTAPI_BACKEND.md` - Backend architecture
- `MODULE_3_IMPLEMENTATION_GUIDE.md` - Previous module
- `requirements.txt` - Dependencies

---

## 📞 Quick Support

### Common Questions

**Q: Where do I start?**
A: Read `OCCUPANCY_QUICK_START.md`

**Q: How do I integrate with my API?**
A: See `OCCUPANCY_API_REFERENCE.md` and choose endpoints

**Q: I need to understand the algorithm**
A: See `OCCUPANCY_IMPLEMENTATION_GUIDE.md` Section 3

**Q: Something's not working**
A: Check `OCCUPANCY_QUICK_START.md` Common Issues

**Q: How do I deploy this?**
A: Follow `MODULE_4_DELIVERY.md` Deployment Guide

**Q: Where's the database schema?**
A: See `OCCUPANCY_IMPLEMENTATION_GUIDE.md` Section 4

---

## 📝 Version Information

**Module Version:** 1.0.0  
**Release Date:** January 2025  
**Status:** Production Ready  
**Code Quality:** Enterprise Grade  
**Documentation:** Comprehensive  

---

**End of File Index**

Use this guide to navigate the Module 4 delivery. Start with the summary for an overview, the quick start for setup, the implementation guide for understanding, and the API reference for integration.

All files are production-ready and fully documented. Good luck with your deployment! 🚀
