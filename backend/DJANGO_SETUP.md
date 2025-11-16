# Factory Safety Detection System - Django Backend Setup

## PostgreSQL Database Setup

### Installation Steps

1. **Download and Install PostgreSQL**
   - Download from: https://www.postgresql.org/download/windows/
   - Run the installer
   - Set password for postgres user: `postgres`
   - Default port: 5432

2. **Create Database**
   ```sql
   -- Open PostgreSQL command line (psql) or pgAdmin
   CREATE DATABASE factory_safety_db;
   ```

   Or via command line:
   ```powershell
   psql -U postgres
   # Enter password when prompted
   CREATE DATABASE factory_safety_db;
   \q
   ```

## Django Setup

### 1. Install Dependencies

```powershell
cd backend
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the backend folder (already created):
```env
DB_NAME=factory_safety_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
```

### 3. Run Migrations

```powershell
cd backend
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Django Admin User

```powershell
python manage.py createsuperuser
```

Enter details:
- Username: admin
- Email: admin@factory.com
- Password: admin123 (or your choice)

### 5. Run Django Server

```powershell
python manage.py runserver 8000
```

## Database Models Created

1. **HelmetDetection** - Stores helmet detection data
   - Fields: timestamp, total_people, compliant_count, violation_count, compliance_rate

2. **LoiteringDetection** - Stores loitering detection data
   - Fields: timestamp, active_groups, group_details, alert_triggered

3. **ProductionCounter** - Stores production counting data
   - Fields: timestamp, item_count, session_date, box_type

4. **Employee** - Stores employee information
   - Fields: first_name, last_name, employee_id, photo_path, department, position

5. **AttendanceRecord** - Stores attendance records
   - Fields: employee (FK), timestamp, date, check_in_time, confidence_score, status

6. **SystemLog** - Stores system logs and events
   - Fields: timestamp, log_type, severity, message, details

7. **DailyReport** - Stores daily summary reports
   - Fields: date, total_employees_present, total_helmet_violations, etc.

## API Endpoints

### Base URL: `http://localhost:8000/api/`

#### Helmet Detection
- `GET /api/helmet-detection/` - List all records
- `POST /api/helmet-detection/` - Create new record
- `GET /api/helmet-detection/recent/?limit=10` - Get recent records
- `GET /api/helmet-detection/violations/` - Get violation records
- `GET /api/stats/helmet/` - Get helmet statistics

#### Loitering Detection
- `GET /api/loitering-detection/` - List all records
- `POST /api/loitering-detection/` - Create new record
- `GET /api/loitering-detection/alerts/` - Get alert records
- `GET /api/stats/loitering/` - Get loitering statistics

#### Production Counter
- `GET /api/production-counter/` - List all records
- `POST /api/production-counter/` - Create new record
- `GET /api/production-counter/today/` - Get today's count
- `GET /api/production-counter/monthly/` - Get monthly count
- `GET /api/stats/production/` - Get production statistics

#### Employees
- `GET /api/employees/` - List all employees
- `POST /api/employees/` - Create new employee
- `GET /api/employees/search/?q=name` - Search employees

#### Attendance
- `GET /api/attendance/` - List all attendance records
- `POST /api/attendance/` - Create new record
- `GET /api/attendance/today/` - Get today's attendance
- `GET /api/attendance/employee_history/?employee_id=EMP001` - Get employee history
- `GET /api/stats/attendance/` - Get attendance statistics

#### Dashboard
- `GET /api/dashboard/summary/` - Get comprehensive dashboard summary

#### System Logs
- `GET /api/system-logs/` - List all logs
- `GET /api/system-logs/errors/` - Get error logs

#### Daily Reports
- `GET /api/daily-reports/` - List all daily reports

## Django Admin Panel

Access: `http://localhost:8000/admin/`
- Username: admin
- Password: (set during createsuperuser)

You can manage all data through the admin panel.

## Testing API Endpoints

### Using curl:
```powershell
# Get helmet stats
curl http://localhost:8000/api/stats/helmet/

# Create helmet detection record
curl -X POST http://localhost:8000/api/helmet-detection/ -H "Content-Type: application/json" -d "{\"total_people\": 10, \"compliant_count\": 8, \"violation_count\": 2}"
```

### Using browser:
Navigate to `http://localhost:8000/api/` to see all available endpoints.

## Integration with Angular Frontend

Update Angular services to point to Django API:
- Base URL: `http://localhost:8000/api/`
- CORS is configured to allow `http://localhost:4200`

## Next Steps

1. Install PostgreSQL
2. Create database
3. Run migrations
4. Create superuser
5. Start Django server
6. Test API endpoints
7. Update Angular frontend to use Django APIs
8. Integrate ML services with Django views to save data
