from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TestReportViewSet, AgentReportViewSet

router = DefaultRouter()
router.register(r'reports', TestReportViewSet, basename='reports')
router.register(r'agent-reports', AgentReportViewSet, basename='agent-report')


urlpatterns = router.urls
