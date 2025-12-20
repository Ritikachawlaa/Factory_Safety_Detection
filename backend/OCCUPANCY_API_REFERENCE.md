# Module 4: Occupancy Analytics - API Reference

## Base URL
```
http://localhost:8000/api/occupancy
```

---

## 📹 Camera Management

### Create Camera
**POST** `/cameras`

Create a new camera for occupancy tracking.

**Request Body:**
```json
{
  "camera_id": "GATE_A",
  "camera_name": "Gate A Entrance",
  "location": "Main Gate",
  "camera_type": "entry_only",
  "max_occupancy": 100,
  "resolution_width": 1920,
  "resolution_height": 1080
}
```

**Response:** 201 Created
```json
{
  "id": 1,
  "camera_id": "GATE_A",
  "camera_name": "Gate A Entrance",
  "location": "Main Gate",
  "camera_type": "entry_only",
  "is_active": true,
  "max_occupancy": 100
}
```

**Error Responses:**
- `400 Bad Request` - Invalid input
- `409 Conflict` - Camera ID already exists

---

### Get All Cameras
**GET** `/cameras`

List all active cameras.

**Response:** 200 OK
```json
[
  {
    "id": 1,
    "camera_id": "GATE_A",
    "camera_name": "Gate A Entrance",
    "location": "Main Gate",
    "camera_type": "entry_only",
    "is_active": true,
    "max_occupancy": 100
  }
]
```

---

### Get Camera Details
**GET** `/cameras/{camera_id}`

Get details for a specific camera.

**Path Parameters:**
- `camera_id` (int, required) - Database ID of camera

**Response:** 200 OK
```json
{
  "id": 1,
  "camera_id": "GATE_A",
  "camera_name": "Gate A Entrance",
  ...
}
```

**Error Responses:**
- `404 Not Found` - Camera not found

---

### Update Camera
**PUT** `/cameras/{camera_id}`

Update camera configuration.

**Path Parameters:**
- `camera_id` (int, required)

**Request Body:**
```json
{
  "camera_name": "Gate A Main Entrance",
  "max_occupancy": 120
}
```

**Response:** 200 OK
```json
{
  "id": 1,
  "camera_name": "Gate A Main Entrance",
  "max_occupancy": 120,
  ...
}
```

---

## 📍 Virtual Line Management

### Create Virtual Line
**POST** `/lines`

Create a virtual line for detecting entries/exits.

**Request Body:**
```json
{
  "camera_id": 1,
  "line_name": "Entrance A",
  "x1": 0,
  "y1": 300,
  "x2": 1920,
  "y2": 300,
  "direction": "entry",
  "confidence_threshold": 0.5
}
```

**Parameters:**
- `x1, y1, x2, y2` - Line endpoints in pixel coordinates
- `direction` - "entry", "exit", or "bidirectional"
- `confidence_threshold` - Minimum confidence (0-1) for detecting crossings

**Response:** 201 Created
```json
{
  "id": 1,
  "camera_id": 1,
  "line_name": "Entrance A",
  "x1": 0,
  "y1": 300,
  "x2": 1920,
  "y2": 300,
  "direction": "entry",
  "is_active": true,
  "created_at": "2025-01-15T10:00:00Z"
}
```

---

### Get Camera Lines
**GET** `/cameras/{camera_id}/lines`

Get all virtual lines configured for a camera.

**Path Parameters:**
- `camera_id` (int, required)

**Response:** 200 OK
```json
[
  {
    "id": 1,
    "camera_id": 1,
    "line_name": "Entrance A",
    "x1": 0,
    "y1": 300,
    "x2": 1920,
    "y2": 300,
    "direction": "entry",
    "is_active": true
  }
]
```

---

### Get Virtual Line Details
**GET** `/lines/{line_id}`

Get details for a specific virtual line.

**Path Parameters:**
- `line_id` (int, required)

**Response:** 200 OK
```json
{
  "id": 1,
  "camera_id": 1,
  "line_name": "Entrance A",
  ...
}
```

---

### Update Virtual Line
**PUT** `/lines/{line_id}`

Update virtual line configuration.

**Request Body:**
```json
{
  "confidence_threshold": 0.6
}
```

**Response:** 200 OK
```json
{
  "id": 1,
  "confidence_threshold": 0.6,
  ...
}
```

---

## 👥 Real-Time Occupancy

### Get Live Occupancy
**GET** `/cameras/{camera_id}/live`

Get current occupancy for a camera.

**Path Parameters:**
- `camera_id` (int, required)

**Response:** 200 OK
```json
{
  "camera_id": 1,
  "current_occupancy": 45,
  "total_entries": 1234,
  "total_exits": 1189,
  "unique_persons": 45,
  "last_updated": "2025-01-15T10:30:45Z"
}
```

**Field Descriptions:**
- `current_occupancy` - Number of people currently in area (entries - exits)
- `total_entries` - Cumulative count since service start
- `total_exits` - Cumulative count since service start
- `unique_persons` - Number of unique tracked individuals
- `last_updated` - Last time occupancy was updated

---

### Get Facility Occupancy
**GET** `/facility/live`

Get facility-wide occupancy (sum of all cameras).

**Response:** 200 OK
```json
{
  "facility_occupancy": 450,
  "total_entries_all_cameras": 12340,
  "total_exits_all_cameras": 11890,
  "cameras_active": 3,
  "last_updated": "2025-01-15T10:30:45Z"
}
```

---

### Manually Calibrate Occupancy
**POST** `/cameras/{camera_id}/calibrate`

Set occupancy to a specific value (used after manual headcount).

**Path Parameters:**
- `camera_id` (int, required)

**Request Body:**
```json
{
  "occupancy_value": 50,
  "notes": "Manual headcount performed at 10:30"
}
```

**Response:** 200 OK
```json
{
  "status": "success",
  "camera_id": 1,
  "occupancy_set_to": 50,
  "timestamp": "2025-01-15T10:31:00Z"
}
```

**Notes:**
- Use when detected count is inaccurate
- Creates a log entry with `is_manual_calibration = true`
- Useful for error correction

---

## 📊 Historical Data - Raw Logs

### Get Occupancy Logs
**GET** `/cameras/{camera_id}/logs`

Get recent occupancy logs (1-5 minute periods).

**Path Parameters:**
- `camera_id` (int, required)

**Query Parameters:**
- `hours` (int, default: 24) - Last N hours to retrieve

**Example Request:**
```
GET /cameras/1/logs?hours=24
```

**Response:** 200 OK
```json
[
  {
    "id": 1001,
    "camera_id": 1,
    "entry_count": 5,
    "exit_count": 2,
    "net_occupancy": 45,
    "timestamp": "2025-01-15T10:00:00Z",
    "tracked_persons": 45
  },
  {
    "id": 1002,
    "camera_id": 1,
    "entry_count": 3,
    "exit_count": 4,
    "net_occupancy": 44,
    "timestamp": "2025-01-15T10:05:00Z",
    "tracked_persons": 44
  }
]
```

**Field Descriptions:**
- `entry_count` - People entering in this period
- `exit_count` - People exiting in this period
- `net_occupancy` - Current occupancy at end of period
- `tracked_persons` - Unique people tracked in period

**Typical Use Cases:**
- Minute-by-minute occupancy tracking
- Detecting rapid fluctuations
- Troubleshooting detection issues

---

## 📈 Historical Data - Hourly

### Get Hourly Occupancy
**GET** `/cameras/{camera_id}/hourly`

Get hourly aggregated occupancy data.

**Path Parameters:**
- `camera_id` (int, required)

**Query Parameters:**
- `days` (int, default: 7) - Last N days of data

**Example Request:**
```
GET /cameras/1/hourly?days=7
```

**Response:** 200 OK
```json
[
  {
    "hour": "2025-01-15 10:00",
    "camera_id": 1,
    "entries": 15,
    "exits": 8,
    "avg_occupancy": 47.5,
    "peak_occupancy": 52,
    "unique_persons": 22
  },
  {
    "hour": "2025-01-15 11:00",
    "camera_id": 1,
    "entries": 12,
    "exits": 14,
    "avg_occupancy": 45.8,
    "peak_occupancy": 50,
    "unique_persons": 18
  }
]
```

**Field Descriptions:**
- `entries` - Total people entered in hour
- `exits` - Total people exited in hour
- `avg_occupancy` - Average occupancy during hour
- `peak_occupancy` - Maximum occupancy in hour
- `unique_persons` - Number of unique individuals

**Typical Use Cases:**
- Hourly trend analysis
- Peak time identification
- Dashboard displays

---

## 📉 Historical Data - Daily

### Get Daily Occupancy
**GET** `/cameras/{camera_id}/daily`

Get daily aggregated occupancy data.

**Path Parameters:**
- `camera_id` (int, required)

**Query Parameters:**
- `days` (int, default: 30) - Last N days of data

**Example Request:**
```
GET /cameras/1/daily?days=30
```

**Response:** 200 OK
```json
[
  {
    "date": "2025-01-15",
    "camera_id": 1,
    "entries": 234,
    "exits": 231,
    "avg_occupancy": 46.2,
    "peak_occupancy": 65,
    "peak_hour": 14,
    "unique_persons": 189
  },
  {
    "date": "2025-01-14",
    "camera_id": 1,
    "entries": 210,
    "exits": 208,
    "avg_occupancy": 42.1,
    "peak_occupancy": 58,
    "peak_hour": 13,
    "unique_persons": 165
  }
]
```

**Field Descriptions:**
- `entries` - Total people entered in day
- `exits` - Total people exited in day
- `avg_occupancy` - Average occupancy across all hours
- `peak_occupancy` - Maximum occupancy in day
- `peak_hour` - Hour (0-23) when peak occurred
- `unique_persons` - Number of unique individuals

**Typical Use Cases:**
- Daily reports
- Week-over-week comparison
- Occupancy trends

---

## 📅 Historical Data - Monthly

### Get Monthly Occupancy
**GET** `/cameras/{camera_id}/monthly`

Get monthly aggregated occupancy data.

**Path Parameters:**
- `camera_id` (int, required)

**Query Parameters:**
- `months` (int, default: 12) - Last N months of data

**Example Request:**
```
GET /cameras/1/monthly?months=12
```

**Response:** 200 OK
```json
[
  {
    "period": "2025-01",
    "camera_id": 1,
    "entries": 5460,
    "exits": 5430,
    "avg_daily_occupancy": 45.3,
    "peak_occupancy": 78,
    "unique_persons": 1850
  },
  {
    "period": "2024-12",
    "camera_id": 1,
    "entries": 5320,
    "exits": 5290,
    "avg_daily_occupancy": 42.8,
    "peak_occupancy": 72,
    "unique_persons": 1720
  }
]
```

**Field Descriptions:**
- `entries` - Total people entered in month
- `exits` - Total people exited in month
- `avg_daily_occupancy` - Average daily occupancy
- `peak_occupancy` - Highest daily occupancy in month
- `unique_persons` - Total unique individuals

**Typical Use Cases:**
- Monthly reports
- Year-over-year comparison
- Long-term planning
- Compliance reporting

---

## ⚠️ Alerts

### Get Active Alerts
**GET** `/alerts`

Get currently unresolved occupancy alerts.

**Query Parameters:**
- `camera_id` (int, optional) - Filter by camera

**Example Requests:**
```
GET /alerts                    # All active alerts
GET /alerts?camera_id=1        # Alerts for camera 1
```

**Response:** 200 OK
```json
[
  {
    "id": 1,
    "camera_id": 1,
    "alert_type": "capacity_exceeded",
    "current_occupancy": 105,
    "message": "Occupancy (105) exceeds capacity (100)",
    "is_resolved": false,
    "timestamp": "2025-01-15T10:30:00Z"
  },
  {
    "id": 2,
    "camera_id": 2,
    "alert_type": "anomaly_detected",
    "current_occupancy": 250,
    "message": "Occupancy anomaly detected",
    "is_resolved": false,
    "timestamp": "2025-01-15T10:25:00Z"
  }
]
```

**Alert Types:**
- `capacity_exceeded` - Occupancy > max_occupancy
- `capacity_warning` - Occupancy > 80% of capacity
- `anomaly_detected` - Unusual pattern detected
- `negative_count` - Occupancy would go below 0
- `equipment_failure` - Camera/detection failure

---

### Resolve Alert
**PUT** `/alerts/{alert_id}/resolve`

Mark an alert as resolved.

**Path Parameters:**
- `alert_id` (int, required)

**Response:** 200 OK
```json
{
  "status": "success",
  "alert_id": 1,
  "resolved_at": "2025-01-15T10:35:00Z"
}
```

---

## 📊 Facility Statistics

### Get Facility Statistics
**GET** `/facility/stats`

Get overall facility statistics and status.

**Response:** 200 OK
```json
{
  "total_cameras": 3,
  "active_cameras": 3,
  "total_persons_in_facility": 450,
  "capacity_utilization": 75.5,
  "active_alerts": 2,
  "timestamp": "2025-01-15T10:30:45Z"
}
```

**Field Descriptions:**
- `total_cameras` - Total configured cameras
- `active_cameras` - Cameras currently operating
- `total_persons_in_facility` - Sum of occupancy across all areas
- `capacity_utilization` - Percentage of total capacity in use
- `active_alerts` - Number of unresolved alerts

**Typical Use Cases:**
- Dashboard summary
- Admin overview
- Facility planning

---

## 🔧 Administration

### Trigger Aggregation
**POST** `/aggregate`

Manually trigger time-series data aggregation (for testing/recovery).

**Request Body:**
```json
{
  "camera_id": null,
  "aggregation_level": "hourly"
}
```

**Parameters:**
- `camera_id` (int, optional) - Specific camera or null for all
- `aggregation_level` (string) - "hourly", "daily", or "monthly"

**Response:** 202 Accepted
```json
{
  "status": "aggregation_triggered",
  "level": "hourly",
  "timestamp": "2025-01-15T10:30:45Z"
}
```

**Notes:**
- Normally runs automatically on schedule
- Use for recovery or testing
- Aggregation runs asynchronously

---

## ❌ Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message describing the problem"
}
```

### Common HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | GET request worked |
| 201 | Created | New camera created |
| 202 | Accepted | Async task accepted |
| 400 | Bad Request | Invalid parameters |
| 404 | Not Found | Camera doesn't exist |
| 409 | Conflict | Duplicate camera ID |
| 500 | Server Error | Database connection lost |
| 503 | Service Unavailable | Service not initialized |

### Common Errors

**Service Not Initialized**
```json
{
  "detail": "Occupancy service not initialized"
}
Status: 503
```

**Camera Not Found**
```json
{
  "detail": "Camera 999 not found"
}
Status: 404
```

**Duplicate Camera**
```json
{
  "detail": "Camera with ID 'GATE_A' already exists"
}
Status: 409
```

---

## 🔄 Pagination

Long responses (lists) may be paginated in future versions.

**Expected Format:**
```json
{
  "items": [...],
  "total": 100,
  "limit": 50,
  "offset": 0
}
```

Currently, all results are returned without pagination, but design your client to handle pagination.

---

## 🔑 Authentication

This API reference assumes authentication is configured separately.

Add authentication headers as needed:
```
Authorization: Bearer {token}
```

---

## 📝 Request Examples

### Using cURL

```bash
# Get current occupancy
curl http://localhost:8000/api/occupancy/cameras/1/live

# Create camera
curl -X POST http://localhost:8000/api/occupancy/cameras \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": "GATE_A",
    "camera_name": "Gate A",
    "camera_type": "entry_only"
  }'

# Get daily data for last 30 days
curl "http://localhost:8000/api/occupancy/cameras/1/daily?days=30"

# Calibrate occupancy
curl -X POST http://localhost:8000/api/occupancy/cameras/1/calibrate \
  -H "Content-Type: application/json" \
  -d '{"occupancy_value": 50}'
```

### Using Python

```python
import requests

BASE_URL = "http://localhost:8000/api/occupancy"

# Get live occupancy
response = requests.get(f"{BASE_URL}/cameras/1/live")
occupancy = response.json()
print(f"Current occupancy: {occupancy['current_occupancy']}")

# Create camera
camera_data = {
    "camera_id": "GATE_B",
    "camera_name": "Gate B",
    "camera_type": "exit_only",
    "max_occupancy": 150
}
response = requests.post(f"{BASE_URL}/cameras", json=camera_data)
new_camera = response.json()
print(f"Created camera: {new_camera['id']}")

# Get daily summaries
response = requests.get(f"{BASE_URL}/cameras/1/daily", params={"days": 7})
daily_data = response.json()
for day in daily_data:
    print(f"{day['date']}: {day['entries']} entries, {day['exits']} exits")
```

### Using JavaScript/Fetch

```javascript
const BASE_URL = 'http://localhost:8000/api/occupancy';

// Get live occupancy
async function getLiveOccupancy(cameraId) {
  const response = await fetch(`${BASE_URL}/cameras/${cameraId}/live`);
  return await response.json();
}

// Create camera
async function createCamera(cameraData) {
  const response = await fetch(`${BASE_URL}/cameras`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(cameraData)
  });
  return await response.json();
}

// Get daily data
async function getDailyData(cameraId, days = 30) {
  const response = await fetch(
    `${BASE_URL}/cameras/${cameraId}/daily?days=${days}`
  );
  return await response.json();
}

// Usage
getLiveOccupancy(1).then(data => {
  console.log('Current occupancy:', data.current_occupancy);
});
```

---

## 📞 Support

For issues or questions:
1. Check response status codes and error messages
2. Review logs: `/var/log/occupancy_service.log`
3. Verify camera configuration: `GET /cameras`
4. Check virtual lines: `GET /cameras/{id}/lines`
5. Review database: Check PostgreSQL directly if needed

---

**API Version:** 1.0  
**Last Updated:** Jan 2025  
**Status:** Production Ready  
**OpenAPI Spec:** Available at `/docs` (Swagger UI)
