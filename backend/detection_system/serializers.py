from rest_framework import serializers
from .models import (
    HelmetDetection, LoiteringDetection, ProductionCounter,
    Employee, AttendanceRecord, SystemLog, DailyReport
)


class HelmetDetectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HelmetDetection
        fields = '__all__'
        read_only_fields = ('id', 'timestamp', 'compliance_rate')


class LoiteringDetectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoiteringDetection
        fields = '__all__'
        read_only_fields = ('id', 'timestamp')


class ProductionCounterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionCounter
        fields = '__all__'
        read_only_fields = ('id', 'timestamp')


class EmployeeSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = Employee
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class AttendanceRecordSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_id_number = serializers.CharField(source='employee.employee_id', read_only=True)
    
    class Meta:
        model = AttendanceRecord
        fields = '__all__'
        read_only_fields = ('id', 'timestamp')


class SystemLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemLog
        fields = '__all__'
        read_only_fields = ('id', 'timestamp')


class DailyReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyReport
        fields = '__all__'
        read_only_fields = ('id', 'generated_at')


# Statistics Serializers
class HelmetStatsSerializer(serializers.Serializer):
    total_detections = serializers.IntegerField()
    total_violations = serializers.IntegerField()
    average_compliance = serializers.FloatField()
    latest_detection = HelmetDetectionSerializer()


class LoiteringStatsSerializer(serializers.Serializer):
    total_alerts = serializers.IntegerField()
    active_groups = serializers.IntegerField()
    latest_detection = LoiteringDetectionSerializer()


class ProductionStatsSerializer(serializers.Serializer):
    total_items_today = serializers.IntegerField()
    total_items_this_month = serializers.IntegerField()
    latest_count = ProductionCounterSerializer()


class AttendanceStatsSerializer(serializers.Serializer):
    total_employees = serializers.IntegerField()
    present_today = serializers.IntegerField()
    absent_today = serializers.IntegerField()
    late_today = serializers.IntegerField()
    attendance_rate = serializers.FloatField()
