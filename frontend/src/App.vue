<template>
  <div id="app">
    <a-layout class="app-layout">
      <a-layout-header class="app-header">
        <div class="header-inner"></div>
        <div v-if="sessionUser" class="user-actions floating-actions">
          <span class="welcome">欢迎，{{ sessionUser.name || sessionUser.email }}</span>
          <a-button size="small" type="primary" danger @click="confirmLogout">
            切换/注销
          </a-button>
        </div>
      </a-layout-header>
      <a-layout-content class="app-content">
        <router-view />
      </a-layout-content>
      <a-layout-footer class="app-footer">
        AiTravelPlanner 智能旅行助手
      </a-layout-footer>
    </a-layout>
  </div>  
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Modal } from 'ant-design-vue'
import { clearSession, getSessionUser } from '@/services/auth'

const router = useRouter()
const sessionUser = ref(getSessionUser())
const navItems = [
  { label: '语音规划', path: '/' },
  { label: '行程结果', path: '/result' }
]

const refreshSession = () => {
  sessionUser.value = getSessionUser()
}

onMounted(() => {
  refreshSession()
})

router.afterEach(() => {
  refreshSession()
})

const confirmLogout = () => {
  Modal.confirm({
    title: '确认退出当前账号？',
    content: '退出后将返回登录/注册页面，可重新选择账号。',
    okText: '确认退出',
    cancelText: '再想想',
    okType: 'danger',
    onOk() {
      clearSession()
      sessionUser.value = null
      router.push('/auth')
    }
  })
}

const goTo = (path: string) => {
  if (router.currentRoute.value.path === path) return
  router.push(path)
}
</script>

<style scoped>
#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    'Noto Sans', sans-serif;
}

.app-layout {
  min-height: 100vh;
}

.app-header {
  background: #0f172a;
  padding: 0;
  position: relative;
}

.header-inner {
  max-width: 1280px;
  margin: 0 auto;
  padding: 20px 24px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #cbd5f5;
}

.floating-actions {
  position: absolute;
  top: 16px;
  right: 24px;
}

.welcome {
  font-size: 14px;
}

.app-content {
  padding: 12px 20px 24px;
  background: #f5f7fb;
  min-height: calc(100vh - 128px);
}

.app-footer {
  text-align: center;
  color: #64748b;
  font-size: 14px;
}
</style>
