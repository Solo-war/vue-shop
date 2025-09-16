<script setup>

import { cart, removeFromCart, clearCart } from '../cart.js'
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'   // ⬅️ добавили

const auth = useAuthStore()
const router = useRouter()


function formatPrice(v) { return Number(v).toLocaleString('ru-RU') }

const total = computed(() => cart.value.reduce((sum, item) => sum + item.price * item.qty, 0))

function increaseQty(id, size = null) {
  const found = cart.value.find((item) => item.id === id && ((item.size ?? null) === (size ?? null)))
  if (found) found.qty++
}

function decreaseQty(id, size = null) {
  const found = cart.value.find((item) => item.id === id && ((item.size ?? null) === (size ?? null)))
  if (found && found.qty > 1) found.qty--
  else removeFromCart(id, size)
}

function goCheckout() {
  if (!auth.user) {
    router.push('/profile') // или на страницу логина
    return
  }
  router.push('/checkout')
}


function inc(item){ increaseQty(item.id, item.size ?? null) }
function dec(item){ decreaseQty(item.id, item.size ?? null) }
function remove(item){ removeFromCart(item.id, item.size ?? null) }
</script>

<template>
  <div class="container basket">
    <h1>Корзина</h1>

    <div v-if="cart.length === 0" class="empty muted">Корзина пуста</div>

    <div v-else>
      <div class="basket-items">
        <div class="basket-item card" v-for="item in cart" :key="item.id + ':' + (item.size || '')">
          <img :src="item.image" alt="" class="thumb" />
          <div class="info">
            <div class="title">{{ item.name }}</div>
            <div class="price">{{ formatPrice(item.price) }} ₽</div>
            <div class="muted" v-if="item.size">Размер: {{ item.size }}</div>
            <div class="qty">
              <button class="qty-btn" @click="dec(item)">−</button>
              {{ item.qty }}
              <button class="qty-btn" @click="inc(item)">+</button>
            </div>
          </div>
          <button class="btn btn-secondary" @click="remove(item)">Удалить</button>
        </div>
      </div>

      <div class="total">Итого: <strong>{{ formatPrice(total) }} ₽</strong></div>


        <div class="actions">
          <button
            v-if="cart.length > 0"
            class="btn btn-primary"
            @click="goCheckout"
          >
            Оформить заказ
          </button>
          <button class="btn btn-danger" @click="clearCart">Очистить корзину</button>
        </div>

    </div>
  </div>
  
</template>

<style scoped>
.basket-item { display: flex; align-items: center; gap: 12px; padding: 12px; margin-bottom: 10px; }
.thumb { width: 86px; height: 86px; object-fit: cover; border-radius: 12px; background: rgba(255,255,255,0.06); }
.info { flex: 1; }
.qty { display: inline-flex; gap: 8px; align-items: center; margin-top: 6px; }
.qty-btn { cursor: pointer; padding: 6px 10px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.15); background: rgba(255,255,255,0.06); color: var(--text-1) }
.actions { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-top: 20px; }
.total { margin-top: 20px; font-size: 18px; }
.empty { text-align: center; padding: 40px; }

/* Mobile responsiveness */
@media (max-width: 640px) {
  .basket-item { align-items: flex-start; flex-wrap: wrap; }
  .thumb { width: 100%; height: auto; aspect-ratio: 4 / 3; }
  .actions { flex-direction: column; gap: 10px; align-items: center; }
}
</style>
