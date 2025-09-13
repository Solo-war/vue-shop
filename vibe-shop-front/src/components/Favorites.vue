<template>
  <div class="container">
    <h1>Избранные товары</h1>

    <div v-if="favorites.length === 0" class="empty">
      Нет избранных товаров
    </div>

    <div v-else class="list">
      <article v-for="p in favorites" :key="p.id" class="card">
        <img :src="p.image" alt="" class="thumb" />

        <div class="info">
          <div class="title">{{ p.name }}</div>
          <div class="desc">{{ p.description }}</div>

          <div class="row">
            <div class="price">{{ formatPrice(p.price) }} руб.</div>
            <div class="actions">
              <button class="add" @click="add(p)">В корзину</button>
              <button class="remove" @click="removeFavorite(p.id)">Удалить</button>
            </div>
          </div>
        </div>
      </article>
    </div>
  </div>
</template>


<script>
import { favorites, removeFavorite } from '../favorites.js'
import { addToCart } from '../cart.js'

export default {
  setup() {
    function add(p) {
      addToCart(p)
    }
    function formatPrice(v) {
      return Number(v).toLocaleString('ru-RU')
    }
    return { favorites, add, formatPrice, removeFavorite }
  },
}
</script>


<style scoped>
.container {
  max-width: 900px;
  margin: 24px auto;
  padding: 0 16px;
}
.list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.card {
  display: flex;
  background: #fff;
  border-radius: 10px;
  padding: 12px;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.06);
  gap: 12px;
}
.thumb {
  width: 140px;
  height: 140px;
  object-fit: cover;
  border-radius: 8px;
  flex-shrink: 0;
}
.info {
  display: flex;
  flex-direction: column;
  flex: 1;
}
.title {
  font-weight: 600;
}
.desc {
  color: #666;
  font-size: 13px;
  margin: 4px 0;
  flex: 1;
}
.row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.price {
  font-weight: 700;
}
.actions {
  display: flex;
  gap: 8px;
}
.add {
  background: #ff6a00;
  border: none;
  color: #fff;
  padding: 6px 10px;
  border-radius: 8px;
  cursor: pointer;
}
.remove {
  background: #eee;
  border: none;
  color: #333;
  padding: 6px 10px;
  border-radius: 8px;
  cursor: pointer;
}
.empty {
  padding: 40px;
  text-align: center;
  color: #777;
}
</style>
