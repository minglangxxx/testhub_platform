<template>
  <div class="log-viewer p-4">
    <el-card>
       <template #header>
        <div class="flex justify-between items-center">
          <span>任务日志: {{ taskName }}</span>
          <el-button @click="router.back()">返回</el-button>
        </div>
      </template>
      <div ref="logContainer" class="log-container bg-gray-900 text-white p-4 rounded font-mono h-96 overflow-y-auto">
        <div v-for="(log, index) in logs" :key="index" :class="getLogClass(log.type)">
          <span class="timestamp mr-4">{{ formatTime(log.timestamp) }}</span>
          <span>{{ log.content }}</span>
        </div>
         <div v-if="loading" class="text-center">加载中...</div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';
import { ElMessage } from 'element-plus';

const route = useRoute();
const router = useRouter();
const taskId = route.params.id;
const taskName = ref('');
const logs = ref([]);
const loading = ref(false);
const logContainer = ref(null);
let intervalId = null;

const fetchLogs = async () => {
  loading.value = true;
  try {
    const response = await axios.get(`/api/tasks/${taskId}/logs/`);
    logs.value = response.data;
    scrollToBottom();
  } catch (error) {
    ElMessage.error('获取日志失败');
    console.error(error);
  } finally {
    loading.value = false;
  }
};

const fetchTaskDetails = async () => {
    try {
        const response = await axios.get(`/api/tasks/${taskId}/`);
        taskName.value = response.data.name;
        // Start polling only if the task is still running
        if (['pending', 'running'].includes(response.data.status)) {
            intervalId = setInterval(fetchLogs, 5000); // Poll every 5 seconds
        }
    } catch (error) {
        ElMessage.error('获取任务详情失败');
    }
}

const formatTime = (timeStr) => {
    if (!timeStr) return '';
    return new Date(timeStr).toLocaleString();
}

const getLogClass = (logType) => {
  return logType === 'stderr' ? 'text-red-400' : 'text-gray-300';
};

const scrollToBottom = () => {
    nextTick(() => {
        if (logContainer.value) {
            logContainer.value.scrollTop = logContainer.value.scrollHeight;
        }
    });
}

onMounted(() => {
  fetchTaskDetails();
  fetchLogs();
});

onUnmounted(() => {
    if (intervalId) {
        clearInterval(intervalId);
    }
})
</script>

<style scoped>
.log-container {
  background-color: #1a202c;
  color: #e2e8f0;
  height: 70vh;
}
.text-red-400 {
    color: #f87171;
}
.text-gray-300 {
    color: #d1d5db;
}
.timestamp {
    color: #6b7280;
}
</style>
