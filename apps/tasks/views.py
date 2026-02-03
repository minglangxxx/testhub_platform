from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
import uuid

from .models import Task, TaskLog, Agent
from .serializers import TaskSerializer, TaskStatusUpdateSerializer, TaskLogCreateSerializer

# A simple in-memory task queue for demonstration purposes
# For production, a more robust solution like Celery/Redis would be better.
TASK_QUEUE = {}

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all().order_by('-created_at')
    serializer_class = TaskSerializer
    lookup_field = 'id'

    def perform_create(self, serializer):
        task_id = str(uuid.uuid4())
        task = serializer.save(id=task_id)
        
        # Add task to the in-memory queue for the specified agent or for general polling
        agent_id = self.request.data.get('agent_id')
        if agent_id:
            if agent_id not in TASK_QUEUE:
                TASK_QUEUE[agent_id] = []
            TASK_QUEUE[agent_id].append(task)
        else:
            # A queue for tasks that can be picked up by any agent
            if 'any' not in TASK_QUEUE:
                TASK_QUEUE['any'] = []
            TASK_QUEUE['any'].append(task)

    @action(detail=False, methods=['get'], url_path='poll')
    def poll(self, request):
        agent_id = request.query_params.get('agent_id')
        if not agent_id:
            return Response({"error": "agent_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Check for agent-specific tasks first
        if agent_id in TASK_QUEUE and TASK_QUEUE[agent_id]:
            task = TASK_QUEUE[agent_id].pop(0)
            task.status = 'running'
            task.agent_id = agent_id
            task.started_at = timezone.now()
            task.save()
            return Response(TaskSerializer(task).data)

        # Then check for general tasks
        if 'any' in TASK_QUEUE and TASK_QUEUE['any']:
            task = TASK_QUEUE['any'].pop(0)
            task.status = 'running'
            task.agent_id = agent_id
            task.started_at = timezone.now()
            task.save()
            return Response(TaskSerializer(task).data)

        return Response({"message": "No pending tasks"}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='status')
    def update_status(self, request, id=None):
        task = self.get_object()
        serializer = TaskStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_status = serializer.validated_data['status']
        task.status = new_status
        
        if new_status in ['success', 'failed', 'timeout']:
            task.finished_at = timezone.now()
        
        task.save()
        # Here you could also handle the progress and message if needed
        
        return Response(TaskSerializer(task).data)

    @action(detail=True, methods=['post'], url_path='log')
    def add_log(self, request, id=None):
        task = self.get_object()
        serializer = TaskLogCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        TaskLog.objects.create(
            task=task,
            log_type=serializer.validated_data['type'],
            content=serializer.validated_data['content'],
            created_at=serializer.validated_data['timestamp']
        )
        
        return Response(status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='logs')
    def get_logs(self, request, id=None):
        task = self.get_object()
        logs = task.logs.all().order_by('created_at')
        # Simple serialization for now, could use a proper serializer
        log_data = [{"type": log.log_type, "content": log.content, "timestamp": log.created_at} for log in logs]
        return Response(log_data)
