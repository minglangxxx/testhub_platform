<template>
  <div class="department-list">
    <div class="action-bar">
      <div class="left-actions">
        <el-input 
          v-model="searchQuery" 
          placeholder="搜索部门名称/编码" 
          clearable
          @input="handleSearch"
          style="width:300px"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
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
          新建部门
        </el-button>
      </div>
    </div>

    <el-table 
      :data="departments" 
      v-loading="loading"
      @selection-change="handleSelectionChange"
      style="width:100%; margin-top:16px"
    >
      <el-table-column type="selection" width="55" />
      <el-table-column type="index" label="序号" width="80" />
      <el-table-column prop="name" label="部门名称" min-width="150" />
      <el-table-column prop="code" label="部门编码" min-width="120" />
      <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
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
      :title="form.id ? '编辑部门' : '新建部门'"
      width="500px"
    >
      <el-form :model="form" label-width="80px">
        <el-form-item label="部门名称" required>
          <el-input v-model="form.name" placeholder="请输入部门名称" />
        </el-form-item>
        <el-form-item label="部门编码">
          <el-input v-model="form.code" placeholder="系统自动生成" disabled />
        </el-form-item>
        <el-form-item label="描述">
          <el-input 
            v-model="form.description" 
            type="textarea" 
            :rows="3"
            placeholder="请输入部门描述（可选）" 
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

const departments = ref([])
const searchQuery = ref('')
const showDialog = ref(false)
const form = ref({ id: null, name: '', code: '', description: '' })
const loading = ref(false)
const isSaving = ref(false)
const isDeleting = ref(false)
const selectedRows = ref([])

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const load = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
      search: searchQuery.value || undefined
    }
    const res = await axios.get('/api/users/departments/', { params })
    departments.value = res.data.results || res.data
    total.value = res.data.count || departments.value.length
  } catch (error) {
    ElMessage.error('加载部门列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
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
  form.value = { id: null, name: '', code: '', description: '' }
  showDialog.value = true
}

const edit = (row) => {
  form.value = { ...row }
  showDialog.value = true
}

const save = async () => {
  if (!form.value.name?.trim()) {
    ElMessage.warning('请输入部门名称')
    return
  }
  
  isSaving.value = true
  try {
    if (form.value.id) {
      await axios.put(`/api/users/departments/${form.value.id}/`, form.value)
      ElMessage.success('更新成功')
    } else {
      await axios.post('/api/users/departments/', form.value)
      ElMessage.success('创建成功')
    }
    showDialog.value = false
    await load()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    isSaving.value = false
  }
}

const remove = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除部门"${row.name}"吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await axios.delete(`/api/users/departments/${row.id}/`)
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
      `确定要删除选中的 ${selectedRows.value.length} 个部门吗？此操作不可恢复。`,
      '批量删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    isDeleting.value = true
    const ids = selectedRows.value.map(r => r.id)
    await axios.post('/api/users/departments/batch-delete/', { ids })
    ElMessage.success(`成功删除 ${ids.length} 个部门`)
    selectedRows.value = []
    await load()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  } finally {
    isDeleting.value = false
  }
}

const exportToExcel = () => {
  if (departments.value.length === 0) {
    ElMessage.warning('暂无数据可导出')
    return
  }
  
  const data = departments.value.map((d, index) => ({
    '序号': index + 1,
    '部门名称': d.name,
    '部门编码': d.code || '',
    '描述': d.description || '',
    '创建时间': d.created_at
  }))
  
  const ws = XLSX.utils.json_to_sheet(data)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, '部门列表')
  XLSX.writeFile(wb, `部门列表_${new Date().toLocaleDateString()}.xlsx`)
  ElMessage.success('导出成功')
}

onMounted(load)
</script>

<style scoped>
.department-list {
  padding: 0;
}

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.left-actions, .right-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}
</style>
