<script setup>
import { ref } from 'vue'
import SiteHeader from './components/SiteHeader.vue'
import HomeView from './components/HomeView.vue'
import Favorites from './components/Favorites.vue'
import Basket from './components/Basket.vue'


const activeView = ref('home') // "home" | "favorites" | "basket"

function toggleFavorites() {
  activeView.value = activeView.value === 'favorites' ? 'home' : 'favorites'
}

function toggleBasket() {
  activeView.value = activeView.value === 'basket' ? 'home' : 'basket'
}
</script>
<template>
  <div class="app-shell">
    <SiteHeader />
    <router-view v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </div>
  
</template>
