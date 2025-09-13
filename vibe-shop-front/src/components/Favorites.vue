<template>
  <div class="container">
    <h1>Избранное</h1>

    <div v-if="favorites.length === 0" class="empty muted">Пусто: ничего не добавлено</div>

    <div v-else class="list">
      <article v-for="p in favorites" :key="p.id" class="card item">
        <img :src="p.image" alt="" class="thumb" />

        <div class="info">
          <div class="title">{{ p.name }}</div>
          <div class="desc">{{ p.description }}</div>

          <div class="row">
            <div class="price">{{ formatPrice(p.price) }} ₽</div>
            <div class="actions">
              <button class="btn btn-primary" @click="add(p)">В корзину</button>
              <button class="btn btn-secondary" @click="removeFavorite(p.id)">Удалить</button>
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
    function add(p) { addToCart(p) }
    function formatPrice(v) { return Number(v).toLocaleString('ru-RU') }
    return { favorites, add, formatPrice, removeFavorite }
  },
}
</script>


<style scoped>
.list { display: flex; flex-direction: column; gap: 16px; }
.item { display: flex; gap: 12px; }
.thumb { width: 140px; height: 140px; object-fit: cover; border-radius: 12px; flex-shrink: 0; background: rgba(255,255,255,0.06); }
.info { display: flex; flex-direction: column; flex: 1; }
.title { font-weight: 700; }
.desc { color: var(--text-2); font-size: 13px; margin: 4px 0; flex: 1; }
.row { display: flex; justify-content: space-between; align-items: center; }
.price { font-weight: 800; }
.actions { display: flex; gap: 8px; }
.empty { padding: 40px; text-align: center; }
</style>

