from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def api_root(request):
    """API root endpoint with available endpoints"""
    return JsonResponse({
        'message': 'Factory Safety Detection System API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'admin': '/admin/',
            'api_base': '/api/',
            'helmet_detection': '/api/helmet-detection/',
            'loitering_detection': '/api/loitering-detection/',
            'production_counter': '/api/production-counter/',
            'employees': '/api/employees/',
            'attendance': '/api/attendance/',
            'system_logs': '/api/system-logs/',
            'daily_reports': '/api/daily-reports/',
            'statistics': {
                'helmet': '/api/stats/helmet/',
                'loitering': '/api/stats/loitering/',
                'production': '/api/stats/production/',
                'attendance': '/api/stats/attendance/',
                'dashboard': '/api/dashboard/summary/'
            }
        }
    })
