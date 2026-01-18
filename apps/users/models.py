from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.db import transaction as dj_transaction

class User(AbstractUser):
    """扩展用户模型"""
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name='头像')
    phone = models.CharField(max_length=11, null=True, blank=True, verbose_name='手机号')
    # 支持用户隶属于多个部门
    department = models.ManyToManyField('Department', blank=True, related_name='users', verbose_name='部门')
    position = models.CharField(max_length=100, null=True, blank=True, verbose_name='职位')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'users_user'
        verbose_name = '用户'
        verbose_name_plural = '用户'

class UserProfile(models.Model):
    """用户配置"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    theme = models.CharField(max_length=20, default='light', verbose_name='主题')
    language = models.CharField(max_length=10, default='zh-cn', verbose_name='语言')
    timezone = models.CharField(max_length=50, default='Asia/Shanghai', verbose_name='时区')
    notifications = models.JSONField(default=dict, verbose_name='通知设置')
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = '用户配置'
        verbose_name_plural = '用户配置'


class Department(models.Model):
    """部门模型，用于多租户/组织管理"""
    name = models.CharField(max_length=100, unique=True, verbose_name='部门名称')
    # code 以字符串形式存放连续编号，例如 '1', '2', '3'
    code = models.CharField(max_length=50, null=True, blank=True, unique=True, verbose_name='部门编码')
    description = models.TextField(null=True, blank=True, verbose_name='描述')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')

    class Meta:
        db_table = 'departments'
        verbose_name = '部门'
        verbose_name_plural = '部门'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """在保存前确保 `code` 为连续自增的字符串编号。

        实现：使用单行计数器 `DepartmentCodeCounter` 在事务内自增并取值，
        将该数值作为字符串写入 `code` 字段，保证连续编号（事务回滚会回退）。
        """
        # 如果前端已经显式提供 code（非空），保留并直接保存（不过我们建议前端留空）
        if self.code:
            # 规范化为纯数字字符串（如果用户传入非数字则保留原样）
            try:
                # 如果能转为 int，则写成数字字符串形式
                int_val = int(str(self.code))
                self.code = str(int_val)
            except Exception:
                # 保持用户提供的值
                pass
            super().save(*args, **kwargs)
            return

        # 若 code 为空，使用计数器生成连续数字
        from django.apps import apps
        from django.db import transaction as dj_transaction

        DepartmentCodeCounter = apps.get_model('users', 'DepartmentCodeCounter')
        with dj_transaction.atomic():
            counter_qs = DepartmentCodeCounter.objects.select_for_update()
            counter = counter_qs.first()
            if not counter:
                counter = DepartmentCodeCounter.objects.create(value=0)
            counter.value = counter.value + 1
            counter.save()

            # assign and save
            self.code = str(counter.value)
            super().save(*args, **kwargs)


class DepartmentCodeCounter(models.Model):
    """单行计数器表，用于生成连续的部门编号（数字）。"""
    value = models.BigIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'department_code_counter'
        verbose_name = '部门编号计数器'
        verbose_name_plural = '部门编号计数器'