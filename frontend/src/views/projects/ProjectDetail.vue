<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">项目详情</h1>
      <el-button type="primary" @click="$router.back()">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
    </div>
    
    <div class="card-container">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="项目信息" name="info">
          <div v-if="project">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="项目名称">{{ project.name }}</el-descriptions-item>
              <el-descriptions-item label="项目状态">
                <el-tag :type="getStatusType(project.status)">{{ getStatusText(project.status) }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="负责人">{{ project.owner?.username }}</el-descriptions-item>
              <el-descriptions-item label="创建时间">{{ formatDate(project.created_at) }}</el-descriptions-item>
              <el-descriptions-item label="项目描述" :span="2">{{ project.description || '暂无描述' }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="项目成员" name="members">
          <div class="members-section">
            <el-button type="primary" @click="showAddMemberDialog = true">添加成员</el-button>
            <el-table :data="members" style="width: 100%; margin-top: 20px;">
              <el-table-column prop="username" label="用户名" />
              <el-table-column prop="email" label="邮箱" />
              <el-table-column prop="role" label="角色" />
              <el-table-column prop="joined_at" label="加入时间">
                <template #default="{ row }">
                  {{ formatDate(row.joined_at) }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="100">
                <template #default="{ row }">
                  <el-button size="small" type="danger" @click="removeMember(row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>

        <!-- 添加成员对话框 -->
        <el-dialog title="添加成员" v-model="showAddMemberDialog" width="500px">
          <el-form :model="newMember">
            <el-form-item label="用户ID" prop="user_id">
              <el-input v-model="newMember.user_id" placeholder="输入用户ID" />
            </el-form-item>
            <el-form-item label="角色" prop="role">
              <el-select v-model="newMember.role" placeholder="选择角色">
                <el-option label="成员" value="member" />
                <el-option label="管理员" value="admin" />
              </el-select>
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="showAddMemberDialog = false">取消</el-button>
            <el-button type="primary" @click="addMember">添加</el-button>
          </template>
        </el-dialog>
        
        <el-tab-pane label="环境配置" name="environments">
          <div class="environments-section">
            <el-button type="primary" @click="showAddEnvDialog = true">添加环境</el-button>
            <el-table :data="environments" style="width: 100%; margin-top: 20px;">
              <el-table-column prop="name" label="环境名称" />
              <el-table-column prop="base_url" label="基础URL" />
              <el-table-column prop="description" label="描述" />
              <el-table-column prop="is_default" label="默认环境">
                <template #default="{ row }">
                  <el-tag v-if="row.is_default" type="success">是</el-tag>
                  <span v-else>否</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>

        <!-- 添加环境对话框 -->
        <el-dialog title="添加环境" v-model="showAddEnvDialog" width="600px">
          <el-form :model="newEnv">
            <el-form-item label="环境名称" prop="name">
              <el-input v-model="newEnv.name" />
            </el-form-item>
            <el-form-item label="基础URL" prop="base_url">
              <el-input v-model="newEnv.base_url" />
            </el-form-item>
            <el-form-item label="描述" prop="description">
              <el-input type="textarea" v-model="newEnv.description" />
            </el-form-item>
            <el-form-item label="默认环境" prop="is_default">
              <el-switch v-model="newEnv.is_default" />
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="showAddEnvDialog = false">取消</el-button>
            <el-button type="primary" @click="addEnvironment">添加</el-button>
          </template>
        </el-dialog>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'
import dayjs from 'dayjs'

const route = useRoute()
const project = ref(null)
const members = ref([])
const environments = ref([])
const activeTab = ref('info')
const showAddMemberDialog = ref(false)
const showAddEnvDialog = ref(false)

const newMember = ref({ user_id: null, role: 'member' })
const newEnv = ref({ name: '', base_url: '', description: '', is_default: false })

const fetchProject = async () => {
  try {
    const response = await api.get(`/projects/${route.params.id}/`)
    project.value = response.data
    await fetchMembers()
    await fetchEnvironments()
  } catch (error) {
    ElMessage.error('获取项目详情失败')
  }
}

const getStatusType = (status) => {
  const typeMap = {
    active: 'success',
    paused: 'warning',
    completed: 'info',
    archived: 'info'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = {
    active: '进行中',
    paused: '已暂停',
    completed: '已完成',
    archived: '已归档'
  }
  return textMap[status] || status
}

const formatDate = (dateString) => {
  return dayjs(dateString).format('YYYY-MM-DD HH:mm')
}

const removeMember = async (member) => {
  try {
    await api.delete(`/projects/${route.params.id}/members/${member.id}/`)
    ElMessage.success('成员删除成功')
    await fetchMembers()
  } catch (error) {
    ElMessage.error('删除成员失败')
  }
}

const fetchMembers = async () => {
  try {
    const response = await api.get(`/projects/${route.params.id}/members/`)
    members.value = response.data
  } catch (error) {
    ElMessage.error('获取项目成员失败')
  }
}

const addMember = async () => {
  try {
    await api.post(`/projects/${route.params.id}/members/add/`, newMember.value)
    ElMessage.success('添加成员成功')
    showAddMemberDialog.value = false
    newMember.value = { user_id: null, role: 'member' }
    await fetchMembers()
  } catch (error) {
    ElMessage.error('添加成员失败')
  }
}

const fetchEnvironments = async () => {
  try {
    const response = await api.get(`/projects/${route.params.id}/environments/`)
    environments.value = response.data.results || response.data
  } catch (error) {
    ElMessage.error('获取环境列表失败')
  }
}

const addEnvironment = async () => {
  try {
    await api.post(`/projects/${route.params.id}/environments/`, newEnv.value)
    ElMessage.success('环境添加成功')
    showAddEnvDialog.value = false
    newEnv.value = { name: '', base_url: '', description: '', is_default: false }
    await fetchEnvironments()
  } catch (error) {
    ElMessage.error('添加环境失败')
  }
}

onMounted(() => {
  fetchProject()
})
</script>

<style lang="scss" scoped>
.members-section, .environments-section {
  padding: 20px 0;
}
</style>