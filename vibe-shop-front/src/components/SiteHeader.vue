<template>
  <header class="site-header">
    <div class="inner">
      <div class="left cursor-pointer" @click="$router.push('/')">
        <img class="logo" :src="logo" alt="logo" />
        <div class="brand">
          <div class="title">VUE SNEAKERS</div>
          <div class="subtitle">Магазин лучших кроссовок</div>
        </div>
      </div>

        <div class="right flex gap-4 items-center">

          <RouterLink to="/basket" class="icon btn-cart" title="Корзина">
            🛒
          </RouterLink>


        <RouterLink to="/favorites" class="icon btn-cart" title="Избранное">
          ❤️
        </RouterLink>
        <template v-if="auth.user">
          <RouterLink to="/profile" class="icon btn-cart" title="Профиль">
            👤 {{ auth.user.username }}
          </RouterLink>
          <button @click="logout" class="ml-2 bg-red-500 px-2 py-1 rounded hover:bg-red-600">
            Выйти
          </button>
        </template>
        <template v-else>
          <RouterLink to="/login" class="hover:underline">Войти</RouterLink>
          <RouterLink to="/register" class="hover:underline">Регистрация</RouterLink>
        </template>
      </div>
    </div>
  </header>
</template>

<script setup>
import { RouterLink } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const auth = useAuthStore()

const logo = '/images/guitar.svg' 

const logout = () => {
  auth.logout()
  window.location.href = '/login'
}
</script>

<style scoped>
.site-header {
  background: linear-gradient(180deg, #f4fff3 0%, #ffffff 60%);
  padding: 18px 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
}
.inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.logo {
  width: 46px;
  height: 46px;
  border-radius: 50%;
  object-fit: cover;
  background: #fff;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
}
.brand .title {
  font-weight: 700;
  letter-spacing: 0.2px;
  font-size: 16px;
}
.brand .subtitle {
  font-size: 12px;
  color: #8b8b8b;
  margin-top: 2px;
}
.right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.icon {
  background: transparent;
  border: none;
  display: inline-flex;
  padding: 8px;
  cursor: pointer;
  color: #333;
}
.icon:hover {
  background: rgba(0, 0, 0, 0.03);
}
.btn-cart .amount {
  font-weight: 700;
  margin-left: 6px;
  font-size: 14px;
}
</style>
