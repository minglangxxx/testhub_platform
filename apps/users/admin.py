from django.contrib import admin
from .models import User, UserProfile
from .models import Department

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'department_display', 'position', 'is_active', 'date_joined']
    list_filter = ['is_active', 'position']
    search_fields = ['username', 'email', 'first_name', 'last_name']

    def department_display(self, obj):
        return ', '.join([d.name for d in obj.department.all()])
    department_display.short_description = '部门'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'theme', 'language', 'timezone']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'created_at']
    search_fields = ['name', 'code']