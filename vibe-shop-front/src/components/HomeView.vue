<script>
import { ref, onMounted } from 'vue'
import { addToCart } from '../cart.js'
import { toggleFavorite, isFavorite } from '../favorites.js'

export default {
  setup() {
    const products = ref([])
    const loading = ref(true)

    onMounted(async () => {
      try {
        const res = await fetch('/api/products')
        const data = await res.json()
        products.value = (Array.isArray(data) ? data : []).map((it, i) => ({
          id: it.id ?? i,
          name: it.name ?? it.title ?? 'Без названия',
          price: Number(it.price ?? 0),
          description: it.description ?? '',
          image:
            (Array.isArray(it.images) && it.images[0]) ||
            it.image ||
            '/images/placeholder.jpg',
        }))
      } catch (e) {
        console.error(e)
      } finally {
        loading.value = false
      }
    })

    function add(p) {
      addToCart(p)
    }

    function formatPrice(v) {
      return Number(v).toLocaleString('ru-RU')
    }

    return { products, loading, add, formatPrice, toggleFavorite, isFavorite }
  },
}
</script>

<template>
  <div class="container">
    <h1>Все товары</h1>

    <div v-if="loading" class="empty">Загрузка...</div>

    <div v-else class="grid">
      <article v-for="p in products" :key="p.id" class="card">
        <div class="thumb-wrapper">
          <img :src="p.image" alt="" class="thumb" />

          <!-- ❤️ кнопка -->
          <button
            class="favorite-btn"
            :class="{ active: isFavorite(p.id) }"
            @click="toggleFavorite(p)"
          >
            <svg
              viewBox="0 0 24 24"
              width="20"
              height="20"
              :fill="isFavorite(p.id) ? 'red' : 'none'"
              stroke="currentColor"
              stroke-width="1.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path
                d="M12 21l-1.45-1.32C5.4 15.36 2 12.28 2 8.5
                   2 6 4 4 6.5 4c1.74 0 3.41 1.01 4.22 2.09
                   C11.09 5.01 12.76 4 14.5 4
                   17 4 19 6 19 8.5c0 3.78-3.4 6.86-8.55 11.18z"
              />
            </svg>
          </button>
        </div>

        <div class="title">{{ p.name }}</div>
        <div class="desc">{{ p.description }}</div>
        <div class="row">
          <div class="price">{{ formatPrice(p.price) }} руб.</div>
          <button class="add" @click="add(p)">Добавить</button>
        </div>
      </article>
    </div>
  </div>
</template>





<style scoped>
.container {
  max-width: 1200px;
  margin: 24px auto;
  padding: 0 16px;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 18px;
}
.card {
  background: #fff;
  border-radius: 10px;
  padding: 12px;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.thumb {
  width: 100%;
  height: 150px;
  object-fit: cover;
  border-radius: 8px;
  background: #f6f6f6;
}
.title {
  font-weight: 600;
}
.desc {
  color: #666;
  font-size: 13px;
}
.row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: auto;
}
.price {
  font-weight: 700;
}
.add {
  background: #ff6a00;
  border: none;
  color: #fff;
  padding: 6px 10px;
  border-radius: 8px;
  cursor: pointer;
}
.empty {
  padding: 40px;
  text-align: center;
  color: #777;
}

.thumb-wrapper {
  position: relative;
}

.favorite-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  background: white;
  border: none;
  border-radius: 50%;
  padding: 5px;
  cursor: pointer;
  transition: transform 0.2s;
}

.favorite-btn:hover {
  transform: scale(1.1);
}

.favorite-btn.active svg {
  fill: red;
  stroke: red;
}

</style>
