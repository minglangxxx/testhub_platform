<template>
  <div class="task-management p-4">
    <el-card>
      <template #header>
        <div class="flex justify-between items-center">
          <span>任务管理</span>
          <div>
            <el-button type="primary" @click="goToCreateTask">创建任务</el-button>
            <el-button @click="refreshTasks">刷新</el-button>
          </div>
        </div>
      </template>
      <el-table :data="tasks" v-loading="loading" style="width: 100%">
        <el-table-column prop="name" label="任务名称" width="250" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="agent.name" label="执行Agent" width="180">
            <template #default="{ row }">
                {{ row.agent ? (row.agent.name || row.agent.id) : 'N/A' }}
            </template>
        </el-table-column>
        <el-table-column prop="created_by" label="创建人" width="120" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="finished_at" label="完成时间" width="180">
            <template #default="{ row }">
            {{ formatTime(row.finished_at) }}
          </template>
        </el-table-column>
        <el-table-column label="执行时长" width="120">
            <template #default="{ row }">
                {{ getDuration(row.started_at, row.finished_at) }}
            </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewTaskLogs(row)">日志</el-button>
            <el-button size="small" type="primary" @click="viewReport(row)">报告</el-button>
            <el-button size="small" type="danger" @click="deleteTask(row)">删除</el-button>
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
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import axios from 'axios';

const router = useRouter();
const tasks = ref([]);
const loading = ref(false);
const pagination = ref({
  currentPage: 1,
  pageSize: 10,
  total: 0,
});

const fetchTasks = async () => {
  loading.value = true;
  try {
    const response = await axios.get('/api/tasks/', {
        params: {
            page: pagination.value.currentPage,
            page_size: pagination.value.pageSize,
        }
    });
    tasks.value = response.data.results;
    pagination.value.total = response.data.count;
  } catch (error) {
    ElMessage.error('获取任务列表失败');
    console.error(error);
  } finally {
    loading.value = false;
  }
};

const refreshTasks = () => {
    fetchTasks();
    ElMessage.success('任务列表已刷新');
}

const goToCreateTask = () => {
  router.push({ name: 'TaskCreate' });
};

const getStatusTagType = (status) => {
  switch (status) {
    case 'success':
      return 'success';
    case 'running':
      return 'primary';
    case 'failed':
    case 'timeout':
      return 'danger';
    case 'pending':
      return 'warning';
    default:
      return 'info';
  }
};

const formatTime = (timeStr) => {
    if (!timeStr) return 'N/A';
    return new Date(timeStr).toLocaleString();
}

const getDuration = (start, end) => {
    if (!start || !end) return 'N/A';
    const duration = new Date(end) - new Date(start);
    if (duration < 0) return 'N/A';
    const seconds = Math.floor((duration / 1000) % 60);
    const minutes = Math.floor((duration / (1000 * 60)) % 60);
    const hours = Math.floor((duration / (1000 * 60 * 60)));
    return `${hours}h ${minutes}m ${seconds}s`;
}

const handleSizeChange = (val) => {
  pagination.value.pageSize = val;
  fetchTasks();
}

const handleCurrentChange = (val) => {
  pagination.value.currentPage = val;
  fetchTasks();
}

const viewTaskLogs = (task) => {
  router.push({ name: 'TaskLogs', params: { id: task.id } });
};

const viewReport = (task) => {
  // Assuming the report URL is available in the task details or can be constructed
  ElMessage.info(`查看任务 "${task.name}" 的报告`);
  // Example: window.open(`/reports/allure/${task.id}/`, '_blank');
};

const deleteTask = (task) => {
  ElMessageBox.confirm(`确定要删除任务 "${task.name}" 吗？`, '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(async () => {
    try {
      await axios.delete(`/api/tasks/${task.id}/`);
      ElMessage.success('任务删除成功');
      fetchTasks();
    } catch (error) {
      ElMessage.error('删除任务失败');
      console.error(error);
    }
  }).catch(() => {
    // Cancelled
  });
};

onMounted(fetchTasks);
</script>

<style scoped>
.task-management {
  height: 100%;
}
</style>
