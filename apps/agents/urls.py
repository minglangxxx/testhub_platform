from rest_framework.routers import DefaultRouter
from .views import AgentViewSet, TagViewSet

router = DefaultRouter()
router.register(r'agents', AgentViewSet, basename='agent')
router.register(r'tags', TagViewSet, basename='tag')

urlpatterns = router.urls
