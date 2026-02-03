from django.db import models

class Tag(models.Model):
    name = models.CharField(max_length=64, unique=True)
    color = models.CharField(max_length=7, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Agent(models.Model):
    STATUS_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('busy', 'Busy'),
    ]
    id = models.CharField(max_length=64, primary_key=True)
    name = models.CharField(max_length=128, blank=True, null=True)
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='offline')
    cpu_usage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    memory_usage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    disk_usage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    tags = models.ManyToManyField(Tag, related_name='agents', blank=True)
    last_heartbeat = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    os_info = models.CharField(max_length=255, blank=True, null=True)
    agent_version = models.CharField(max_length=50, blank=True, null=True)


    def __str__(self):
        return self.name or self.id
