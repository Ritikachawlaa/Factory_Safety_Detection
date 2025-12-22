# Frontend API Integration - Quick Test Guide

## 5-Minute Setup & Test

### Step 1: Install Dependencies (2 minutes)
```bash
cd Frontend_Safety_Detection/frontend
npm install
```

### Step 2: Start Backend (1 minute)
In another terminal:
```bash
cd Factory_Safety_Detection/backend
python main_unified.py
```
Wait for: `Uvicorn running on http://127.0.0.1:8000`

### Step 3: Start Frontend (1 minute)
```bash
npm run dev
```
Frontend runs on: `http://localhost:5173`

### Step 4: Test Connectivity (1 minute)
Open browser console (F12) and run:
```javascript
fetch('http://localhost:8000/api/health')
  .then(r => r.json())
  .then(d => console.log(d))
```
Should see status: "healthy"

---

## Module-by-Module Testing

### ✅ Module 1: Person Identity (Face Recognition)
1. Go to "Person Identity" module
2. Click "📤 Upload Face Image"
3. Select any JPG/PNG image with a face
4. Check results:
   - ✅ "Faces Detected" counter increases
   - ✅ "Total Recognized" shows detected faces
   - ✅ Processing time shows in milliseconds
   - ✅ Module status shows "✓ Active"

**Test Enrollment:**
1. Click "Toggle Enrollment Mode"
2. Enter Employee ID: `EMP001`
3. Enter Name: `John Doe`
4. Upload an image
5. Check: "Enrollment successful" message

---

### ✅ Module 2: Vehicle Management
1. Go to "Vehicle & Gate Management" module
2. Check stats grid:
   - ✅ "Vehicles Detected" shows number > 0
   - ✅ "Plates Read" shows recognized plates
   - ✅ Processing time displays
   - ✅ Module status shows "✓ Active"
3. Scroll down to table
4. Check vehicle data is displayed with:
   - ✅ License plates
   - ✅ Vehicle type (car/truck icons)
   - ✅ Confidence percentage
   - ✅ Detection timestamp

---

### ✅ Module 3: Attendance
1. Go to "Attendance & Workforce" module
2. Check stats grid:
   - ✅ "Present Today" count displays
   - ✅ "Late Arrivals" shows number
   - ✅ "Early Exits" count visible
   - ✅ "Absent" count shows
3. Scroll down to attendance table
4. Check table shows:
   - ✅ Employee names
   - ✅ Departments
   - ✅ Check-in times
   - ✅ Status badges (Present/Late/Absent)

---

### ✅ Module 4: People Counting
1. Go to "People Counting & Occupancy" module
2. Check stats grid:
   - ✅ "Current Occupancy" shows number
   - ✅ "Total Entries" increments
   - ✅ "Total Exits" increments
   - ✅ Module status shows "✓ Active"
3. Check zone cards:
   - ✅ Zone names display
   - ✅ Occupancy progress bars show
   - ✅ Entry/exit icons and counts visible
4. Check table for:
   - ✅ Zone-wise occupancy data
   - ✅ Capacity usage percentages

---

### ✅ Module 5: Crowd Density
1. Go to "Crowd Density & Overcrowding" module
2. Check stats grid:
   - ✅ "Critical Zones" count
   - ✅ "High Density" zones
   - ✅ "Zones Monitored" total
   - ✅ Module status
3. Check alert table:
   - ✅ Zone names
   - ✅ Density levels (critical/high/medium/low)
   - ✅ Density percentages
   - ✅ Status badges (Alert/Monitoring/Normal)

---

## Data Refresh Verification

All modules refresh data every 5 seconds:

1. Open browser DevTools (F12)
2. Go to "Network" tab
3. Watch for API calls to:
   - `/api/diagnostic`
   - `/api/vehicle-logs`
   - `/api/occupancy-logs`
   - `/api/attendance-records`
4. Should see requests every 5 seconds
5. Check "Response" tab for JSON data

---

## Troubleshooting

### Frontend won't start
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Backend connection error
```
Error: Failed to fetch from http://localhost:8000
```
**Fix:** Make sure backend is running:
```bash
cd backend
python main_unified.py
```

### API returns 404
```
GET /api/health 404
```
**Fix:** Check backend URL in `.env.local`:
```env
VITE_API_URL=http://localhost:8000
VITE_API_BASE=/api
```

### Module shows "Module Status: ● Offline"
- Backend health check failed
- Verify backend is running
- Check console for error messages
- Backend may need restart

### No data in tables
- Wait 5 seconds for first data refresh
- Check browser console (F12) for errors
- Verify API endpoints are working
- Backend may need test data

---

## Performance Check

### Frontend Bundle
```bash
npm run build
# Check console output for bundle size
```
Expected: ~250KB (gzipped)

### API Response Time
Open DevTools → Network tab → Pick any API request
- Time to first byte (TTFB): ~100-200ms
- Content download: ~50-100ms
- Total: ~150-300ms

### Module Load Time
From page visit to first data visible:
- Expected: ~500ms - 1 second
- Includes: React render + API call + data population

---

## Verification Checklist

Before considering integration complete, verify:

- [ ] npm install completes without errors
- [ ] npm run dev starts on port 5173
- [ ] Backend runs on http://localhost:8000
- [ ] Health check API returns {"status": "healthy"}
- [ ] Module 1 accepts image upload and shows results
- [ ] Module 2 displays vehicle detection data
- [ ] Module 3 shows attendance records
- [ ] Module 4 shows occupancy counts
- [ ] Module 5 shows crowd density alerts
- [ ] All tables populate with real data
- [ ] Stats grids show non-zero values
- [ ] Data refreshes every 5 seconds
- [ ] No red error messages in UI
- [ ] Browser console has no errors
- [ ] All modules have status "✓ Active"

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| "ERR_INTERNET_DISCONNECTED" | Backend not running on port 8000 |
| Module status shows "● Offline" | Check backend health: `curl localhost:8000/api/health` |
| Tables are empty | Wait 5 seconds for first refresh, then F5 to reload |
| Images not uploading | Check file size < 5MB, format is JPG/PNG |
| Module metrics show 0 | Backend may not have processed any frames yet |
| Page loads slowly | Check network tab, look for slow API responses |

---

## Success Indicators

✅ **Module pages load** (< 2 seconds)
✅ **Data populates** (< 5 seconds)
✅ **Stats show real numbers** (not zero/hardcoded)
✅ **Tables display actual data** (not empty)
✅ **No red error messages** (in UI)
✅ **Console has no errors** (F12)
✅ **Data refreshes** (every 5 seconds)
✅ **API calls visible** (Network tab)

---

## Next Steps After Verification

1. **Run full test suite** (if available)
2. **Check backend logs** for any warnings
3. **Test with real camera feed** (if available)
4. **Performance testing** with DevTools
5. **Cross-browser testing** (Chrome, Edge, Firefox)
6. **Mobile responsiveness** (check on phone)
7. **Prepare for deployment** (build dist folder)

---

## Files Modified

- ✅ `frontend/src/hooks/useFactorySafetyAPI.ts` - API hook
- ✅ `frontend/.env.local` - API configuration
- ✅ `frontend/src/pages/PersonIdentityModule.tsx` - Module 1
- ✅ `frontend/src/pages/VehicleManagementModule.tsx` - Module 2
- ✅ `frontend/src/pages/AttendanceModule.tsx` - Module 3
- ✅ `frontend/src/pages/PeopleCountingModule.tsx` - Module 4
- ✅ `frontend/src/pages/CrowdDensityModule.tsx` - Module 5

---

**Ready to test! Follow the 5-minute setup above.** 🚀
