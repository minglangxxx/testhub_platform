from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from .models import Agent, Tag
from .serializers import AgentSerializer, TagSerializer, AgentHeartbeatSerializer

class AgentViewSet(viewsets.ModelViewSet):
    queryset = Agent.objects.all()
    serializer_class = AgentSerializer
    lookup_field = 'id'

    @action(detail=False, methods=['post'], url_path='register')
    def register(self, request):
        agent_id = request.data.get('agent_id')
        if not agent_id:
            return Response({"error": "agent_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        agent, created = Agent.objects.get_or_create(id=agent_id)
        
        # Update agent info on registration
        serializer = self.get_serializer(agent, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(last_heartbeat=timezone.now(), status='online')

        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='heartbeat')
    def heartbeat(self, request):
        serializer = AgentHeartbeatSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        agent_id = data['agent_id']
        
        try:
            agent = Agent.objects.get(id=agent_id)
            agent.status = data['status']
            agent.cpu_usage = data['resources'].get('cpu_usage')
            agent.memory_usage = data['resources'].get('memory_usage')
            agent.disk_usage = data['resources'].get('disk_usage')
            agent.os_info = data.get('os_info', agent.os_info)
            agent.agent_version = data.get('agent_version', agent.agent_version)
            agent.last_heartbeat = timezone.now()
            agent.save()
            return Response({"message": "Heartbeat received"}, status=status.HTTP_200_OK)
        except Agent.DoesNotExist:
            # If agent does not exist, register it
            new_agent_data = {
                "id": agent_id,
                "status": data['status'],
                "cpu_usage": data['resources'].get('cpu_usage'),
                "memory_usage": data['resources'].get('memory_usage'),
                "disk_usage": data['resources'].get('disk_usage'),
                "os_info": data.get('os_info'),
                "agent_version": data.get('agent_version'),
                "last_heartbeat": timezone.now()
            }
            agent = Agent.objects.create(**new_agent_data)
            return Response(AgentSerializer(agent).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['put'], url_path='status')
    def update_status(self, request, id=None):
        try:
            agent = self.get_object()
            new_status = request.data.get('status')
            if new_status not in [s[0] for s in Agent.STATUS_CHOICES]:
                return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)
            
            agent.status = new_status
            agent.save()
            return Response(self.get_serializer(agent).data)
        except Agent.DoesNotExist:
            return Response({"error": "Agent not found"}, status=status.HTTP_404_NOT_FOUND)

class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
