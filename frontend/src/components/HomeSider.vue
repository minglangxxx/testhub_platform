<template>
  <el-aside class="home-aside" width="64px">
    <el-menu
      default-active="$route.path"
      class="home-menu"
      router
      unique-opened
      :collapse="false"
    >
        <el-menu-item index="/ai-generation/requirement-analysis" @click="setModule('ai-generation')">
          <el-tooltip content="AI用例生成" placement="right">
            <el-icon><MagicStick /></el-icon>
          </el-tooltip>
        </el-menu-item>

        <el-menu-item index="/api-testing/dashboard" @click="setModule('api-testing')">
          <el-tooltip content="接口测试" placement="right">
            <el-icon><Link /></el-icon>
          </el-tooltip>
        </el-menu-item>

        <el-menu-item index="/ui-automation/dashboard" @click="setModule('ui-automation')">
          <el-tooltip content="UI自动化" placement="right">
            <el-icon><Monitor /></el-icon>
          </el-tooltip>
        </el-menu-item>

        <el-menu-item index="/configuration/ai-model" @click="setModule('configuration')">
          <el-tooltip content="配置中心" placement="right">
            <el-icon><Setting /></el-icon>
          </el-tooltip>
        </el-menu-item>

        <el-menu-item index="/ai-intelligent-mode/testing" @click="setModule('ai-intelligent-mode')">
          <el-tooltip content="AI智能模式" placement="right">
            <el-icon><Cpu /></el-icon>
          </el-tooltip>
        </el-menu-item>

        <el-menu-item index="/ai-generation/assistant" @click="setModule('ai-generation')">
          <el-tooltip content="AI评测师" placement="right">
            <el-icon><ChatDotRound /></el-icon>
          </el-tooltip>
        </el-menu-item>

        <el-menu-item index="/ai-generation/agents" @click="setModule('agent')">
          <el-tooltip content="Agent管理" placement="right">
            <el-icon><Connection /></el-icon>
          </el-tooltip>
        </el-menu-item>

        <el-menu-item index="/department-manage/departments" @click="setModule('department')">
          <el-tooltip content="部门与用户管理" placement="right">
            <el-icon><UserFilled /></el-icon>
          </el-tooltip>
        </el-menu-item>

        <el-menu-item index="/" @click="setModule('home')">
          <el-tooltip content="首页" placement="right">
            <el-icon><Odometer /></el-icon>
          </el-tooltip>
        </el-menu-item>
</el-menu>
</el-aside>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { MagicStick, Link, Monitor, Setting, Cpu, ChatDotRound, UserFilled, Odometer, Connection } from '@element-plus/icons-vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const setModule = (module) => {
  // allow layout to react via route path change
  // navigation handled by el-menu router prop
}
</script>

<style scoped lang="scss">
.home-aside {
  background-color: #001529;
  height: 100vh;
  padding: 8px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  box-sizing: border-box;
  /* 与主侧栏的分隔线，避免出现白色缝隙 */
  border-right: 1px solid rgba(255,255,255,0.06);
}

.home-menu {
  width: 48px;
  border-right: none;
  height: 100%;
}

.home-menu .el-menu-item {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.home-menu .el-icon {
  font-size: 20px;
}

/* 覆盖 Element Plus 的默认样式，确保列背景一致且菜单占满高度 */
.home-aside :deep(.el-menu) {
  background-color: transparent !important;
  height: 100% !important;
  width: 100%;
  padding: 8px 0;
  box-sizing: border-box;
}

.home-aside :deep(.el-scrollbar__wrap),
.home-aside :deep(.el-scrollbar__view) {
  background-color: transparent !important;
  height: 100% !important;
}

.home-aside :deep(.el-menu-item) {
  background-color: transparent !important;
}
</style>
