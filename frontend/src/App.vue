<template>
  <div id="app">
    <a-layout class="app-layout">
      <a-layout-header class="app-header">
        <div class="header-inner">
          <div class="brand-block">
            <div class="logo">✈️</div>
            <div class="brand-text">
              <div class="title">AiTravelPlanner 智能旅行助手</div>
              <div class="subtitle">语音驱动 · AI 规划 · 悦享旅程</div>
            </div>
          </div>
          <div class="nav-block">
            <button
              v-for="item in navItems"
              :key="item.path"
              :class="['nav-link', { active: router.currentRoute.value.path === item.path }]"
              @click="goTo(item.path)"
            >
              {{ item.label }}
            </button>
          </div>
          <div v-if="sessionUser" class="actions-block">
            <span class="welcome">欢迎，{{ sessionUser.name || sessionUser.email }}</span>
            <a-button size="small" type="primary" danger @click="confirmLogout">
              切换/注销
            </a-button>
          </div>
        </div>
      </a-layout-header>
      <a-layout-content class="app-content">
        <router-view />
      </a-layout-content>
      <a-layout-footer class="app-footer">
        AiTravelPlanner 智能旅行助手 ©2025 基于 AiTravelPlanner 框架
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
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif;
}

.app-layout {
  min-height: 100vh;
}

.app-header {
  background: #0f172a;
  padding: 0;
}

.header-inner {
  max-width: 1280px;
  margin: 0 auto;
  padding: 10px 24px;
  min-height: 72px;
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.brand-block {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #e2e8f0;
  flex: 1 1 260px;
  min-width: 220px;
}

.brand-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.logo {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.title {
  font-size: 22px;
  font-weight: 700;
  white-space: nowrap;
}

.subtitle {
  font-size: 14px;
  color: #94a3b8;
}

.nav-block {
  flex: 1 1 320px;
  min-width: 240px;
  display: flex;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
}

.nav-link {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(148, 163, 184, 0.3);
  color: #cbd5f5;
  padding: 6px 14px;
  border-radius: 999px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.nav-link:hover,
.nav-link.active {
  border-color: #fff;
  color: #fff;
  background: rgba(255, 255, 255, 0.15);
}

.actions-block {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #cbd5f5;
  flex: 0 0 auto;
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

@media (max-width: 1024px) {
  .header-inner {
    flex-direction: column;
    align-items: stretch;
  }
  .brand-block,
  .nav-block,
  .actions-block {
    justify-content: center;
  }
  .nav-block {
    order: 3;
  }
}
</style>


