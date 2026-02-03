from rest_framework import serializers
from .models import Task, TaskLog
from apps.agents.serializers import AgentSerializer

class TaskLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskLog
        fields = '__all__'

class TaskSerializer(serializers.ModelSerializer):
    agent = AgentSerializer(read_only=True)
    agent_id = serializers.CharField(write_only=True, required=False, allow_null=True)
    logs = TaskLogSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'name', 'description', 'script', 'status', 'agent', 'agent_id',
            'created_by', 'created_at', 'started_at', 'finished_at',
            'timeout', 'workspace_clean', 'env_vars', 'logs'
        ]
        read_only_fields = ('created_at', 'started_at', 'finished_at', 'logs')

class TaskStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Task.STATUS_CHOICES)
    progress = serializers.IntegerField(required=False)
    message = serializers.CharField(required=False)

class TaskLogCreateSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=TaskLog.LOG_TYPE_CHOICES)
    content = serializers.CharField()
    timestamp = serializers.DateTimeField()
