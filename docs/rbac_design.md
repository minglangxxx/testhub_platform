RBAC 设计文档

概述
- 使用纯 RBAC（Role-Based Access Control）模型：Role / Permission / RolePermission / UserRole
- `admin` 为全局 superuser，其他角色为 project-scoped（project_id）
- 变更角色后通过 `token_version` 或 refresh-token 撤销策略强制用户重新登录

一、数据模型
1. Role
- id, name, display_name, is_superuser_role, description, created_at

2. Permission
- id, resource, action, codename (resource:action), is_global, description

3. RolePermission
- id, role_id, permission_id, created_at

4. UserRole
- id, user_id, role_id, project_id (nullable, null 表示 global), assigned_by, assigned_at, expires_at

5. User.token_version
- integer 字段，变更时自增以使 token 失效

二、主要 API
- GET /api/v1/roles
- GET /api/v1/permissions
- GET /api/v1/projects/{project_id}/auth/summary
- POST /api/v1/projects/{project_id}/roles/assign
- POST /api/v1/projects/{project_id}/roles/revoke
- POST /api/v1/roles/assign  (global)
- POST /api/v1/roles/revoke  (global)

三、迁移步骤（高层）
1. 在开发/测试环境生成并应用迁移：
   python manage.py makemigrations apps.users
   python manage.py migrate
2. 创建基础数据：插入默认 Role（admin, owner, executor）以及必要 Permission 初始集
3. 运行集成测试验证 API 行为
4. 部署到生产窗口执行迁移，监控 DB 与应用日志

回滚策略
- 在生产执行迁移前备份数据库快照
- 若发现问题，使用备份恢复或运行反向迁移（python manage.py migrate apps.users <previous_migration>)

四、验收测试 Checklist
- 能够列出 Role 与 Permission
- 能够在 project 内给用户分配/撤销 role，且非管理员不能跨项目分配
- 角色变更后，目标用户旧 token 无法继续访问需要权限的 API
- 前端调用 /projects/{project_id}/auth/summary 能返回正确权限集合
- 所有新 API 返回格式与错误码符合现有系统标准

五、注意事项
- 敏感字段（如密码、token 明文）不得记录在日志
- 所有输入必须进行类型校验
- 若使用 token_version 方案，请确保 token 在生成时包含该 claim 或在验证逻辑中查询 DB


文档末
