前端权限摘要与集成说明

目的
- 前端使用 /api/v1/projects/{project_id}/auth/summary 接口获取当前用户在指定 project 的角色与权限集合，用于路由守卫和按钮/组件显隐。

接口说明
- GET /api/v1/projects/{project_id}/auth/summary
  - 请求头：Authorization: Bearer <access_token>
  - 返回：{ roles: ["executor", "owner"], permissions: ["testcase:generate", "plan:execute", ...] }

前端使用建议
- 在用户登录成功后，首次进入项目页时调用一次该接口并缓存结果（可放入 Pinia store），用于路由守卫与页面渲染。
- 对于需要即时生效的权限变更（例如管理员在后台更改某用户权限），前端在收到 401 或特定错误（如 token_version_mismatch）时，清理本地缓存并重定向用户到登录页。
- 不要在前端做安全校验，只用于改善用户体验和减少无效请求。后端始终做最终权限判断。

示例（伪代码）
- 调用时机：进入项目详情页、打开需要权限的操作面板前
- 缓存策略：store.state.projectPermissions[projectId] = response.data
- 失效策略：当收到 401/token mismatch 或管理员提示权限变更时，清空该缓存并重新获取。

注意事项
- 接口返回顺序不可依赖，前端应把 permissions 转为 Set 以便快速判断。
- 为避免多次并发请求，前端应在请求进行中期间阻塞重复请求或复用进行中的 Promise。
