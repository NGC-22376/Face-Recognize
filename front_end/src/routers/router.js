import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/login.vue'
import Admin from '../views/admin.vue'

const routes = [
  {
    path: '/',
    name: 'LoginPage',
    component: Login
  },
  {
    path: '/register',
    name: 'RegisterPage',
    component: Login // 复用 login.vue，页面自动切换为注册模式
  },
  {
    path: '/admin',
    name: 'AdminPage',
    component: Admin,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')
  const userInfo = JSON.parse(localStorage.getItem('user_info') || '{}')
  
  if (to.meta.requiresAuth) {
    if (!token) {
      // 未登录，重定向到登录页
      next('/')
      return
    }
    
    if (to.meta.role && userInfo.role !== to.meta.role) {
      // 权限不足
      alert('权限不足，无法访问该页面')
      next('/')
      return
    }
  }
  
  next()
})

export default router