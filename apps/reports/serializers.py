from rest_framework import serializers
from .models import Report, Attachment, TestReport, ReportTemplate

class AgentReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = '__all__'

class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = '__all__'

class TestReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestReport
        fields = '__all__'

class ReportTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportTemplate
        fields = '__all__'
