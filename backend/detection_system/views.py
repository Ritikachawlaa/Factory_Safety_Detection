from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Camera
from .serializers import CameraSerializer

# Camera CRUD API
class CameraViewSet(viewsets.ModelViewSet):
    """ViewSet for managing cameras (CCTV/RTSP/HTTP/USB)"""
    queryset = Camera.objects.all()
    serializer_class = CameraSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
    HelmetDetection, LoiteringDetection, ProductionCounter,
    Employee, AttendanceRecord, SystemLog, DailyReport,
    SystemConfiguration, ModuleConfiguration
)
from .serializers import (
    HelmetDetectionSerializer, LoiteringDetectionSerializer,
    ProductionCounterSerializer, EmployeeSerializer,
    AttendanceRecordSerializer, SystemLogSerializer,
    DailyReportSerializer, HelmetStatsSerializer,
    LoiteringStatsSerializer, ProductionStatsSerializer,
    AttendanceStatsSerializer
)


class HelmetDetectionViewSet(viewsets.ModelViewSet):
    """ViewSet for helmet detection records"""
    queryset = HelmetDetection.objects.all()
    serializer_class = HelmetDetectionSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
            
        return queryset
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent helmet detections"""
        limit = int(request.query_params.get('limit', 10))
        recent_records = self.queryset[:limit]
        serializer = self.get_serializer(recent_records, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def violations(self, request):
        """Get records with violations"""
        violations = self.queryset.filter(violation_count__gt=0)
        serializer = self.get_serializer(violations, many=True)
        return Response(serializer.data)


class LoiteringDetectionViewSet(viewsets.ModelViewSet):
    """ViewSet for loitering detection records"""
    queryset = LoiteringDetection.objects.all()
    serializer_class = LoiteringDetectionSerializer
    
    @action(detail=False, methods=['get'])
    def alerts(self, request):
        """Get records where alerts were triggered"""
        alerts = self.queryset.filter(alert_triggered=True)
        serializer = self.get_serializer(alerts, many=True)
        return Response(serializer.data)


class ProductionCounterViewSet(viewsets.ModelViewSet):
    """ViewSet for production counter records"""
    queryset = ProductionCounter.objects.all()
    serializer_class = ProductionCounterSerializer
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's production count"""
        today = timezone.now().date()
        today_records = self.queryset.filter(session_date=today)
        total = today_records.aggregate(total=Sum('item_count'))['total'] or 0
        
        return Response({
            'date': today,
            'total_items': total,
            'records': self.get_serializer(today_records, many=True).data
        })
    
    @action(detail=False, methods=['get'])
    def monthly(self, request):
        """Get monthly production statistics"""
        month = request.query_params.get('month', timezone.now().month)
        year = request.query_params.get('year', timezone.now().year)
        
        monthly_records = self.queryset.filter(
            session_date__month=month,
            session_date__year=year
        )
        total = monthly_records.aggregate(total=Sum('item_count'))['total'] or 0
        
        return Response({
            'month': month,
            'year': year,
            'total_items': total
        })


class EmployeeViewSet(viewsets.ModelViewSet):
    """ViewSet for employee management"""
    queryset = Employee.objects.filter(is_active=True)
    serializer_class = EmployeeSerializer
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search employees by name or employee_id"""
        query = request.query_params.get('q', '')
        if query:
            employees = self.queryset.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(employee_id__icontains=query)
            )
            serializer = self.get_serializer(employees, many=True)
            return Response(serializer.data)
        return Response([])


class AttendanceRecordViewSet(viewsets.ModelViewSet):
    """ViewSet for attendance records"""
    queryset = AttendanceRecord.objects.all()
    serializer_class = AttendanceRecordSerializer
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's attendance records"""
        today = timezone.now().date()
        today_records = self.queryset.filter(date=today)
        serializer = self.get_serializer(today_records, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def employee_history(self, request):
        """Get attendance history for a specific employee"""
        employee_id = request.query_params.get('employee_id')
        if not employee_id:
            return Response({'error': 'employee_id required'}, status=400)
        
        records = self.queryset.filter(employee__employee_id=employee_id)
        serializer = self.get_serializer(records, many=True)
        return Response(serializer.data)


class SystemLogViewSet(viewsets.ModelViewSet):
    """ViewSet for system logs"""
    queryset = SystemLog.objects.all()
    serializer_class = SystemLogSerializer
    
    @action(detail=False, methods=['get'])
    def errors(self, request):
        """Get error logs"""
        errors = self.queryset.filter(severity__in=['error', 'critical'])
        serializer = self.get_serializer(errors, many=True)
        return Response(serializer.data)


class DailyReportViewSet(viewsets.ModelViewSet):
    """ViewSet for daily reports"""
    queryset = DailyReport.objects.all()
    serializer_class = DailyReportSerializer


# Statistics Views
class HelmetStatsView(APIView):
    """Get helmet detection statistics"""
    
    def get(self, request):
        today = timezone.now().date()
        queryset = HelmetDetection.objects.filter(timestamp__date=today)
        
        stats = queryset.aggregate(
            total_detections=Count('id'),
            total_violations=Sum('violation_count'),
            average_compliance=Avg('compliance_rate')
        )
        
        latest = queryset.first()
        
        data = {
            'total_detections': stats['total_detections'] or 0,
            'total_violations': stats['total_violations'] or 0,
            'average_compliance': round(stats['average_compliance'] or 0, 2),
            'latest_detection': HelmetDetectionSerializer(latest).data if latest else None
        }
        
        return Response(data)


class LoiteringStatsView(APIView):
    """Get loitering detection statistics"""
    
    def get(self, request):
        today = timezone.now().date()
        queryset = LoiteringDetection.objects.filter(timestamp__date=today)
        
        total_alerts = queryset.filter(alert_triggered=True).count()
        latest = queryset.first()
        active_groups = latest.active_groups if latest else 0
        
        data = {
            'total_alerts': total_alerts,
            'active_groups': active_groups,
            'latest_detection': LoiteringDetectionSerializer(latest).data if latest else None
        }
        
        return Response(data)


class ProductionStatsView(APIView):
    """Get production counter statistics"""
    
    def get(self, request):
        today = timezone.now().date()
        this_month_start = today.replace(day=1)
        
        today_count = ProductionCounter.objects.filter(
            session_date=today
        ).aggregate(total=Sum('item_count'))['total'] or 0
        
        month_count = ProductionCounter.objects.filter(
            session_date__gte=this_month_start
        ).aggregate(total=Sum('item_count'))['total'] or 0
        
        latest = ProductionCounter.objects.first()
        
        data = {
            'total_items_today': today_count,
            'total_items_this_month': month_count,
            'latest_count': ProductionCounterSerializer(latest).data if latest else None
        }
        
        return Response(data)


class AttendanceStatsView(APIView):
    """Get attendance statistics"""
    
    def get(self, request):
        today = timezone.now().date()
        total_employees = Employee.objects.filter(is_active=True).count()
        
        today_records = AttendanceRecord.objects.filter(date=today)
        present = today_records.filter(status='present').count()
        late = today_records.filter(status='late').count()
        absent = total_employees - present - late
        
        attendance_rate = (present / total_employees * 100) if total_employees > 0 else 0
        
        data = {
            'total_employees': total_employees,
            'present_today': present,
            'absent_today': absent,
            'late_today': late,
            'attendance_rate': round(attendance_rate, 2)
        }
        
        return Response(data)


class DashboardSummaryView(APIView):
    """Get comprehensive dashboard summary"""
    
    def get(self, request):
        today = timezone.now().date()
        
        # Helmet stats
        helmet_violations = HelmetDetection.objects.filter(
            timestamp__date=today
        ).aggregate(total=Sum('violation_count'))['total'] or 0
        
        # Loitering stats
        loitering_alerts = LoiteringDetection.objects.filter(
            timestamp__date=today,
            alert_triggered=True
        ).count()
        
        # Production stats
        production_count = ProductionCounter.objects.filter(
            session_date=today
        ).aggregate(total=Sum('item_count'))['total'] or 0
        
        # Attendance stats
        total_employees = Employee.objects.filter(is_active=True).count()
        present = AttendanceRecord.objects.filter(
            date=today,
            status__in=['present', 'late']
        ).count()
        
        summary = {
            'date': today,
            'helmet_violations': helmet_violations,
            'loitering_alerts': loitering_alerts,
            'production_count': production_count,
            'attendance': {
                'total_employees': total_employees,
                'present': present,
                'attendance_rate': round((present / total_employees * 100) if total_employees > 0 else 0, 2)
            }
        }
        
        return Response(summary)


class ModuleConfigurationView(APIView):
    """API for managing module configurations (enable/disable modules)"""
    
    def get(self, request):
        """Get all module configurations"""
        modules = ModuleConfiguration.objects.all()
        data = [{
            'module_name': module.module_name,
            'display_name': module.display_name,
            'is_enabled': module.is_enabled,
            'settings': module.settings,
            'description': module.description,
            'updated_at': module.updated_at
        } for module in modules]
        return Response(data)
    
    def post(self, request):
        """Create or update module configuration"""
        module_name = request.data.get('module_name')
        if not module_name:
            return Response({'error': 'module_name is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        module, created = ModuleConfiguration.objects.get_or_create(
            module_name=module_name,
            defaults={
                'display_name': request.data.get('display_name', module_name.replace('_', ' ').title()),
                'is_enabled': request.data.get('is_enabled', True),
                'settings': request.data.get('settings', {}),
                'description': request.data.get('description', ''),
                'updated_by': request.data.get('updated_by', 'admin')
            }
        )
        
        if not created:
            # Update existing module
            if 'is_enabled' in request.data:
                module.is_enabled = request.data['is_enabled']
            if 'settings' in request.data:
                module.settings = request.data['settings']
            if 'description' in request.data:
                module.description = request.data['description']
            if 'updated_by' in request.data:
                module.updated_by = request.data['updated_by']
            module.save()
        
        return Response({
            'message': 'Module configuration updated successfully',
            'module': {
                'module_name': module.module_name,
                'display_name': module.display_name,
                'is_enabled': module.is_enabled,
                'settings': module.settings,
            }
        }, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)


class SystemConfigurationView(APIView):
    """API for managing system-wide configuration settings"""
    
    def get(self, request):
        """Get system configuration by key or all configurations"""
        config_key = request.query_params.get('key')
        
        if config_key:
            try:
                config = SystemConfiguration.objects.get(config_key=config_key)
                return Response({
                    'config_key': config.config_key,
                    'config_value': config.config_value,
                    'description': config.description,
                    'updated_at': config.updated_at
                })
            except SystemConfiguration.DoesNotExist:
                return Response({'error': 'Configuration not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            configs = SystemConfiguration.objects.all()
            data = [{
                'config_key': config.config_key,
                'config_value': config.config_value,
                'description': config.description,
                'updated_at': config.updated_at
            } for config in configs]
            return Response(data)
    
    def post(self, request):
        """Create or update system configuration"""
        config_key = request.data.get('config_key')
        config_value = request.data.get('config_value')
        
        if not config_key or config_value is None:
            return Response(
                {'error': 'config_key and config_value are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        config, created = SystemConfiguration.objects.update_or_create(
            config_key=config_key,
            defaults={
                'config_value': config_value,
                'description': request.data.get('description', ''),
                'updated_by': request.data.get('updated_by', 'admin')
            }
        )
        
        return Response({
            'message': 'Configuration updated successfully',
            'config': {
                'config_key': config.config_key,
                'config_value': config.config_value,
                'description': config.description
            }
        }, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)
