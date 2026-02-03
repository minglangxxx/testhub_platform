<template>
  <div class="task-create p-4">
    <el-card>
      <template #header>
        <div class="flex justify-between items-center">
          <span>创建新任务</span>
          <el-button @click="router.back()">返回</el-button>
        </div>
      </template>
      <el-form :model="form" :rules="rules" ref="taskFormRef" label-width="120px">
        <el-form-item label="任务名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入任务名称"></el-input>
        </el-form-item>
        <el-form-item label="任务描述" prop="description">
          <el-input type="textarea" v-model="form.description" placeholder="请输入任务描述"></el-input>
        </el-form-item>
        <el-form-item label="执行Agent" prop="agent_id">
          <el-select v-model="form.agent_id" placeholder="选择一个Agent或留空" clearable filterable>
            <el-option
              v-for="agent in availableAgents"
              :key="agent.id"
              :label="agent.name || agent.id"
              :value="agent.id">
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="Shell脚本" prop="script">
          <div class="w-full h-64 border rounded">
            <MonacoEditor v-model="form.script" language="shell" />
          </div>
        </el-form-item>
        <el-form-item label="环境变量" prop="env_vars">
            <div class="w-full">
                <div v-for="(item, index) in envVarItems" :key="index" class="flex items-center mb-2">
                    <el-input v-model="item.key" placeholder="Key" class="mr-2"></el-input>
                    <el-input v-model="item.value" placeholder="Value" class="mr-2"></el-input>
                    <el-button type="danger" @click="removeEnvVar(index)" circle>-</el-button>
                </div>
                <el-button @click="addEnvVar" type="primary" plain>+ 添加环境变量</el-button>
            </div>
        </el-form-item>
        <el-form-item label="超时时间(秒)" prop="timeout">
            <el-input-number v-model="form.timeout" :min="60" :step="60"></el-input-number>
        </el-form-item>
        <el-form-item label="清理工作空间" prop="workspace_clean">
            <el-switch v-model="form.workspace_clean"></el-switch>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="submitForm" :loading="submitting">立即创建</el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import axios from 'axios';
import MonacoEditor from '@/components/common/MonacoEditor.vue';

const router = useRouter();
const taskFormRef = ref(null);
const submitting = ref(false);
const availableAgents = ref([]);
const envVarItems = ref([{ key: '', value: '' }]);

const form = reactive({
  name: '',
  description: '',
  script: '#!/bin/bash\n\necho "Hello, Agent!"\n',
  agent_id: null,
  env_vars: {},
  timeout: 1800,
  workspace_clean: true,
});

const rules = {
  name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  script: [{ required: true, message: '请输入执行脚本', trigger: 'blur' }],
};

const fetchAvailableAgents = async () => {
    try {
        const response = await axios.get('/api/agents/', { params: { page_size: 1000 } }); // Fetch all agents
        availableAgents.value = response.data.results.filter(agent => agent.status === 'online');
    } catch (error) {
        ElMessage.error('获取可用Agent列表失败');
        console.error(error);
    }
}

const addEnvVar = () => {
    envVarItems.value.push({ key: '', value: '' });
}

const removeEnvVar = (index) => {
    envVarItems.value.splice(index, 1);
}

// Watch envVarItems to update form.env_vars
watch(envVarItems, (newVal) => {
    form.env_vars = newVal.reduce((acc, item) => {
        if (item.key) {
            acc[item.key] = item.value;
        }
        return acc;
    }, {});
}, { deep: true });


const submitForm = () => {
  taskFormRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true;
      try {
        await axios.post('/api/tasks/', form);
        ElMessage.success('任务创建成功');
        router.push({ name: 'TaskList' });
      } catch (error) {
        ElMessage.error('任务创建失败');
        console.error(error);
      } finally {
        submitting.value = false;
      }
    }
  });
};

const resetForm = () => {
  taskFormRef.value.resetFields();
  form.script = '#!/bin/bash\n\necho "Hello, Agent!"\n';
  envVarItems.value = [{ key: '', value: '' }];
};

onMounted(() => {
    fetchAvailableAgents();
})
</script>

<style scoped>
.task-create {
  height: 100%;
}
.w-full {
    width: 100%;
}
.h-64 {
    height: 16rem;
}
.border {
    border: 1px solid #dcdfe6;
}
.rounded {
    border-radius: 4px;
}
.mb-2 {
    margin-bottom: 0.5rem;
}
.mr-2 {
    margin-right: 0.5rem;
}
</style>
