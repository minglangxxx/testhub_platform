from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, UserProfile
from .models import Department

class UserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'avatar')

class UserSerializer(serializers.ModelSerializer):
    # 可选：在response中展示department详情，在request中接受id列表
    department_display = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'avatar', 'phone', 'department', 'department_display', 'position', 'is_active',
                 'date_joined', 'created_at', 'updated_at']
        read_only_fields = ['id', 'date_joined', 'created_at', 'updated_at', 'department_display']
    
    def get_department_display(self, obj):
        """返回部门名称列表用于前端显示"""
        return [{'id': d.id, 'name': d.name} for d in obj.department.all()]
    
    def update(self, instance, validated_data):
        """处理更新操作，支持department的ManyToMany更新"""
        departments = validated_data.pop('department', None)
        # 更新其他字段
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # 更新ManyToMany关系
        if departments is not None:
            instance.department.set(departments)
        
        return instance

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm',
                 'first_name', 'last_name', 'phone', 'department', 'position']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("密码不一致")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        # handle ManyToMany department: pop then set
        departments = validated_data.pop('department', None)
        user = User.objects.create_user(**validated_data)
        if departments:
            # departments may be list of ids or names; support both
            if all(isinstance(d, int) for d in departments):
                user.department.set(Department.objects.filter(id__in=departments))
            else:
                # assume list of names
                objs = []
                for name in departments:
                    obj, _ = Department.objects.get_or_create(name=name)
                    objs.append(obj)
                user.department.set(objs)
        return user


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'code', 'description', 'created_at']
        read_only_fields = ['id', 'created_at', 'code']

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('用户名或密码错误')
            if not user.is_active:
                raise serializers.ValidationError('用户已被禁用')
        else:
            raise serializers.ValidationError('用户名和密码不能为空')
        
        attrs['user'] = user
        return attrs

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'