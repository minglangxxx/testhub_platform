<template>
  <div class="department-manage page-wrapper">
    <div class="page-header">
      <h2>部门与用户管理</h2>
      <p class="subtitle">在此处管理组织结构与用户，支持多部门隶属与权限分配</p>
    </div>

    <div class="content-card">
      <div class="card-body">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup>
// 组件现在通过路由的子路由渲染 DepartmentList / DepartmentUserList
</script>

<style scoped>
.department-manage {
  padding: 20px;
}

.page-header {
  margin-bottom: 16px;
}

.page-header h2 {
  margin: 0 0 6px 0;
  font-size: 20px;
}

.page-header .subtitle {
  color: #6b7280;
  margin: 0 0 12px 0;
}

.content-card {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

.card-body {
  padding: 8px 0;
}

.department-tabs :deep(.el-tabs__nav) {
  background: #fafafa;
  padding: 12px;
}

.department-tabs :deep(.el-tab-pane) {
  padding: 12px;
}
</style>
