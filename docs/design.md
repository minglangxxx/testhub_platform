设计文档：RBAC 概念数据模型与接口（详述）

目标与前提:

使用纯 RBAC（角色-权限）模型。
admin 为全局 superuser（无需 project scope）。
其他角色（负责人、执行人）为 project-scoped，通过 UserRole 关联到 project_id。
后端 Django 负责最终鉴权；前端仅做体验控制。
用户信息或角色变更后，必须清除该用户当前 token，强制重新登录以刷新权限。
优先以 AI 生成用例 / 用例管理 / 评审管理 / 测试计划 / 测试报告 流程为试点。

一、数据模型（数据库表与字段变更）
说明：以下为概念表与字段，字段类型以 Django ORM 对应类型为参考（例如 ForeignKey, CharField, BooleanField, IntegerField, DateTimeField）。

Role 表（已有则扩展）
目的：定义角色类型与元信息。
必要字段：
id (PK)
name (string, unique) — 例如: "admin", "owner", "executor"（可多语言描述另加 display_name）
is_default (bool) — 是否为系统内置角色（可选）
is_superuser_role (bool) — 若 true 则视为 superuser（用于快速判断 admin）
description (string, optional)
created_at, updated_at (timestamps)
Permission 表（若已有权限表，需扩展粒度）
目的：以 resource:action 作为最小权限单元。
必要字段：
id (PK)
resource (string) — 如 project, testcase, plan, report, user, department, ai_generation 等
action (string) — 如 view, create, update, delete, publish, execute, assign 等
codename (string, unique) — 例如 testcase:generate 或 project:manage（建议形成 resource:action 格式）
is_global (bool) — 若 true 则表示该权限只能作为全局权限（平台级），默认 false（project scoped）
description, created_at, updated_at
RolePermission 表（Role ↔ Permission 多对多）
目的：把角色映射到可执行的权限集合。
必要字段：
id (PK)
role_id (FK -> Role)
permission_id (FK -> Permission)
created_at
UserRole 表（User ↔ Role 映射，含 scope）
目的：表示某个用户在某个 scope（project）下具有的角色。对 admin，project_id 可为 NULL（表示全局）。
必要字段：
id (PK)
user_id (FK -> User)
role_id (FK -> Role)
project_id (FK -> Project, nullable) — NULL 表示全局（仅 admin）；非 NULL 则为 project-scoped。
assigned_by (FK -> User, optional) — 记录分配者
assigned_at (datetime)
expires_at (datetime, optional) — 若需要临时角色支持（可选）
唯一约束： (user_id, role_id, project_id) 防止重复分配
Token版本或撤销表（用于强制登出）
方法 A（推荐） — Token 版本字段：
在 User 表新增字段：token_version (integer, default 0)。
JWT payload 内不存放完整权限，但可包含 token_version，或后端在验证时额外检查用户当前 token_version（取决于 JWT 策略）。
角色/权限变更时，token_version 自增，造成现有 token 失效（如果 token 验证包含该版本）。
方法 B — Token 黑名单 / 撤销表（若使用短寿命 Access Token + Refresh Token，也可直接撤销或删除 refresh tokens）：
RevokedToken 表记录已撤销的 token 标识（例如 jti），鉴权时检查是否被撤销。
在分配/撤销角色时，把相关用户的 active refresh tokens 标记为撤销，或记录一条 account-wide revoke marker 来拒绝旧 token。
注：选哪种策略参考后续Token 清理策略。设计应与现有认证策略兼容；

兼容与过渡考虑
若系统已有权限表或角色模型，应提供数据迁移脚本把旧映射平滑迁移至新结构。
对于已有的“组”或“部门”权限关系需要单独映射到 RolePermission 或 UserRole（视逻辑而定）。
二、API 端点（名称与 I/O 要点，均不包含实现代码）

说明：端点名称为建议，遵循 REST 风格并支持权限校验与审计友好响应。所有端点后端均进行最终权限校验；前端仅作体验优化。建议统一返回格式包含 code, message, data。

查询当前用户在 project 下的权限/角色摘要
路径（建议）：GET /api/v1/projects/{project_id}/auth/summary
输入：URL path project_id，Auth header（token）
输出（200）：{ roles: [ { role: "executor", assigned_by, assigned_at, project_id } ], permissions: [ "testcase:create", "plan:execute", ... ] }
说明：用于前端路由守卫与按钮显隐。后端返回真实权限集合（合并 global 与 project-scoped 权限）。
列出所有可用 Role（及其描述）
路径：GET /api/v1/roles
输入：Auth
输出：[{ id, name, display_name, is_superuser_role, description }]
列出或查询 Permission 列表（带过滤）
路径：GET /api/v1/permissions?is_global=true|false&resource=testcase
输入：可选 query filters
输出：[{ id, codename, resource, action, is_global, description }]
查询某用户在项目下的 Role 映射（管理员/负责人查看用）
路径：GET /api/v1/projects/{project_id}/users/{user_id}/roles
输入：path project_id, user_id
输出：[{ role_id, role_name, assigned_by, assigned_at }]
分配角色（关键接口，带权限校验）
路径：POST /api/v1/projects/{project_id}/roles/assign
输入（body）：{ "user_id": <int>, "role_id": <int> }
备注：若分配 global role（如 admin），则 project_id 可为 null 或由不同 endpoint 处理（如 /api/v1/users/{user_id}/roles/assign-global）。
成功输出（200/201）：{ "status": "ok", "message": "role assigned", "data": { user_role_id } }
错误输出：403（无权分配），400（参数不全）
权限校验规则（后端）：调用者必须为 admin（global）或在 path project_id 上为负责人（owner）才允许为该 project 分配角色；若调用者试图跨项目操作且非 admin，则返回 403。
撤销角色
路径：POST /api/v1/projects/{project_id}/roles/revoke
输入（body）：{ "user_id": <int>, "role_id": <int> }
行为：删除 UserRole 对应记录并触发 token 清理逻辑。
输出 / 错误类似分配接口。
批量分配/批量撤销（可选）
路径：POST /api/v1/projects/{project_id}/roles/batch_assign 或 /batch_revoke
输入：{ "items": [ { "user_id": x, "role_id": y }, ... ] }
输出：详列成功/失败项，便于前端显示。
查询某 Role 的 Permission 集合（管理员用来编辑角色权限）
路径：GET /api/v1/roles/{role_id}/permissions
输出：{ role_id, permissions: [ codename, resource, action ] }
更新 Role ↔ Permission 映射（仅 admin 可操作）
路径：PUT /api/v1/roles/{role_id}/permissions
输入：{ "permission_ids": [1,2,3] }
输出：更新后的权限集合。注：若系统约定 admin 为 superuser，则应限制对此操作的影响或强行包含 superuser 标志。
Token / 会话管理接口（配合 token 清理策略）
方案 A（token_version）不需要单独端点；后端在角色变更处更新 User.token_version。
方案 B（refresh token 撤销）需接口：POST /api/v1/auth/revoke_tokens — 输入 { "user_id": x }（仅 admin 或 指定权限可调用），作用为撤销该用户的 refresh tokens 并在响应中指示前端强制登出。
输出：{ status, revoked_count }
审计 / 日志接口（可选但建议）
路径：GET /api/v1/audit/role_changes?user_id=&project_id=&since=
输出：角色变更记录（assign/revoke/actor/timestamp），便于事后审计（即使当前不考虑复杂审计，也建议保留基本表记录）。
三、Token 清理策略（步骤与注意事项）

方案 ：Refresh Token 撤销 / Token 黑名单（若使用 Simple JWT 或类似）

记录每个发出的 refresh token 的唯一 jti（或 token id）到 RefreshToken 表，标注为有效。
在角色变更时，把该用户的 active refresh tokens 全部标记为 revoked（或插入一条全局撤销记录）。
Access Token 的有效期应尽可能短（比如几分钟），使得撤销 refresh token 后用户必须重新登录以获取新的 access token。
对于已发放的 access token（短期），可选择不做额外撤销，依赖其短期过期与 refresh token 的撤销来强制登出。
后端在 refresh 流程或需要验证时检查 token 是否在 revoked 列表中。
优点：对现有无 token_version 的实现兼容；可更精细撤销单个 token。
缺点：需要存储 token 列表/黑名单，且随时间增长需要清理；access token 仍在有效期内可能短时间内仍能访问。

推荐策略：系统已使用 Simple JWT（常见于 Django），优先采用 Refresh Token 撤销结合短期 Access Token 的方式；可在认证验证流程中增加 DB 查询，token_version 方案更简单且更容易实现对“全部用户失效”的需求（例如在角色变更时对单用户做全量失效）。

四、权限校验流程（抽象步骤）

每次 API 调用的后端处理顺序（抽象）：

验证 token 有效性（签名 + 未过期）。
若使用 token_version：比较 token_version；若不匹配返回 401 并指示重登录。
解析请求意图：确定目标资源与动作（例如资源 testcase，action create），并提取可能的 project_id（从 path 或 body）。如若无法确定 project_id 且权限不是 global，则返回 400/403。
若 user 是 superuser（由 Role.is_superuser_role 或 UserRole with NULL project and admin role 判断），直接允许。
否则查找 UserRole 在 project_id 上的角色集合，合并这些角色对应的 RolePermission，判断所需 permission (resource:action) 是否在集合内。
若存在则允许；否则返回 403 权限不足。
分配操作权限判断（assign/revoke）：

若调用者为 admin（global），允许对任意 project 操作。
若调用者为负责人（owner）且其 UserRole 包含该 project，则允许对该 project 内的用户进行 assign/revoke（仅限 project 范围）。
禁止负责人跨项目分配。若尝试跨项目操作，返回 403。
五、对现有功能的影响评估与兼容计划

影响点：
对所有后端 API 添加或确保存在最终授权检查，会影响性能（额外查询），需做索引与缓存优化（例如缓存用户在某项目的权限摘要若频繁读取）。
若当前前端依赖 token 内嵌大量权限以决定 UI，需改为调用权限摘要 API 或依赖后端在 token 中仅给少量标识符。
数据库迁移：新增表与字段需谨慎执行，并准备回滚脚本。
向后兼容策略：
不需要前后版本或者新旧数据库兼容，现在版本还未发布，属于开发阶段，开发人员直接更新数据库表即可。
六、关键约束与注意事项

必须确保后端为最终授权决策点，前端不能信任。
对于 project_id 的解析：所有需要 project-scoped 授权的 API 必须在请求中明确定义 project_id（path param 或 body 字段），否则后端应拒绝或要求额外确认。
对 is_global 权限（平台级）需在 Permission 定义中明确标注，避免错误地赋为 project-scoped。示例：configuration:ai_model 必须为 is_global=true 且只有 admin 能修改。
角色继承：业务上 admin 包含 owner 与 executor 权限；owner 包含 executor 权限。实现方式：在数据层显式把包含的权限写入 higher-role 的 RolePermission（不要依赖隐式继承逻辑以便查询时简单）。
Token 清理后的用户体验：在 token 被清理后，用户当前页面应尽可能优雅地提示需要重新登录并保存未提交数据（前端需做相应提示）。
审计：即使当前不实现复杂审计，也建议记录最少的角色变更日志（assigner, assignee, role, project, timestamp）以便追踪误操作。
安全：权限分配接口必须对调用者权限严格校验，避免水平越权（负责人对非本项目用户误赋权）与垂直越权（普通用户通过 API 提升自身或他人角色）。
不确定项（需产品确认或进一步决策）：
不允许临时角色（expires_at）场景
token 机制选择：走 refresh-token 撤销方案。
不允许 Role 动态定义，内部技术人员使用平台，权限粒度不用太细，所以不需要动态定义角色。