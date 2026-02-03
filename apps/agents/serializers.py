from rest_framework import serializers
from .models import Agent, Tag

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'

class AgentSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=Tag.objects.all(), source='tags', required=False
    )

    class Meta:
        model = Agent
        fields = [
            'id', 'name', 'ip_address', 'status', 'cpu_usage', 
            'memory_usage', 'disk_usage', 'tags', 'tag_ids', 'last_heartbeat', 
            'created_at', 'updated_at', 'os_info', 'agent_version'
        ]
        read_only_fields = ('last_heartbeat', 'created_at', 'updated_at')

class AgentHeartbeatSerializer(serializers.Serializer):
    agent_id = serializers.CharField(max_length=64)
    status = serializers.ChoiceField(choices=Agent.STATUS_CHOICES)
    resources = serializers.JSONField()
    os_info = serializers.CharField(max_length=255, required=False)
    agent_version = serializers.CharField(max_length=50, required=False)
