from django.utils import timezone
from django.db import models

class UnknownAttendance(models.Model):
    """Model to store unknown/failed attendance attempts (unrecognized faces)"""
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    snapshot = models.ImageField(upload_to='attendance/unknown/', null=True, blank=True)  # Face snapshot
    confidence_score = models.FloatField(default=0.0)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'unknown_attendance'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
        ]

    def __str__(self):
        return f"Unknown - {self.timestamp} (conf: {self.confidence_score})"
from django.db import models

class SystemConfiguration(models.Model):
    """Model to store system-wide configuration (key-value pairs)"""
    key = models.CharField(max_length=100, unique=True)
    value = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'system_configuration'
        ordering = ['key']

    def __str__(self):
        return f"{self.key}: {self.value}"


class ModuleConfiguration(models.Model):
    """Model to enable/disable modules and store per-module settings"""
    module_name = models.CharField(max_length=50, unique=True)
    enabled = models.BooleanField(default=True)
    settings = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'module_configuration'
        ordering = ['module_name']

    def __str__(self):
        return f"{self.module_name} (enabled={self.enabled})"
from django.db import models
from django.utils import timezone


class HelmetDetection(models.Model):
    """Model to store helmet detection data"""
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    total_people = models.IntegerField(default=0)
    compliant_count = models.IntegerField(default=0)
    violation_count = models.IntegerField(default=0)
    compliance_rate = models.FloatField(default=0.0)
    frame_data = models.JSONField(null=True, blank=True)  # Store detection details
    
    class Meta:
        db_table = 'helmet_detection'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
        ]
    
    def __str__(self):
        return f"Helmet Detection - {self.timestamp} - {self.violation_count} violations"
    
    def save(self, *args, **kwargs):
        # Calculate compliance rate
        if self.total_people > 0:
            self.compliance_rate = (self.compliant_count / self.total_people) * 100
        super().save(*args, **kwargs)


class LoiteringDetection(models.Model):
    """Model to store loitering detection data"""
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    active_groups = models.IntegerField(default=0)
    group_details = models.JSONField(null=True, blank=True)  # Store group information
    alert_triggered = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'loitering_detection'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
        ]
    
    def __str__(self):
        return f"Loitering Detection - {self.timestamp} - {self.active_groups} groups"


class ProductionCounter(models.Model):
    """Model to store production counter data"""
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    item_count = models.IntegerField(default=0)
    session_date = models.DateField(default=timezone.now)
    box_type = models.CharField(max_length=50, null=True, blank=True)
    details = models.JSONField(null=True, blank=True)  # Store counting details
    
    class Meta:
        db_table = 'production_counter'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['session_date']),
        ]
    
    def __str__(self):
        return f"Production - {self.timestamp} - {self.item_count} items"


class Employee(models.Model):
    """Model to store employee information"""
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    employee_id = models.CharField(max_length=50, unique=True)
    photo = models.ImageField(upload_to='employees/', null=True, blank=True)
    department = models.CharField(max_length=100, blank=True)
    position = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'employees'
        ordering = ['first_name', 'last_name']
        indexes = [
            models.Index(fields=['employee_id']),
            models.Index(fields=['first_name']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_id})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class AttendanceRecord(models.Model):
    """Model to store attendance records"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    date = models.DateField(default=timezone.now, db_index=True)
    check_in_time = models.TimeField(null=True, blank=True)
    confidence_score = models.FloatField(default=0.0)
    snapshot = models.ImageField(upload_to='attendance/verified/', null=True, blank=True)  # Face snapshot
    status = models.CharField(
        max_length=20,
        choices=[
            ('present', 'Present'),
            ('late', 'Late'),
            ('absent', 'Absent'),
        ],
        default='present'
    )
    
    class Meta:
        db_table = 'attendance_records'
        ordering = ['-timestamp']
        unique_together = [['employee', 'date']]  # One record per employee per day
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['date']),
            models.Index(fields=['employee', 'date']),
        ]
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.date} - {self.status}"


class SystemLog(models.Model):
    """Model to store system logs and events"""
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    log_type = models.CharField(
        max_length=50,
        choices=[
            ('helmet', 'Helmet Detection'),
            ('loitering', 'Loitering Detection'),
            ('production', 'Production Counter'),
            ('attendance', 'Attendance System'),
            ('system', 'System Event'),
            ('error', 'Error'),
        ]
    )
    severity = models.CharField(
        max_length=20,
        choices=[
            ('info', 'Info'),
            ('warning', 'Warning'),
            ('error', 'Error'),
            ('critical', 'Critical'),
        ],
        default='info'
    )
    message = models.TextField()
    details = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'system_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['log_type']),
            models.Index(fields=['severity']),
        ]
    
    def __str__(self):
        return f"[{self.severity.upper()}] {self.log_type} - {self.timestamp}"


class DailyReport(models.Model):
    """Model to store daily summary reports"""
    date = models.DateField(unique=True, db_index=True)
    total_employees_present = models.IntegerField(default=0)
    total_helmet_violations = models.IntegerField(default=0)
    total_loitering_alerts = models.IntegerField(default=0)
    total_items_produced = models.IntegerField(default=0)
    average_compliance_rate = models.FloatField(default=0.0)
    report_data = models.JSONField(null=True, blank=True)
    generated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'daily_reports'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['-date']),
        ]
    
    def __str__(self):
        return f"Daily Report - {self.date}"
