# Frontend Optimization - Installation & Setup Script

Write-Host "🚀 Starting Frontend Optimization Setup..." -ForegroundColor Cyan
Write-Host ""

# Navigate to frontend directory
Set-Location -Path "frontend"

# Step 1: Install core dependencies
Write-Host "📦 Installing Angular CDK and Charts..." -ForegroundColor Yellow
npm install @angular/cdk @swimlane/ngx-charts

# Step 2: Install Tailwind CSS
Write-Host "🎨 Installing Tailwind CSS..." -ForegroundColor Yellow
npm install -D tailwindcss autoprefixer postcss

# Step 3: Initialize Tailwind
Write-Host "⚙️ Initializing Tailwind configuration..." -ForegroundColor Yellow
npx tailwindcss init

# Step 4: Create Tailwind config
Write-Host "📝 Creating Tailwind configuration..." -ForegroundColor Yellow
$tailwindConfig = @"
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{html,ts}'],
  theme: {
    extend: {
      colors: {
        factory: {
          dark: '#0a0e1a',
          darker: '#050810',
          accent: '#00d9ff',
          danger: '#ff3b30',
          success: '#34c759',
          warning: '#ff9500',
          'gray-900': '#1a1d29',
          'gray-800': '#252936'
        }
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      }
    }
  },
  plugins: []
}
"@
$tailwindConfig | Out-File -FilePath "tailwind.config.js" -Encoding utf8

# Step 5: Update global styles
Write-Host "🎨 Updating global styles..." -ForegroundColor Yellow
$globalStyles = @"
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Factory Dark Theme Global Styles */
body {
  @apply bg-factory-dark text-gray-100;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* Custom Scrollbar */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  @apply bg-factory-darker;
}

::-webkit-scrollbar-thumb {
  @apply bg-gray-600 rounded;
}

::-webkit-scrollbar-thumb:hover {
  @apply bg-gray-500;
}
"@
$globalStyles | Out-File -FilePath "src/styles.css" -Encoding utf8

Write-Host ""
Write-Host "✅ Frontend optimization setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Run 'ng serve' to start development server" -ForegroundColor White
Write-Host "2. The SocketService and CameraConfigService are ready to use" -ForegroundColor White
Write-Host "3. Review FRONTEND_OPTIMIZATION_PLAN.md for implementation details" -ForegroundColor White
Write-Host ""
Write-Host "📚 Key files created:" -ForegroundColor Cyan
Write-Host "  • src/app/services/socket.service.ts (WebSocket + Signals)" -ForegroundColor White
Write-Host "  • src/app/services/camera-config.service.ts (Camera CRUD)" -ForegroundColor White
Write-Host "  • tailwind.config.js (Dark industrial theme)" -ForegroundColor White
Write-Host ""
