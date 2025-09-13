<script>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { addToCart } from '../cart.js'
import { toggleFavorite, isFavorite } from '../favorites.js'
import { toggleCompare, isCompared } from '../compare.js'

export default {
  setup() {
    const products = ref([])
    const loading = ref(true)
    const route = useRoute()

    onMounted(async () => {
      try {
        const res = await fetch('/api/products')
        const data = await res.json()
        products.value = (Array.isArray(data) ? data : []).map((it, i) => ({
          id: it.id ?? i,
          name: it.name ?? it.title ?? 'Product',
          price: Number(it.price ?? 0),
          description: it.description ?? '',
          image: (Array.isArray(it.images) && it.images[0]) || it.image || '/images/placeholder.svg',
        }))
      } catch (e) {
        console.error(e)
      } finally {
        loading.value = false
      }
    })

    function add(p) { addToCart(p) }
    function formatPrice(v) { return Number(v).toLocaleString('ru-RU') }

    const q = computed(() => String(route.query.q || '').trim().toLowerCase())
    const filteredProducts = computed(() => {
      const term = q.value
      if (!term) return products.value
      return products.value.filter(p =>
        String(p.name || '').toLowerCase().includes(term) ||
        String(p.description || '').toLowerCase().includes(term)
      )
    })

    return { products, loading, add, formatPrice, toggleFavorite, isFavorite, toggleCompare, isCompared, filteredProducts }
  },
}
</script>

<template>
  <div class="container">
    <h1>Products</h1>

    <div v-if="loading" class="empty muted">Loading...</div>
    <div v-else-if="filteredProducts.length === 0" class="empty muted">No results found</div>

    <div v-else class="grid-premium">
      <article v-for="p in filteredProducts" :key="p.id" class="card product-card">
        <div class="thumb-wrapper">
          <img :src="p.image" alt="" class="thumb" />

          <button
            class="compare-btn"
            :class="{ active: isCompared(p.id) }"
            @click="toggleCompare(p)"
            aria-label="Compare"
            title="Compare"
          >
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M10 4h4v2h-4zM8 8h8v2H8zM6 12h12v2H6zM4 16h16v2H4z" />
            </svg>
          </button>

          <button
            class="favorite-btn"
            :class="{ active: isFavorite(p.id) }"
            @click="toggleFavorite(p)"
            aria-label="Toggle favorite"
            title="Toggle favorite"
          >
            <svg viewBox="0 0 24 24" width="20" height="20" :fill="isFavorite(p.id) ? 'red' : 'none'" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 21l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 6 4 4 6.5 4c1.74 0 3.41 1.01 4.22 2.09C11.09 5.01 12.76 4 14.5 4 17 4 19 6 19 8.5c0 3.78-3.4 6.86-8.55 11.18z" />
            </svg>
          </button>
        </div>

        <div class="title">{{ p.name }}</div>
        <div class="desc">{{ p.description }}</div>
        <div class="row">
          <div class="price">{{ formatPrice(p.price) }} ₽</div>
          <button class="btn btn-primary" @click="add(p)">Add to cart</button>
        </div>
      </article>
    </div>
  </div>
  
</template>

<style scoped>
.thumb {
  width: 100%;
  height: 180px;
  object-fit: cover;
  border-radius: 12px;
  background: rgba(255,255,255,0.04);
}
.title { font-weight: 700; }
.desc { color: var(--text-2); font-size: 13px; min-height: 30px; }
.row { display: flex; justify-content: space-between; align-items: center; margin-top: auto; }
.price { font-weight: 800; }
.empty { padding: 40px; text-align: center; }

.thumb-wrapper { position: relative; }
.compare-btn {
  position: absolute; top: 8px; left: 8px; border: 1px solid rgba(255,255,255,0.15);
  background: linear-gradient(180deg, rgba(255,255,255,0.12), rgba(255,255,255,0.06));
  border-radius: 12px; padding: 6px; cursor: pointer; transition: transform 0.2s;
}
.compare-btn:hover { transform: scale(1.05); }
.compare-btn.active svg { stroke: var(--brand); }
.favorite-btn {
  position: absolute; top: 8px; right: 8px; border: 1px solid rgba(255,255,255,0.15);
  background: linear-gradient(180deg, rgba(255,255,255,0.12), rgba(255,255,255,0.06));
  border-radius: 12px; padding: 6px; cursor: pointer; transition: transform 0.2s;
}
.favorite-btn:hover { transform: scale(1.05); }
.favorite-btn.active svg { fill: red; stroke: red; }
</style>

