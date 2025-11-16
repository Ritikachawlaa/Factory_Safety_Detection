# Factory Safety Detector - Angular Frontend

A modern Angular frontend application for the Factory Safety Detection System. This application provides real-time monitoring of:
- 🪖 Helmet Detection (Safety Compliance)
- 👥 Loitering Detection (Security)
- 📦 Production Counter (Productivity)
- ✓ Attendance System (Employee Tracking)

## Features

- **Real-time Data Updates**: Automatically polls the FastAPI backend every 2-5 seconds
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Visual Dashboard**: Beautiful cards with statistics and progress indicators
- **Multiple Views**: Dashboard overview and dedicated feature pages
- **Live Status Badges**: Visual indicators for system status

## Tech Stack

- **Angular 17**: Modern web framework
- **RxJS**: Reactive programming for real-time updates
- **TypeScript**: Type-safe development
- **CSS3**: Modern styling with gradients and animations

## Prerequisites

- Node.js (v18 or higher)
- npm (v9 or higher)
- Angular CLI (v17 or higher)

## Installation

### Step 1: Install Node.js and npm

Download and install from: https://nodejs.org/

### Step 2: Install Angular CLI

```powershell
npm install -g @angular/cli
```

### Step 3: Install Dependencies

Navigate to the frontend folder and install dependencies:

```powershell
cd frontend
npm install
```

## Running the Application

### Start the Backend First

Make sure your FastAPI backend is running on port 8000:

```powershell
cd ..
uvicorn app.main:app --reload --port 8000
```

### Start the Angular Frontend

In a new terminal, navigate to the frontend folder and run:

```powershell
cd frontend
ng serve
```

Or use npm:

```powershell
npm start
```

The application will be available at: **http://localhost:4200**

## Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── components/
│   │   │   ├── dashboard/           # Main dashboard component
│   │   │   └── helmet-detection/    # Helmet detection detail view
│   │   ├── services/
│   │   │   ├── helmet.service.ts    # Helmet API service
│   │   │   ├── loitering.service.ts # Loitering API service
│   │   │   ├── production.service.ts# Production API service
│   │   │   └── attendance.service.ts# Attendance API service
│   │   ├── app.component.*          # Root component
│   │   ├── app.module.ts            # Main module
│   │   └── app-routing.module.ts    # Routing configuration
│   ├── environments/                # Environment configurations
│   ├── index.html                   # HTML entry point
│   ├── main.ts                      # Application bootstrap
│   └── styles.css                   # Global styles
├── angular.json                     # Angular configuration
├── package.json                     # Dependencies
└── tsconfig.json                    # TypeScript configuration
```

## API Integration

The frontend connects to the FastAPI backend at `http://localhost:8000/api` with the following endpoints:

- `GET /api/status/helmet` - Helmet detection status
- `GET /api/status/loitering` - Loitering detection status
- `GET /api/status/counting` - Production counter status
- `GET /api/status/attendance` - Attendance system status

### Configuration

To change the API URL, edit the environment files:

**src/environments/environment.ts** (Development):
```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api'
};
```

**src/environments/environment.prod.ts** (Production):
```typescript
export const environment = {
  production: true,
  apiUrl: 'https://your-production-api.com/api'
};
```

## Building for Production

To create a production build:

```powershell
ng build --configuration production
```

The build artifacts will be stored in the `dist/` directory.

## Development

### Generate New Components

```powershell
ng generate component components/component-name
```

### Generate New Services

```powershell
ng generate service services/service-name
```

### Run Tests

```powershell
ng test
```

## Troubleshooting

### CORS Issues

If you see CORS errors in the browser console, ensure your FastAPI backend has CORS enabled (it should already be configured in `app/main.py`).

### Connection Refused

Make sure:
1. The FastAPI backend is running on port 8000
2. The camera/video source is accessible
3. All Python dependencies are installed

### Port Already in Use

If port 4200 is already in use, you can run on a different port:

```powershell
ng serve --port 4300
```

## Browser Support

- Chrome (recommended)
- Firefox
- Safari
- Edge

## Contributing

1. Create a new branch for your feature
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

This project is part of the Factory Safety Detector system.

## Contact

For issues or questions, please open an issue in the repository.
