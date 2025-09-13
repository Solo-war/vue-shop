import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../components/HomeView.vue'
import Basket from '@/components/Basket.vue'
import Favorites from '@/components/Favorites.vue'
import SiteHeader from '@/components/SiteHeader.vue'
import Checkout from '@/components/Checkout.vue' 
import Login from '@/views/Login.vue'
import Register from '@/views/Register.vue'
import Profile from '@/views/Profile.vue'
import PayMock from '@/components/PayMock.vue'
import { useAuthStore } from '@/store/auth'

// 🔹 Сначала создаём список маршрутов
const routes = [
  { path: '/', component: HomeView },
  { path: '/basket', component: Basket },
  { path: '/favorites', component: Favorites },
  { path: '/login', component: Login },
  { path: '/register', component: Register },
  {
    path: '/profile',
    component: Profile,
    meta: { requiresAuth: true }, // 🔒 Защита
  },
  { path: '/checkout', component: Checkout },
  { path: '/pay', name: 'pay', component: PayMock }, // 🔹 новый маршрут
]

// 🔹 Создаём сам роутер
const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 🔹 Теперь навешиваем middleware
router.beforeEach(async (to, from, next) => {
  const auth = useAuthStore()

  if (auth.token && !auth.user) {
    try {
      await auth.fetchUser()
    } catch {
      auth.logout()
      return next('/login')
    }
  }

  if (to.meta.requiresAuth && !auth.token) {
    return next('/login')
  }

  next()
})

export default router
