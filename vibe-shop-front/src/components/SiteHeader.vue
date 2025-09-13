<template>
  <header class="site-header">
    <div class="inner">
      <div class="left cursor-pointer" @click="$router.push('/')">
        <img class="logo" :src="logo" alt="logo" />
        <div class="brand">
          <div class="title">Vibe Shop</div>
          <div class="subtitle">Premium marketplace experience</div>
        </div>
      </div>

      <div class="right">
        <RouterLink
          v-if="auth.user?.role === 'admin'"
          to="/admin"
          class="icon"
          aria-label="Admin"
          title="Admin"
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="3"></circle>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33h0A1.65 1.65 0 0 0 10.91 3H11a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51h0a1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82v0A1.65 1.65 0 0 0 21 12v.09a1.65 1.65 0 0 0-1.6 1.41z"></path>
          </svg>
        </RouterLink>
        <div class="search">
          <span class="icon-left" aria-hidden="true">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="11" cy="11" r="8"/>
              <line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
          </span>
          <input
            v-model="search"
            @keydown.enter="goSearch"
            @input="onType"
            type="search"
            placeholder="Search products..."
            aria-label="Search products"
          />
          <button v-if="search" class="clear" @click="clearSearch" aria-label="Clear search">
            ×
          </button>
        </div>
        <RouterLink to="/basket" class="icon" aria-label="Basket" title="Basket">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="9" cy="21" r="1"></circle>
            <circle cx="20" cy="21" r="1"></circle>
            <path d="M1 1h4l2.68 12.39a2 2 0 0 0 2 1.61h7.72a2 2 0 0 0 2-1.61L23 6H6"></path>
          </svg>
        </RouterLink>

        <RouterLink to="/compare" class="icon with-badge" aria-label="Compare" title="Compare">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 4h6v2H3zM3 9h10v2H3zM3 14h14v2H3zM3 19h18v2H3z" />
          </svg>
          <span v-if="compareList.length" class="badge">{{ compareList.length }}</span>
        </RouterLink>

        <RouterLink to="/favorites" class="icon" aria-label="Favorites" title="Favorites">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78L12 21.23l8.84-8.84a5.5 5.5 0 0 0 0-7.78z" />
          </svg>
        </RouterLink>

        <template v-if="auth.user">
          <RouterLink to="/profile" class="profile" title="Profile">
            <span class="avatar">{{ auth.user.username?.slice(0,1)?.toUpperCase() || 'U' }}</span>
            <span class="name">{{ auth.user.username }}</span>
          </RouterLink>
          <button @click="logout" class="btn-secondary logout">Logout</button>
        </template>
        <template v-else>
          <RouterLink to="/login" class="auth">Login</RouterLink>
          <RouterLink to="/register" class="auth">Sign up</RouterLink>
        </template>
      </div>
    </div>
  </header>
</template>

<script setup>
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { ref, watch } from 'vue'
import { useAuthStore } from '@/store/auth'
import { compareList } from '@/compare.js'

const auth = useAuthStore()

const logo = '/images/guitar.svg'

const logout = () => {
  auth.logout()
  window.location.href = '/login'
}

// Search state synced with route query `q`
const route = useRoute()
const router = useRouter()
const search = ref(String(route.query.q || ''))

watch(
  () => route.query.q,
  (q) => { if ((search.value || '') !== String(q || '')) search.value = String(q || '') },
)

function updateRouteQuery(q) {
  const query = { ...route.query, q: q || undefined }
  if (route.path !== '/') {
    router.push({ path: '/', query })
  } else {
    router.replace({ query })
  }
}

function onType() {
  updateRouteQuery(search.value)
}

function goSearch() {
  updateRouteQuery(search.value)
}

function clearSearch() {
  search.value = ''
  updateRouteQuery('')
}
</script>

<style scoped>
.inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 10px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.left { display: flex; align-items: center; gap: 12px; }
.logo {
  width: 44px; height: 44px; border-radius: 12px; object-fit: cover;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.10);
}
.brand .title { font-weight: 800; letter-spacing: -0.02em; }
.brand .subtitle { font-size: 12px; opacity: .8; }

.right { display: flex; align-items: center; gap: 10px; }
.icon {
  display: inline-flex; align-items: center; justify-content: center;
  padding: 10px; color: var(--text-1);
  border-radius: 10px; border: 1px solid rgba(255,255,255,0.10);
  background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
}
.icon:hover { filter: brightness(1.15); }

.with-badge { position: relative; }
.badge {
  position: absolute; top: -6px; right: -6px;
  min-width: 18px; height: 18px; padding: 0 5px;
  border-radius: 999px; display: inline-flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700; color: #fff;
  background: linear-gradient(135deg, var(--brand), var(--brand-2));
  box-shadow: var(--shadow-sm);
}

.profile {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 8px 10px; border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.10);
  background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
  color: var(--text-1);
}
.avatar {
  width: 26px; height: 26px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, var(--brand), var(--brand-2));
  color: #fff; font-weight: 700; font-size: 12px;
}
.name { color: var(--text-2); font-weight: 600; }
.logout { margin-left: 4px; padding: 8px 10px; }
.auth { color: var(--text-1); opacity: .9; padding: 8px 10px; }
.auth:hover { opacity: 1; }

/* Search */
.search {
  position: relative;
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 240px;
  max-width: 360px;
  flex: 1 1 280px;
}
.search input {
  padding-left: 36px;
  padding-right: 30px;
}
.search .icon-left {
  position: absolute;
  left: 10px;
  color: var(--text-2);
  opacity: .9;
  display: inline-flex;
}
.search .clear {
  position: absolute;
  right: 6px;
  border-radius: 8px;
  height: 28px;
  width: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  background: transparent;
  color: var(--text-2);
}
.search .clear:hover {
  filter: none;
  color: var(--text-1);
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.12);
}
</style>
