<template>
  <div class="agent-management p-4">
    <el-card>
      <template #header>
        <div class="flex justify-between items-center">
          <span>Agent 节点管理</span>
          <el-button type="primary" @click="refreshAgents">刷新</el-button>
        </div>
      </template>
      <el-table :data="agents" v-loading="loading" style="width: 100%">
        <el-table-column prop="name" label="Agent 名称">
          <template #default="{ row }">
            {{ row.name || row.id }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="ip_address" label="IP 地址" width="150" />
        <el-table-column label="资源使用率" width="300">
          <template #default="{ row }">
            <div>CPU: <el-progress :percentage="parseFloat(row.cpu_usage || 0)" class="mb-2" /></div>
            <div>内存: <el-progress :percentage="parseFloat(row.memory_usage || 0)" status="success" class="mb-2" /></div>
            <div>磁盘: <el-progress :percentage="parseFloat(row.disk_usage || 0)" status="warning" /></div>
          </template>
        </el-table-column>
        <el-table-column prop="agent_version" label="版本" width="100" />
        <el-table-column label="标签" width="200">
            <template #default="{ row }">
                <el-tag v-for="tag in row.tags" :key="tag.id" class="mr-2" :color="tag.color" effect="dark">
                    {{ tag.name }}
                </el-tag>
            </template>
        </el-table-column>
        <el-table-column prop="last_heartbeat" label="上次心跳" width="180">
           <template #default="{ row }">
            {{ formatTime(row.last_heartbeat) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewAgentDetails(row)">详情</el-button>
            <el-button size="small" type="danger" @click="deleteAgent(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
       <el-pagination
        class="mt-4"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        :current-page="pagination.currentPage"
        :page-sizes="[10, 20, 50, 100]"
        :page-size="pagination.pageSize"
        layout="total, sizes, prev, pager, next, jumper"
        :total="pagination.total">
      </el-pagination>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import axios from 'axios';

const agents = ref([]);
const loading = ref(false);
const pagination = ref({
  currentPage: 1,
  pageSize: 10,
  total: 0,
});
let intervalId = null;

const fetchAgents = async () => {
  loading.value = true;
  try {
    const response = await axios.get('/api/agents/', {
      params: {
        page: pagination.value.currentPage,
        page_size: pagination.value.pageSize,
      }
    });
    agents.value = response.data.results;
    pagination.value.total = response.data.count;
  } catch (error) {
    ElMessage.error('获取 Agent 列表失败');
    console.error(error);
  } finally {
    loading.value = false;
  }
};

const refreshAgents = () => {
    fetchAgents();
    ElMessage.success('Agent 列表已刷新');
}

const getStatusTagType = (status) => {
  switch (status) {
    case 'online':
      return 'success';
    case 'busy':
      return 'warning';
    case 'offline':
      return 'danger';
    default:
      return 'info';
  }
};

const formatTime = (timeStr) => {
    if (!timeStr) return 'N/A';
    return new Date(timeStr).toLocaleString();
}

const handleSizeChange = (val) => {
  pagination.value.pageSize = val;
  fetchAgents();
}

const handleCurrentChange = (val) => {
  pagination.value.currentPage = val;
  fetchAgents();
}

const viewAgentDetails = (agent) => {
  // TODO: Implement agent detail view
  ElMessage.info(`查看 Agent: ${agent.name || agent.id}`);
};

const deleteAgent = (agent) => {
  ElMessageBox.confirm(`确定要删除 Agent "${agent.name || agent.id}" 吗？`, '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(async () => {
    try {
      await axios.delete(`/api/agents/${agent.id}/`);
      ElMessage.success('Agent 删除成功');
      fetchAgents();
    } catch (error) {
      ElMessage.error('删除 Agent 失败');
      console.error(error);
    }
  }).catch(() => {
    // Cancelled
  });
};

onMounted(() => {
  fetchAgents();
  // Poll for agent status every 10 seconds
  intervalId = setInterval(fetchAgents, 10000);
});

onUnmounted(() => {
    if(intervalId) {
        clearInterval(intervalId);
    }
})
</script>

<style scoped>
.agent-management {
  height: 100%;
}
.mb-2 {
    margin-bottom: 0.5rem;
}
</style>
