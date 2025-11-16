from django.contrib import admin
from .models import (
    HelmetDetection, LoiteringDetection, ProductionCounter,
    Employee, AttendanceRecord, SystemLog, DailyReport
)


@admin.register(HelmetDetection)
class HelmetDetectionAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'total_people', 'compliant_count', 'violation_count', 'compliance_rate')
    list_filter = ('timestamp',)
    search_fields = ('timestamp',)
    ordering = ('-timestamp',)
    readonly_fields = ('compliance_rate',)


@admin.register(LoiteringDetection)
class LoiteringDetectionAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'active_groups', 'alert_triggered')
    list_filter = ('timestamp', 'alert_triggered')
    search_fields = ('timestamp',)
    ordering = ('-timestamp',)


@admin.register(ProductionCounter)
class ProductionCounterAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'session_date', 'item_count', 'box_type')
    list_filter = ('session_date', 'box_type')
    search_fields = ('session_date', 'box_type')
    ordering = ('-timestamp',)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'full_name', 'department', 'position', 'is_active', 'created_at')
    list_filter = ('is_active', 'department', 'position')
    search_fields = ('first_name', 'last_name', 'employee_id', 'department')
    ordering = ('first_name', 'last_name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'check_in_time', 'status', 'confidence_score')
    list_filter = ('date', 'status')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_id')
    ordering = ('-date', '-timestamp')


@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'log_type', 'severity', 'message')
    list_filter = ('timestamp', 'log_type', 'severity')
    search_fields = ('message', 'log_type')
    ordering = ('-timestamp',)


@admin.register(DailyReport)
class DailyReportAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_employees_present', 'total_helmet_violations', 
                    'total_loitering_alerts', 'total_items_produced', 'average_compliance_rate')
    list_filter = ('date',)
    search_fields = ('date',)
    ordering = ('-date',)
    readonly_fields = ('generated_at',)
