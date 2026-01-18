from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import login, logout
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import User, UserProfile
from .serializers import UserSerializer, UserCreateSerializer, LoginSerializer, UserProfileSerializer
from .models import Department
from .serializers import DepartmentSerializer

# JWT 相关导入
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_current_user(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import login, logout

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_current_user(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all().order_by('username')
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # 安全地创建token
        try:
            from rest_framework.authtoken.models import Token
            token, created = Token.objects.get_or_create(user=user)
            token_key = token.key
        except ImportError:
            token_key = f"temp_token_{user.id}"
        
        return Response({
            'user': UserSerializer(user).data,
            'token': token_key
        }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@csrf_exempt
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data['user']
    login(request, user)

    # JWT Token (优先使用JWT)
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)

    return Response({
        'user': UserSerializer(user).data,
        'access': access_token,       # JWT access token
        'refresh': refresh_token,     # JWT refresh token
        'message': '登录成功'
    })

@api_view(['POST'])
@csrf_exempt
def logout_view(request):
    """用户退出登录，将refresh token加入黑名单"""
    if request.user.is_authenticated:
        try:
            # 尝试将refresh token加入黑名单
            refresh_token = request.data.get('refresh')
            if refresh_token:
                from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
                from rest_framework_simplejwt.tokens import RefreshToken as JWTRefreshToken
                try:
                    token = JWTRefreshToken(refresh_token)
                    token.blacklist()
                except Exception as e:
                    print(f"Blacklist error: {e}")
        except Exception as e:
            print(f"Logout error: {e}")

        # 清除旧的auth token（向后兼容）
        try:
            request.user.auth_token.delete()
        except:
            pass

        logout(request)

    return Response({'message': '退出成功'})

@api_view(['GET'])
def profile_view(request):
    if not request.user.is_authenticated:
        return Response({'error': '未登录'}, status=status.HTTP_401_UNAUTHORIZED)
    
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class UserListView(generics.ListCreateAPIView):
    queryset = User.objects.all().order_by('-created_at')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone']
    filterset_fields = ['is_active', 'department']
    ordering_fields = ['username', 'created_at', 'email']
    ordering = ['-created_at']
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserSerializer

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class DepartmentListView(generics.ListCreateAPIView):
    queryset = Department.objects.all().order_by('name')
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    pagination_class = StandardResultsSetPagination


class DepartmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def batch_delete_departments(request):
    """批量删除部门"""
    ids = request.data.get('ids', [])
    if not ids:
        return Response({'error': '未提供要删除的部门ID'}, status=status.HTTP_400_BAD_REQUEST)
    
    deleted_count, _ = Department.objects.filter(id__in=ids).delete()
    return Response({
        'message': f'成功删除 {deleted_count} 个部门',
        'deleted_count': deleted_count
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def batch_delete_users(request):
    """批量删除用户"""
    ids = request.data.get('ids', [])
    if not ids:
        return Response({'error': '未提供要删除的用户ID'}, status=status.HTTP_400_BAD_REQUEST)
    
    # 防止删除当前用户
    if request.user.id in ids:
        return Response({'error': '不能删除当前登录用户'}, status=status.HTTP_400_BAD_REQUEST)
    
    deleted_count, _ = User.objects.filter(id__in=ids).delete()
    return Response({
        'message': f'成功删除 {deleted_count} 个用户',
        'deleted_count': deleted_count
    })
