import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/login.vue'
// 其他页面可按需导入，如：import Home from '../views/home.vue'

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
  }
  // 后续页面示例
  // {
  //   path: '/home',
  //   name: 'Home',
  //   component: Home
  // }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router