from django.db import models
from apps.agents.models import Agent

class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('timeout', 'Timeout'),
    ]
    id = models.CharField(max_length=64, primary_key=True)
    name = models.CharField(max_length=256)
    description = models.TextField(blank=True, null=True)
    script = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', db_index=True)
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks', db_index=True)
    created_by = models.CharField(max_length=128, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    timeout = models.IntegerField(default=1800, help_text="Timeout in seconds")
    workspace_clean = models.BooleanField(default=True)
    env_vars = models.JSONField(null=True, blank=True)

    def __str__(self):
        return self.name

class TaskLog(models.Model):
    LOG_TYPE_CHOICES = [
        ('stdout', 'Stdout'),
        ('stderr', 'Stderr'),
    ]
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='logs')
    log_type = models.CharField(max_length=6, choices=LOG_TYPE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['task', 'created_at']),
        ]

    def __str__(self):
        return f"Log for task {self.task.id} at {self.created_at}"
