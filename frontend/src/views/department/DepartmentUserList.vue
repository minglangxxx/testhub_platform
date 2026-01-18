<template>
  <div class="user-list">
    <div class="action-bar">
      <div class="left-actions">
        <el-input 
          v-model="searchQuery" 
          placeholder="搜索用户名/邮箱/手机号" 
          clearable
          @input="handleSearch"
          style="width:300px"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select 
          v-model="departmentFilter" 
          placeholder="按部门筛选" 
          clearable
          @change="handleFilter"
          style="width:200px"
        >
          <el-option 
            v-for="d in departments" 
            :key="d.id" 
            :label="d.name" 
            :value="d.id" 
          />
        </el-select>
        <el-select 
          v-model="statusFilter" 
          placeholder="按状态筛选" 
          clearable
          @change="handleFilter"
          style="width:120px"
        >
          <el-option label="激活" :value="true" />
          <el-option label="禁用" :value="false" />
        </el-select>
      </div>
      <div class="right-actions">
        <el-button 
          v-if="selectedRows.length > 0" 
          type="danger" 
          @click="batchDelete"
          :disabled="isDeleting"
        >
          <el-icon><Delete /></el-icon>
          批量删除 ({{ selectedRows.length }})
        </el-button>
        <el-button type="success" @click="exportToExcel">
          <el-icon><Download /></el-icon>
          导出Excel
        </el-button>
        <el-button type="primary" @click="openCreate">
          <el-icon><Plus /></el-icon>
          新建用户
        </el-button>
      </div>
    </div>

    <el-table 
      :data="users" 
      v-loading="loading"
      @selection-change="handleSelectionChange"
      style="width:100%; margin-top:16px"
    >
      <el-table-column type="selection" width="55" />
      <el-table-column type="index" label="序号" width="80" />
      <el-table-column prop="username" label="用户名" min-width="120" />
      <el-table-column prop="email" label="邮箱" min-width="180" />
      <el-table-column prop="phone" label="手机号" min-width="120" />
      <el-table-column label="部门" min-width="200">
        <template #default="{ row }">
          <el-tag 
            v-for="dept in row.department_display" 
            :key="dept.id" 
            size="small"
            style="margin-right:4px"
          >
            {{ dept.name }}
          </el-tag>
          <span v-if="!row.department_display || row.department_display.length === 0" class="text-muted">
            未分配
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="position" label="职位" min-width="120" />
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
            {{ row.is_active ? '激活' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" min-width="160" />
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link size="small" @click="edit(row)">
            <el-icon><Edit /></el-icon>
            编辑
          </el-button>
          <el-button type="danger" link size="small" @click="remove(row)">
            <el-icon><Delete /></el-icon>
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-if="total > 0"
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      :total="total"
      :page-sizes="[10, 20, 50, 100]"
      layout="total, sizes, prev, pager, next, jumper"
      @size-change="handlePageSizeChange"
      @current-change="handlePageChange"
      style="margin-top:16px; justify-content:flex-end"
    />

    <el-dialog 
      v-model="showDialog" 
      :title="form.id ? '编辑用户' : '新建用户'"
      width="600px"
    >
      <el-form :model="form" label-width="90px">
        <el-form-item label="用户名" required>
          <el-input v-model="form.username" placeholder="请输入用户名" :disabled="!!form.id" />
        </el-form-item>
        <el-form-item label="邮箱" required>
          <el-input v-model="form.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="form.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="姓" v-if="!form.id">
          <el-input v-model="form.last_name" placeholder="请输入姓" />
        </el-form-item>
        <el-form-item label="名" v-if="!form.id">
          <el-input v-model="form.first_name" placeholder="请输入名" />
        </el-form-item>
        <el-form-item label="职位">
          <el-input v-model="form.position" placeholder="请输入职位" />
        </el-form-item>
        <el-form-item label="部门">
          <el-select 
            v-model="form.department" 
            multiple 
            placeholder="选择部门（可多选）" 
            style="width:100%"
          >
            <el-option 
              v-for="d in departments" 
              :key="d.id" 
              :label="d.name" 
              :value="d.id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.is_active" active-text="激活" inactive-text="禁用" />
        </el-form-item>
        <el-form-item label="密码" v-if="!form.id" required>
          <el-input 
            v-model="form.password" 
            type="password" 
            placeholder="请输入密码（至少6位）" 
            show-password 
          />
        </el-form-item>
        <el-form-item label="确认密码" v-if="!form.id" required>
          <el-input 
            v-model="form.password_confirm" 
            type="password" 
            placeholder="请再次输入密码" 
            show-password 
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="save" :loading="isSaving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Edit, Delete, Download } from '@element-plus/icons-vue'
import axios from 'axios'
import * as XLSX from 'xlsx'

const users = ref([])
const departments = ref([])
const searchQuery = ref('')
const departmentFilter = ref(null)
const statusFilter = ref(null)
const showDialog = ref(false)
const form = ref({ 
  id: null, 
  username: '', 
  email: '', 
  phone: '', 
  first_name: '',
  last_name: '',
  position: '',
  department: [],
  is_active: true,
  password: '',
  password_confirm: ''
})
const loading = ref(false)
const isSaving = ref(false)
const isDeleting = ref(false)
const selectedRows = ref([])

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const loadDepartments = async () => {
  try {
    const res = await axios.get('/api/users/departments/', { 
      params: { page_size: 1000 } 
    })
    departments.value = res.data.results || res.data
  } catch (error) {
    console.error('加载部门列表失败', error)
  }
}

const load = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
      search: searchQuery.value || undefined,
      department: departmentFilter.value || undefined,
      is_active: statusFilter.value !== null ? statusFilter.value : undefined
    }
    const res = await axios.get('/api/users/users/', { params })
    users.value = res.data.results || res.data
    total.value = res.data.count || users.value.length
  } catch (error) {
    ElMessage.error('加载用户列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  load()
}

const handleFilter = () => {
  currentPage.value = 1
  load()
}

const handleSelectionChange = (selection) => {
  selectedRows.value = selection
}

const handlePageChange = () => {
  load()
}

const handlePageSizeChange = () => {
  currentPage.value = 1
  load()
}

const openCreate = () => {
  form.value = { 
    id: null, 
    username: '', 
    email: '', 
    phone: '',
    first_name: '',
    last_name: '',
    position: '',
    department: [],
    is_active: true,
    password: '',
    password_confirm: ''
  }
  showDialog.value = true
}

const edit = (row) => {
  // 将后端返回的 department_display 转换为 id 数组
  const departmentIds = row.department_display?.map(d => d.id) || []
  form.value = { 
    ...row,
    department: departmentIds,
    password: '',
    password_confirm: ''
  }
  showDialog.value = true
}

const save = async () => {
  // 验证必填字段
  if (!form.value.username?.trim()) {
    ElMessage.warning('请输入用户名')
    return
  }
  if (!form.value.email?.trim()) {
    ElMessage.warning('请输入邮箱')
    return
  }
  if (!form.value.id) {
    // 新建用户时验证密码
    if (!form.value.password || form.value.password.length < 6) {
      ElMessage.warning('密码至少6位')
      return
    }
    if (form.value.password !== form.value.password_confirm) {
      ElMessage.warning('两次输入的密码不一致')
      return
    }
  }
  
  isSaving.value = true
  try {
    if (form.value.id) {
      // 编辑用户：不发送密码字段
      const updateData = { ...form.value }
      delete updateData.password
      delete updateData.password_confirm
      delete updateData.department_display
      await axios.put(`/api/users/users/${form.value.id}/`, updateData)
      ElMessage.success('更新成功')
    } else {
      // 新建用户
      await axios.post('/api/users/users/', form.value)
      ElMessage.success('创建成功')
    }
    showDialog.value = false
    await load()
  } catch (error) {
    const msg = error.response?.data?.username?.[0] || 
                error.response?.data?.email?.[0] || 
                error.response?.data?.detail || 
                '保存失败'
    ElMessage.error(msg)
  } finally {
    isSaving.value = false
  }
}

const remove = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户"${row.username}"吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await axios.delete(`/api/users/users/${row.id}/`)
    ElMessage.success('删除成功')
    await load()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const batchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedRows.value.length} 个用户吗？此操作不可恢复。`,
      '批量删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    isDeleting.value = true
    const ids = selectedRows.value.map(r => r.id)
    await axios.post('/api/users/users/batch-delete/', { ids })
    ElMessage.success(`成功删除 ${ids.length} 个用户`)
    selectedRows.value = []
    await load()
  } catch (error) {
    if (error !== 'cancel') {
      const msg = error.response?.data?.error || '批量删除失败'
      ElMessage.error(msg)
    }
  } finally {
    isDeleting.value = false
  }
}

const exportToExcel = () => {
  if (users.value.length === 0) {
    ElMessage.warning('暂无数据可导出')
    return
  }
  
  const data = users.value.map((u, index) => ({
    '序号': index + 1,
    '用户名': u.username,
    '邮箱': u.email,
    '手机号': u.phone || '',
    '职位': u.position || '',
    '部门': u.department_display?.map(d => d.name).join(', ') || '',
    '状态': u.is_active ? '激活' : '禁用',
    '创建时间': u.created_at
  }))
  
  const ws = XLSX.utils.json_to_sheet(data)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, '用户列表')
  XLSX.writeFile(wb, `用户列表_${new Date().toLocaleDateString()}.xlsx`)
  ElMessage.success('导出成功')
}

onMounted(() => {
  loadDepartments()
  load()
})
</script>

<style scoped>
.user-list {
  padding: 0;
}

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}

.left-actions, .right-actions {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.text-muted {
  color: #909399;
  font-size: 12px;
}
</style>
