<template>
  <div class="department-manage page-wrapper">
    <div class="page-header">
      <h2>部门与用户管理</h2>
      <p class="subtitle">在此处管理组织结构与用户，支持多部门隶属与权限分配</p>
    </div>

    <div class="content-card">
      <el-tabs v-model="active" tab-position="left" class="department-tabs">
        <el-tab-pane label="部门管理" name="departments">
          <div class="card-body">
            <DepartmentList />
          </div>
        </el-tab-pane>
        <el-tab-pane label="用户管理" name="users">
          <div class="card-body">
            <DepartmentUserList />
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import DepartmentList from '@/views/department/DepartmentList.vue'
import DepartmentUserList from '@/views/department/DepartmentUserList.vue'

const active = ref('departments')

const handleSelect = (index) => {
  active.value = index
}
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
