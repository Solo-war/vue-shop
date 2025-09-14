import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../components/HomeView.vue'
import Basket from '@/components/Basket.vue'
import Favorites from '@/components/Favorites.vue'
import Compare from '@/components/Compare.vue'
import SiteHeader from '@/components/SiteHeader.vue'
import Checkout from '@/components/Checkout.vue' 
import Login from '@/views/Login.vue'
import Register from '@/views/Register.vue'
import Profile from '@/views/Profile.vue'
import PayMock from '@/components/PayMock.vue'
import { useAuthStore } from '@/store/auth'
import { syncCartOnLogin } from '@/cart.js'
import Admin from '@/views/Admin.vue'
import ProductDetail from '@/views/ProductDetail.vue'

// 🔹 Сначала создаём список маршрутов
const routes = [
  { path: '/', component: HomeView },
  { path: '/basket', component: Basket },
  { path: '/favorites', component: Favorites },
  { path: '/compare', component: Compare },
  { path: '/login', component: Login },
  { path: '/register', component: Register },
  {
    path: '/profile',
    component: Profile,
    meta: { requiresAuth: true }, // 🔒 Защита
  },
  { path: '/checkout', component: Checkout },
  { path: '/pay', name: 'pay', component: PayMock }, // 🔹 новый маршрут
  { path: '/admin', component: Admin, meta: { requiresAuth: true, requiresAdmin: true } },
  // Support pretty slug or numeric id in the same param
  { path: '/product/:key', component: ProductDetail },
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
      if (auth.user?.username) {
        syncCartOnLogin(auth.user.username)
      }
    } catch {
      auth.logout()
      return next('/login')
    }
  }

  if (to.meta.requiresAuth && !auth.token) {
    return next('/login')
  }

  if (to.meta.requiresAdmin) {
    if (auth.user?.role !== 'admin') {
      return next('/')
    }
  }

  next()
})

export default router
