import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'
import App from './App.vue'
import Home from './views/Home.vue'
import Result from './views/Result.vue'
import Auth from './views/Auth.vue'
import { getSessionUser } from '@/services/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Home',
      component: Home
    },
    {
      path: '/result',
      name: 'Result',
      component: Result
    },
    {
      path: '/auth',
      name: 'Auth',
      component: Auth
    }
  ]
})

const publicRoutes = ['/auth']

router.beforeEach((to, _from, next) => {
  const session = getSessionUser()
  if (!session && !publicRoutes.includes(to.path)) {
    next('/auth')
    return
  }
  if (session && to.path === '/auth') {
    next('/')
    return
  }
  next()
})

const app = createApp(App)

app.use(router)
app.use(Antd)

app.mount('#app')

