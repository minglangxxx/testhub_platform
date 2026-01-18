<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">测试用例</h1>
      <div class="header-actions">
        <el-button 
          v-if="selectedTestCases.length > 0" 
          type="danger" 
          @click="batchDeleteTestCases"
          :disabled="isDeleting">
          <el-icon><Delete /></el-icon>
          批量删除 ({{ selectedTestCases.length }})
        </el-button>
        <el-button type="success" @click="exportToExcel">
          <el-icon><Download /></el-icon>
          导出Excel
        </el-button>
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon>
          新建用例
        </el-button>
      </div>
    </div>
    
    <div class="card-container">
      <el-container class="content-container">
        <!-- 左侧项目/版本树 -->
        <el-aside width="280px" class="tree-sidebar">
          <div class="sidebar-header">
            <h3>项目与版本</h3>
            <el-button 
              v-if="selectedProjectId || selectedVersionId" 
              size="small" 
              text 
              @click="clearSelection">
              清除筛选
            </el-button>
          </div>
          <div class="tree-container">
            <el-tree
              ref="treeRef"
              :data="treeData"
              :props="treeProps"
              node-key="id"
              :highlight-current="true"
              :expand-on-click-node="false"
              @node-click="handleTreeNodeClick"
              v-loading="treeLoading"
            >
              <template #default="{ node, data }">
                <div class="tree-node-content">
                  <el-icon v-if="data.type === 'project'" class="node-icon">
                    <Folder />
                  </el-icon>
                  <el-icon v-else class="node-icon version-icon">
                    <Document />
                  </el-icon>
                  <span class="node-label">{{ node.label }}</span>
                  <el-tag 
                    v-if="data.type === 'version' && data.is_baseline" 
                    size="small" 
                    type="warning"
                    class="baseline-tag"
                  >
                    基线
                  </el-tag>
                </div>
              </template>
            </el-tree>
          </div>
        </el-aside>

        <!-- 右侧用例列表 -->
        <el-main class="main-content">
          <div class="filter-bar">
            <el-row :gutter="20">
              <el-col :span="8">
                <el-input
                  v-model="searchText"
                  placeholder="搜索用例标题"
                  clearable
                  @input="handleSearch"
                >
                  <template #prefix>
                    <el-icon><Search /></el-icon>
                  </template>
                </el-input>
              </el-col>
              <el-col :span="5">
                <el-select v-model="priorityFilter" placeholder="优先级筛选" clearable @change="handleFilter">
                  <el-option label="低" value="low" />
                  <el-option label="中" value="medium" />
                  <el-option label="高" value="high" />
                  <el-option label="紧急" value="critical" />
                </el-select>
              </el-col>
              <el-col :span="5">
                <el-select v-model="statusFilter" placeholder="状态筛选" clearable @change="handleFilter">
                  <el-option label="草稿" value="draft" />
                  <el-option label="激活" value="active" />
                  <el-option label="废弃" value="deprecated" />
                </el-select>
              </el-col>
            </el-row>
            <div v-if="selectedProjectId || selectedVersionId" class="filter-info">
              <el-alert
                :title="getFilterInfoText()"
                type="info"
                :closable="false"
              />
            </div>
          </div>
          
          <el-table 
            :data="testcases" 
            v-loading="loading" 
            style="width: 100%"
            @selection-change="handleSelectionChange">
            <el-table-column type="selection" width="55" />
            <el-table-column type="index" label="序号" width="80" :index="getSerialNumber" />
            <el-table-column prop="title" label="用例标题" min-width="250">
              <template #default="{ row }">
                <el-link @click="goToTestCase(row.id)" type="primary">
                  {{ row.title }}
                </el-link>
              </template>
            </el-table-column>
            <el-table-column prop="project.name" label="关联项目" width="150">
              <template #default="{ row }">
                {{ row.project?.name || '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="versions" label="关联版本" width="200">
              <template #default="{ row }">
                <div v-if="row.versions && row.versions.length > 0" class="version-tags">
                  <el-tag 
                    v-for="version in row.versions.slice(0, 2)" 
                    :key="version.id" 
                    size="small" 
                    :type="version.is_baseline ? 'warning' : 'info'"
                    class="version-tag"
                  >
                    {{ version.name }}
                  </el-tag>
                  <el-tooltip v-if="row.versions.length > 2" :content="getVersionsTooltip(row.versions)">
                    <el-tag size="small" type="info" class="version-tag">
                      +{{ row.versions.length - 2 }}
                    </el-tag>
                  </el-tooltip>
                </div>
                <span v-else class="no-version">未关联版本</span>
              </template>
            </el-table-column>
            <el-table-column prop="priority" label="优先级" width="100">
              <template #default="{ row }">
                <el-tag :class="`priority-tag ${row.priority}`">{{ getPriorityText(row.priority) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="test_type" label="测试类型" width="120">
              <template #default="{ row }">
                {{ getTypeText(row.test_type) }}
              </template>
            </el-table-column>
            <el-table-column prop="author.username" label="作者" width="120" />
            <el-table-column prop="created_at" label="创建时间" width="180">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="editTestCase(row)">编辑</el-button>
                <el-button size="small" type="danger" @click="deleteTestCase(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <div class="pagination-container">
            <el-pagination
              v-model:current-page="currentPage"
              :page-size="pageSize"
              :total="total"
              layout="total, prev, pager, next"
              @current-change="handlePageChange"
            />
          </div>
        </el-main>
      </el-container>
    </div>
    
    <!-- 创建用例对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      title="新建测试用例"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createFormRules"
        label-width="100px"
      >
        <el-form-item label="用例标题" prop="title">
          <el-input
            v-model="createForm.title"
            placeholder="请输入用例标题"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="归属项目" prop="project_id">
          <el-select
            v-model="createForm.project_id"
            placeholder="请选择项目"
            style="width: 100%"
            @change="handleProjectChange"
          >
            <el-option
              v-for="project in projects"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="关联版本" prop="version_ids">
          <el-select
            v-model="createForm.version_ids"
            placeholder="请选择关联版本"
            multiple
            style="width: 100%"
            :disabled="!createForm.project_id"
          >
            <el-option
              v-for="version in availableVersions"
              :key="version.id"
              :label="version.name + (version.is_baseline ? ' (基线)' : '')"
              :value="version.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="用例描述" prop="description">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入用例描述"
          />
        </el-form-item>
        
        <el-form-item label="前置条件" prop="preconditions">
          <el-input
            v-model="createForm.preconditions"
            type="textarea"
            :rows="2"
            placeholder="请输入前置条件"
          />
        </el-form-item>
        
        <el-form-item label="操作步骤" prop="steps">
          <el-input
            v-model="createForm.steps"
            type="textarea"
            :rows="3"
            placeholder="请输入操作步骤"
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="预期结果" prop="expected_result">
          <el-input
            v-model="createForm.expected_result"
            type="textarea"
            :rows="3"
            placeholder="请输入预期结果"
          />
        </el-form-item>
        
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="优先级" prop="priority">
              <el-select v-model="createForm.priority" style="width: 100%">
                <el-option label="低" value="low" />
                <el-option label="中" value="medium" />
                <el-option label="高" value="high" />
                <el-option label="紧急" value="critical" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="状态" prop="status">
              <el-select v-model="createForm.status" style="width: 100%">
                <el-option label="草稿" value="draft" />
                <el-option label="激活" value="active" />
                <el-option label="废弃" value="deprecated" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="测试类型" prop="test_type">
              <el-select v-model="createForm.test_type" style="width: 100%">
                <el-option label="功能测试" value="functional" />
                <el-option label="集成测试" value="integration" />
                <el-option label="API测试" value="api" />
                <el-option label="UI测试" value="ui" />
                <el-option label="性能测试" value="performance" />
                <el-option label="安全测试" value="security" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCreateForm" :loading="createLoading">
          确定创建
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Download, Delete, Folder, Document } from '@element-plus/icons-vue'
import api from '@/utils/api'
import dayjs from 'dayjs'
import * as XLSX from 'xlsx'

const router = useRouter()
const loading = ref(false)
const treeLoading = ref(false)
const testcases = ref([])
const projects = ref([])
const treeData = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchText = ref('')
const priorityFilter = ref('')
const statusFilter = ref('')
const selectedTestCases = ref([])
const isDeleting = ref(false)
const treeRef = ref(null)

// 新增：左侧树选中的项目和版本
const selectedProjectId = ref(null)
const selectedVersionId = ref(null)
const selectedProjectName = ref('')
const selectedVersionName = ref('')

// 创建用例对话框相关
const createDialogVisible = ref(false)
const createLoading = ref(false)
const createFormRef = ref(null)
const availableVersions = ref([])
const createForm = ref({
  title: '',
  description: '',
  preconditions: '',
  steps: '',
  expected_result: '',
  priority: 'medium',
  status: 'draft',
  test_type: 'functional',
  project_id: null,
  version_ids: []
})

// 表单验证规则
const createFormRules = {
  title: [
    { required: true, message: '请输入用例标题', trigger: 'blur' },
    { min: 1, max: 500, message: '标题长度在 1 到 500 个字符', trigger: 'blur' }
  ],
  project_id: [
    { required: true, message: '请选择归属项目', trigger: 'change' }
  ],
  steps: [
    { required: true, message: '请输入操作步骤', trigger: 'blur' },
    { min: 1, max: 1000, message: '操作步骤长度在 1 到 1000 个字符', trigger: 'blur' }
  ],
  expected_result: [
    { required: true, message: '请输入预期结果', trigger: 'blur' }
  ]
}

// 树形控件配置
const treeProps = {
  children: 'children',
  label: 'label'
}

// 获取过滤信息文本
const getFilterInfoText = () => {
  if (selectedVersionId.value) {
    return `当前筛选：${selectedProjectName.value} / ${selectedVersionName.value}`
  } else if (selectedProjectId.value) {
    return `当前筛选：${selectedProjectName.value} （所有版本）`
  }
  return ''
}

// 清除选择
const clearSelection = () => {
  selectedProjectId.value = null
  selectedVersionId.value = null
  selectedProjectName.value = ''
  selectedVersionName.value = ''
  if (treeRef.value) {
    treeRef.value.setCurrentKey(null)
  }
  currentPage.value = 1
  fetchTestCases()
}

// 打开创建对话框
const openCreateDialog = async () => {
  // 重置表单
  createForm.value = {
    title: '',
    description: '',
    preconditions: '',
    steps: '',
    expected_result: '',
    priority: 'medium',
    status: 'draft',
    test_type: 'functional',
    project_id: null,
    version_ids: []
  }
  
  // 根据左侧选择自动填充项目和版本
  if (selectedProjectId.value) {
    createForm.value.project_id = selectedProjectId.value
    
    // 加载该项目的版本列表
    await loadProjectVersions(selectedProjectId.value)
    
    // 如果选中了版本，也自动填充
    if (selectedVersionId.value) {
      createForm.value.version_ids = [selectedVersionId.value]
    }
  }
  
  createDialogVisible.value = true
  
  // 重置表单验证
  if (createFormRef.value) {
    createFormRef.value.clearValidate()
  }
}

// 处理项目变更
const handleProjectChange = async (projectId) => {
  createForm.value.version_ids = []
  availableVersions.value = []
  
  if (projectId) {
    await loadProjectVersions(projectId)
  }
}

// 加载指定项目的版本列表
const loadProjectVersions = async (projectId) => {
  try {
    const response = await api.get(`/versions/projects/${projectId}/versions/`)
    availableVersions.value = response.data || []
  } catch (error) {
    console.error('获取项目版本失败:', error)
    ElMessage.error('获取项目版本失败')
  }
}

// 提交创建表单
const submitCreateForm = async () => {
  if (!createFormRef.value) return
  
  await createFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    createLoading.value = true
    try {
      await api.post('/testcases/', createForm.value)
      ElMessage.success('测试用例创建成功')
      createDialogVisible.value = false
      
      // 刷新用例列表
      fetchTestCases()
    } catch (error) {
      console.error('创建测试用例失败:', error)
      ElMessage.error('创建测试用例失败: ' + (error.response?.data?.message || error.message || '未知错误'))
    } finally {
      createLoading.value = false
    }
  })
}

// 处理树节点点击
const handleTreeNodeClick = (data) => {
  if (data.type === 'project') {
    // 点击项目节点，按项目过滤
    selectedProjectId.value = data.projectId
    selectedVersionId.value = null
    selectedProjectName.value = data.label
    selectedVersionName.value = ''
  } else if (data.type === 'version') {
    // 点击版本节点，按项目和版本过滤
    selectedProjectId.value = data.projectId
    selectedVersionId.value = data.versionId
    selectedProjectName.value = data.projectName
    selectedVersionName.value = data.label
  }
  currentPage.value = 1
  fetchTestCases()
}

// 获取项目和版本的树形数据
const fetchProjectsAndVersions = async () => {
  treeLoading.value = true
  try {
    // 获取所有项目
    const projectsResponse = await api.get('/projects/')
    const allProjects = projectsResponse.data.results || projectsResponse.data || []
    projects.value = allProjects

    // 构建树形数据
    const tree = []
    for (const project of allProjects) {
      const projectNode = {
        id: `project-${project.id}`,
        label: project.name,
        type: 'project',
        projectId: project.id,
        children: []
      }

      // 获取该项目的版本列表
      try {
        const versionsResponse = await api.get(`/versions/projects/${project.id}/versions/`)
        const versions = versionsResponse.data || []
        
        projectNode.children = versions.map(version => ({
          id: `version-${version.id}`,
          label: version.name,
          type: 'version',
          projectId: project.id,
          projectName: project.name,
          versionId: version.id,
          is_baseline: version.is_baseline
        }))
      } catch (error) {
        console.error(`获取项目 ${project.name} 的版本失败:`, error)
      }

      tree.push(projectNode)
    }

    treeData.value = tree
  } catch (error) {
    ElMessage.error('获取项目列表失败')
  } finally {
    treeLoading.value = false
  }
}

const fetchTestCases = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      search: searchText.value,
      priority: priorityFilter.value,
      status: statusFilter.value
    }
    
    // 根据左侧选择添加过滤参数
    if (selectedVersionId.value) {
      // 如果选择了版本，同时传递项目和版本参数
      params.project = selectedProjectId.value
      params.version = selectedVersionId.value
      console.log('按版本筛选:', {
        projectId: selectedProjectId.value,
        projectName: selectedProjectName.value,
        versionId: selectedVersionId.value,
        versionName: selectedVersionName.value
      })
    } else if (selectedProjectId.value) {
      // 如果只选择了项目，只传递项目参数
      params.project = selectedProjectId.value
      console.log('按项目筛选:', {
        projectId: selectedProjectId.value,
        projectName: selectedProjectName.value
      })
    }

    console.log('API 请求参数:', params)
    const response = await api.get('/testcases/', { params })
    testcases.value = response.data.results || []
    total.value = response.data.count || 0
    console.log('获取到的用例数量:', testcases.value.length)
  } catch (error) {
    ElMessage.error('获取测试用例列表失败')
    console.error('获取测试用例失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchTestCases()
}

const handleFilter = () => {
  currentPage.value = 1
  fetchTestCases()
}

const handlePageChange = () => {
  fetchTestCases()
}

const goToTestCase = (id) => {
  router.push(`/ai-generation/testcases/${id}`)
}

const editTestCase = (testcase) => {
  router.push(`/ai-generation/testcases/${testcase.id}/edit`)
}

const deleteTestCase = async (testcase) => {
  try {
    await ElMessageBox.confirm('确定要删除这个测试用例吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.delete(`/testcases/${testcase.id}/`)
    ElMessage.success('测试用例删除成功')
    fetchTestCases()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('测试用例删除失败')
    }
  }
}

// 处理选择变化
const handleSelectionChange = (selection) => {
  selectedTestCases.value = selection
}

// 获取序号
const getSerialNumber = (index) => {
  return (currentPage.value - 1) * pageSize.value + index + 1
}

// 批量删除
const batchDeleteTestCases = async () => {
  if (selectedTestCases.value.length === 0) {
    ElMessage.warning('请先选择要删除的测试用例')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedTestCases.value.length} 个测试用例吗？此操作不可恢复。`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    isDeleting.value = true
    let successCount = 0
    let failCount = 0

    // 逐个删除选中的测试用例
    for (const testcase of selectedTestCases.value) {
      try {
        await api.delete(`/testcases/${testcase.id}/`)
        successCount++
      } catch (error) {
        console.error(`删除测试用例 ${testcase.id} 失败:`, error)
        failCount++
      }
    }

    // 显示删除结果
    if (successCount > 0) {
      ElMessage.success(`成功删除 ${successCount} 个测试用例${failCount > 0 ? `，${failCount} 个失败` : ''}`)
    } else {
      ElMessage.error('删除失败')
    }

    // 清空选择并重新加载列表
    selectedTestCases.value = []
    fetchTestCases()

  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error)
      ElMessage.error('批量删除失败: ' + (error.message || '未知错误'))
    }
  } finally {
    isDeleting.value = false
  }
}

const getPriorityText = (priority) => {
  const textMap = {
    low: '低',
    medium: '中',
    high: '高',
    critical: '紧急'
  }
  return textMap[priority] || priority
}

const getStatusType = (status) => {
  const typeMap = {
    draft: 'info',
    active: 'success',
    deprecated: 'warning'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = {
    draft: '草稿',
    active: '激活',
    deprecated: '废弃'
  }
  return textMap[status] || status
}

const getTypeText = (type) => {
  const textMap = {
    functional: '功能测试',
    integration: '集成测试',
    api: 'API测试',
    ui: 'UI测试',
    performance: '性能测试',
    security: '安全测试'
  }
  return textMap[type] || '-'
}

const formatDate = (dateString) => {
  return dayjs(dateString).format('YYYY-MM-DD HH:mm')
}

const getVersionsTooltip = (versions) => {
  return versions.map(v => v.name + (v.is_baseline ? ' (基线)' : '')).join('、')
}

// 将HTML的<br>标签转换为换行符（用于Excel导出）
const convertBrToNewline = (text) => {
  if (!text) return ''
  return text.replace(/<br\s*\/?>/gi, '\n')
}

const exportToExcel = async () => {
  try {
    loading.value = true
    
    // 获取所有测试用例数据（不分页）
    const params = {
      page_size: 9999, // 获取所有数据
      search: searchText.value,
      priority: priorityFilter.value,
      status: statusFilter.value
    }
    
    // 根据左侧选择添加过滤参数
    if (selectedVersionId.value) {
      params.project = selectedProjectId.value
      params.version = selectedVersionId.value
    } else if (selectedProjectId.value) {
      params.project = selectedProjectId.value
    }
    
    const response = await api.get('/testcases/', { params })
    
    const allTestCases = response.data.results || []
    
    if (allTestCases.length === 0) {
      ElMessage.warning('没有测试用例数据可导出')
      return
    }
    
    // 创建工作簿
    const workbook = XLSX.utils.book_new()
    
    // 准备Excel数据
    const worksheetData = [
      ['测试用例编号', '用例标题', '关联项目', '关联版本', '前置条件', '操作步骤', '预期结果', '优先级', '状态', '测试类型', '作者', '创建时间']
    ]
    
    allTestCases.forEach((testcase, index) => {
      const versions = testcase.versions && testcase.versions.length > 0 
        ? testcase.versions.map(v => v.name + (v.is_baseline ? '(基线)' : '')).join('、')
        : '未关联版本'
      
      worksheetData.push([
        `TC${String(index + 1).padStart(3, '0')}`,
        testcase.title || '',
        testcase.project?.name || '',
        versions,
        convertBrToNewline(testcase.preconditions || ''),
        convertBrToNewline(testcase.steps || ''),
        convertBrToNewline(testcase.expected_result || ''),
        getPriorityText(testcase.priority),
        getStatusText(testcase.status),
        getTypeText(testcase.test_type),
        testcase.author?.username || '',
        formatDate(testcase.created_at)
      ])
    })
    
    // 创建工作表
    const worksheet = XLSX.utils.aoa_to_sheet(worksheetData)
    
    // 设置列宽
    const colWidths = [
      { wch: 15 }, // 测试用例编号
      { wch: 30 }, // 用例标题
      { wch: 20 }, // 关联项目
      { wch: 25 }, // 关联版本
      { wch: 30 }, // 前置条件
      { wch: 40 }, // 操作步骤
      { wch: 30 }, // 预期结果
      { wch: 10 }, // 优先级
      { wch: 10 }, // 状态
      { wch: 15 }, // 测试类型
      { wch: 15 }, // 作者
      { wch: 20 }  // 创建时间
    ]
    worksheet['!cols'] = colWidths
    
    // 设置表头样式
    for (let col = 0; col < worksheetData[0].length; col++) {
      const cellAddress = XLSX.utils.encode_cell({ r: 0, c: col })
      if (!worksheet[cellAddress]) continue
      worksheet[cellAddress].s = {
        font: { bold: true },
        alignment: { horizontal: 'center', vertical: 'center', wrapText: true }
      }
    }
    
    // 设置其他行的样式
    for (let row = 1; row < worksheetData.length; row++) {
      for (let col = 0; col < worksheetData[row].length; col++) {
        const cellAddress = XLSX.utils.encode_cell({ r: row, c: col })
        if (worksheet[cellAddress]) {
          worksheet[cellAddress].s = {
            alignment: { vertical: 'top', wrapText: true }
          }
        }
      }
    }
    
    // 添加工作表到工作簿
    XLSX.utils.book_append_sheet(workbook, worksheet, '测试用例')
    
    // 生成文件名
    const fileName = `测试用例_${new Date().toISOString().slice(0, 10)}.xlsx`
    
    // 导出文件
    XLSX.writeFile(workbook, fileName)
    
    ElMessage.success('测试用例导出成功')
  } catch (error) {
    console.error('导出测试用例失败:', error)
    ElMessage.error('导出测试用例失败: ' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const fetchProjects = async () => {
  try {
    const response = await api.get('/projects/')
    projects.value = response.data.results || response.data || []
  } catch (error) {
    ElMessage.error('获取项目列表失败')
  }
}

onMounted(() => {
  fetchProjectsAndVersions()
  fetchTestCases()
})
</script>

<style lang="scss" scoped>
.content-container {
  height: calc(100vh - 200px);
  background: #fff;
  border-radius: 4px;
}

.tree-sidebar {
  border-right: 1px solid #e4e7ed;
  background: #fafafa;
  padding: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  
  .sidebar-header {
    padding: 16px;
    border-bottom: 1px solid #e4e7ed;
    background: #fff;
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    h3 {
      margin: 0;
      font-size: 14px;
      font-weight: 600;
      color: #303133;
    }
  }
  
  .tree-container {
    flex: 1;
    overflow-y: auto;
    padding: 8px;
    background: #fff;
  }
  
  .tree-node-content {
    display: flex;
    align-items: center;
    gap: 6px;
    flex: 1;
    padding-right: 8px;
    
    .node-icon {
      font-size: 16px;
      color: #409eff;
      
      &.version-icon {
        color: #909399;
      }
    }
    
    .node-label {
      flex: 1;
      font-size: 13px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    
    .baseline-tag {
      margin-left: auto;
    }
  }
}

.main-content {
  padding: 16px;
  overflow-y: auto;
}

.filter-bar {
  margin-bottom: 16px;
  
  .filter-info {
    margin-top: 12px;
  }
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.priority-tag {
  &.low { color: #67c23a; }
  &.medium { color: #e6a23c; }
  &.high { color: #f56c6c; }
  &.critical { color: #f56c6c; font-weight: bold; }
}

.version-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  
  .version-tag {
    margin: 0;
  }
}

.no-version {
  color: #909399;
  font-size: 12px;
  font-style: italic;
}
</style>