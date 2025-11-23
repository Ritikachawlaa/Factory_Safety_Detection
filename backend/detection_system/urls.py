from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, ml_views

router = DefaultRouter()
router.register(r'helmet-detection', views.HelmetDetectionViewSet, basename='helmet-detection')
router.register(r'loitering-detection', views.LoiteringDetectionViewSet, basename='loitering-detection')
router.register(r'production-counter', views.ProductionCounterViewSet, basename='production-counter')
router.register(r'employees', views.EmployeeViewSet, basename='employee')
router.register(r'attendance', views.AttendanceRecordViewSet, basename='attendance')
router.register(r'unknown-attendance', views.UnknownAttendanceViewSet, basename='unknown-attendance')
router.register(r'system-logs', views.SystemLogViewSet, basename='system-log')
router.register(r'daily-reports', views.DailyReportViewSet, basename='daily-report')

urlpatterns = [
    path('', include(router.urls)),
    
    # Statistics endpoints
    path('stats/helmet/', views.HelmetStatsView.as_view(), name='helmet-stats'),
    path('stats/loitering/', views.LoiteringStatsView.as_view(), name='loitering-stats'),
    path('stats/production/', views.ProductionStatsView.as_view(), name='production-stats'),
    path('stats/attendance/', views.AttendanceStatsView.as_view(), name='attendance-stats'),
    path('dashboard/summary/', views.DashboardSummaryView.as_view(), name='dashboard-summary'),
    
    # Live ML detection endpoints (webcam integration)
    path('live/helmet/', ml_views.helmet_detection_live, name='live-helmet'),
    path('live/loitering/', ml_views.loitering_detection_live, name='live-loitering'),
    path('live/production/', ml_views.production_counter_live, name='live-production'),
    path('live/production/reset/', ml_views.production_counter_reset, name='live-production-reset'),
    path('live/attendance/', ml_views.attendance_system_live, name='live-attendance'),
    path('test/ml-services/', ml_views.test_ml_services, name='test-ml-services'),

    # System/module config endpoints
    path('config/system/', views.SystemConfigView.as_view(), name='system-config'),
    path('config/modules/', views.ModuleConfigView.as_view(), name='module-config'),

    # New API endpoints for frontend
    path('violations/loitering/', views.LoiteringViolationsView.as_view(), name='loitering-violations'),
    path('violations/helmet/', views.HelmetViolationsView.as_view(), name='helmet-violations'),
    path('production/today/', views.ProductionTodayView.as_view(), name='production-today'),
]
