<script setup>
import { cart, removeFromCart, clearCart } from '../cart.js'
import { computed } from 'vue'
import { RouterLink } from 'vue-router'

function formatPrice(v) {
  return Number(v).toLocaleString('ru-RU')
}

// итоговая сумма
const total = computed(() =>
  cart.value.reduce((sum, item) => sum + item.price * item.qty, 0)
)

// увеличить количество
function increaseQty(id) {
  const found = cart.value.find((item) => item.id === id)
  if (found) {
    found.qty++
  }
}

// уменьшить количество
function decreaseQty(id) {
  const found = cart.value.find((item) => item.id === id)
  if (found && found.qty > 1) {
    found.qty--
  } else {
    removeFromCart(id)
  }
}
</script>

<template>
  <div class="container basket">
    <h1>Корзина</h1>

    <div v-if="cart.length === 0" class="empty">
      Корзина пуста
    </div>

    <div v-else>
      <div class="basket-items">
        <div class="basket-item" v-for="item in cart" :key="item.id">
          <img :src="item.image" alt="" class="thumb" />
          <div class="info">
            <div class="title">{{ item.name }}</div>
            <div class="price">{{ formatPrice(item.price) }} ₽</div>
            <div class="qty">
              <button class="qty-btn" @click="decreaseQty(item.id)">–</button>
              {{ item.qty }}
              <button class="qty-btn" @click="increaseQty(item.id)">+</button>
            </div>
          </div>
          <button class="remove" @click="removeFromCart(item.id)">Удалить</button>
        </div>
      </div>

      <div class="total">
        Итого: <strong>{{ formatPrice(total) }} ₽</strong>
      </div>

      <div class="actions">
        <RouterLink v-if="cart.length > 0" to="/checkout" class="pay">
          Оплатить
        </RouterLink>
        <button class="clear" @click="clearCart">Очистить корзину</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.container {
  max-width: 800px;
  margin: 24px auto;
  padding: 0 16px;
}
.basket-item {
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid #eee;
  padding: 12px 0;
}

.actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 20px;
}

.clear,
.pay {
  padding: 10px 18px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  text-decoration: none;
  text-align: center;
  min-width: 120px;
}

.clear {
  background: #e74c3c;
  color: white;
}

.pay {
  background: #27ae60;
  color: white;
  justify-self: end;


}

.thumb {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 8px;
  background: #f6f6f6;
}
.info {
  flex: 1;
}
.remove {
  background: #ff4444;
  color: #fff;
  border: none;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
}
.total {
  margin-top: 20px;
  font-size: 18px;
}
.clear {
  margin-top: 12px;
  background: #666;
  color: #fff;
  border: none;
  padding: 8px 14px;
  border-radius: 6px;
  cursor: pointer;
}
.empty {
  text-align: center;
  padding: 40px;
  color: #777;
}

.qty-btn {
  cursor: pointer;
}
</style>
