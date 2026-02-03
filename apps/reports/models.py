from django.db import models
from django.utils import timezone
from apps.users.models import User
from apps.projects.models import Project
from apps.executions.models import TestRun
from apps.tasks.models import Task


class TestReport(models.Model):
    """测试报告"""
    TYPE_CHOICES = [
        ('execution', '执行报告'),
        ('summary', '汇总报告'),
        ('trend', '趋势报告'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='reports')
    name = models.CharField(max_length=200, verbose_name='报告名称')
    report_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='execution', verbose_name='报告类型')
    execution = models.OneToOneField(TestRun, on_delete=models.CASCADE, null=True, blank=True, related_name='report', verbose_name='关联执行')
    summary = models.JSONField(default=dict, verbose_name='报告摘要')
    content = models.JSONField(default=dict, verbose_name='报告内容')
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='生成者')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'test_reports'
        verbose_name = '测试报告'
        verbose_name_plural = '测试报告'
        ordering = ['-created_at']

class ReportTemplate(models.Model):
    """报告模板"""
    name = models.CharField(max_length=200, verbose_name='模板名称')
    description = models.TextField(blank=True, verbose_name='模板描述')
    template_config = models.JSONField(default=dict, verbose_name='模板配置')
    is_default = models.BooleanField(default=False, verbose_name='是否默认')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='创建者')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'report_templates'
        verbose_name = '报告模板'
        verbose_name_plural = '报告模板'


class Report(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='agent_reports', db_index=True)
    report_path = models.CharField(max_length=512)
    summary = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report for task {self.task.id}"

class Attachment(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attachments', db_index=True)
    file_name = models.CharField(max_length=256)
    file_path = models.CharField(max_length=512)
    file_size = models.BigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file_name