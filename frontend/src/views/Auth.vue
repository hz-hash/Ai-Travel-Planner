<template>
  <div class="auth-page">
    <div class="background-decoration">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
      <div class="circle circle-3"></div>
    </div>

    <div class="auth-card">
      <div class="brand">
        <div class="icon">✈️</div>
        <div>
          <h1>智能旅行助手</h1>
          <p>语音驱动 · AI 规划 · 悦享旅程</p>
        </div>
      </div>

      <div class="tabs">
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'login' }"
          @click="activeTab = 'login'"
        >
          登录
        </button>
        <button
          class="tab-btn"
          :class="[{ active: activeTab === 'register' }, 'right']"
          @click="activeTab = 'register'"
        >
          注册
        </button>
      </div>

      <div v-if="activeTab === 'login'" class="form-wrapper">
        <a-form layout="vertical" :model="loginForm" @finish="handleLogin">
          <a-form-item label="邮箱" name="email">
            <a-input
              v-model:value="loginForm.email"
              size="large"
              placeholder="请输入邮箱"
              autocomplete="email"
            />
          </a-form-item>
          <a-form-item label="密码" name="password">
            <a-input-password
              v-model:value="loginForm.password"
              size="large"
              placeholder="请输入密码"
              autocomplete="current-password"
            />
          </a-form-item>
          <a-button type="primary" size="large" block html-type="submit" class="primary-btn">
            登录
          </a-button>
          <p class="hint">
            试用账号: <strong>demo@aitrip.com / demo123</strong>
          </p>
        </a-form>
      </div>

      <div v-else class="form-wrapper">
        <a-form layout="vertical" :model="registerForm" @finish="handleRegister">
          <a-form-item label="昵称" name="name">
            <a-input
              v-model:value="registerForm.name"
              size="large"
              placeholder="请输入昵称"
            />
          </a-form-item>
          <a-form-item label="邮箱" name="email">
            <a-input
              v-model:value="registerForm.email"
              size="large"
              placeholder="请输入邮箱"
              autocomplete="email"
            />
          </a-form-item>
          <a-form-item label="密码" name="password">
            <a-input-password
              v-model:value="registerForm.password"
              size="large"
              placeholder="请输入密码"
              autocomplete="new-password"
            />
          </a-form-item>
          <a-form-item label="确认密码" name="confirmPassword">
            <a-input-password
              v-model:value="registerForm.confirmPassword"
              size="large"
              placeholder="请再次输入密码"
            />
          </a-form-item>
          <a-button type="primary" size="large" block html-type="submit" class="primary-btn">
            注册并进入
          </a-button>
        </a-form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { loginUser, registerUser } from '@/services/auth'

const router = useRouter()
const activeTab = ref<'login' | 'register'>('login')

const loginForm = reactive({
  email: 'demo@aitrip.com',
  password: 'demo123'
})

const registerForm = reactive({
  name: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const handleLogin = () => {
  if (!loginForm.email || !loginForm.password) {
    message.warning('请填写完整的登录信息')
    return
  }
  const result = loginUser(loginForm.email, loginForm.password)
  if (!result.success) {
    message.error(result.message)
    return
  }
  message.success(result.message)
  router.push('/')
}

const handleRegister = () => {
  if (!registerForm.name || !registerForm.email || !registerForm.password) {
    message.warning('请填写完整的注册信息')
    return
  }
  if (registerForm.password !== registerForm.confirmPassword) {
    message.warning('两次输入的密码不一致')
    return
  }
  const result = registerUser({
    name: registerForm.name,
    email: registerForm.email,
    password: registerForm.password
  })
  if (!result.success) {
    message.error(result.message)
    return
  }
  message.success(result.message)
  router.push('/')
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  padding: 40px 16px;
}

.background-decoration .circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.3;
  filter: blur(60px);
}

.circle-1 {
  width: 400px;
  height: 400px;
  background: #a78bfa;
  top: -100px;
  left: -80px;
}

.circle-2 {
  width: 300px;
  height: 300px;
  background: #63b3ed;
  right: -60px;
  top: 120px;
}

.circle-3 {
  width: 280px;
  height: 280px;
  background: #f6ad55;
  bottom: -80px;
  left: 120px;
}

.auth-card {
  width: 100%;
  max-width: 520px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 24px;
  padding: 36px;
  box-shadow: 0 30px 70px rgba(0, 0, 0, 0.25);
  position: relative;
  z-index: 2;
}

.brand {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.brand .icon {
  width: 64px;
  height: 64px;
  border-radius: 18px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  color: white;
}

.brand h1 {
  margin: 0;
  font-size: 26px;
  font-weight: 700;
  color: #2d3748;
}

.brand p {
  margin: 4px 0 0;
  color: #718096;
}

.tabs {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  background: #f1f5f9;
  padding: 6px;
  border-radius: 14px;
  margin-bottom: 32px;
  gap: 6px;
}

.tab-btn {
  border: none;
  background: transparent;
  color: #64748b;
  font-size: 16px;
  font-weight: 600;
  padding: 10px 0;
  border-radius: 12px;
  transition: all 0.3s ease;
  cursor: pointer;
}

.tab-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 8px 20px rgba(118, 75, 162, 0.25);
}

.form-wrapper {
  animation: fadeIn 0.4s ease;
}

.primary-btn {
  margin-top: 12px;
  height: 48px;
  font-size: 16px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
}

.hint {
  text-align: center;
  margin-top: 16px;
  color: #718096;
  font-size: 14px;
}

.hint strong {
  color: #4c51bf;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
