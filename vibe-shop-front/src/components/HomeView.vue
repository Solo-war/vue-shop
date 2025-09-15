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
    const selectedImage = ref({})

    onMounted(async () => {
      function mapProducts(data){
        function sanitize(u){
          const s = String(u||'')
          return s || '/images/placeholder.svg'
        }
        function reorderImages(list){
          const arr = Array.isArray(list) ? list.slice() : []
          const kw = [
            // RU
            'муж', 'мужчина', 'парень', 'полный', 'рост', 'анфас', 'фронт', 'стоя', 'лиц',
            // EN
            'man', 'male', 'model', 'full', 'fullbody', 'full-body', 'full_length', 'full-length', 'front', 'standing', 'person', 'guy'
          ]
          const demote = ['placeholder', 'noimg', 'no-image', 'notfound']
          const scored = arr.map((src, i) => {
            const s = String(src||'').toLowerCase()
            let score = 0
            for(const k of kw){ if(s.includes(k)) score += 1 }
            if((s.includes('full') || s.includes('полный') || s.includes('рост')) && (s.includes('front') || s.includes('анфас') || s.includes('лиц'))) score += 2
            for(const d of demote){ if(s.includes(d)) score -= 10 }
            return { src, i, score }
          })
          scored.sort((a,b) => b.score - a.score || a.i - b.i)
          return scored.map(x => x.src)
        }
        return (Array.isArray(data) ? data : []).map((it, i) => {
          const imgsRaw = Array.isArray(it.images) && it.images.length ? it.images : (it.image ? [it.image] : [])
          const imgs = reorderImages(imgsRaw.map(sanitize))
          return {
            id: it.id ?? i,
            name: it.name ?? it.title ?? 'Product',
            price: Number(it.price ?? 0),
            description: it.description ?? '',
            image: imgs[0] || '/images/placeholder.svg',
            slug: it.slug || undefined,
            images: imgs,
          }
        })
      }
      try {
        // Primary: Node backend via Vite proxy
        const res = await fetch('/api/products')
        if (!res.ok) throw new Error('API /api/products is not available')
        const data = await res.json()
        const mapped = mapProducts(data)
        if (!Array.isArray(mapped) || mapped.length === 0) throw new Error('Empty products from /api')
        products.value = mapped
      } catch (e) {
        console.warn('Falling back to 8000/products:', e?.message || e)
        try {
          const res2 = await fetch('http://127.0.0.1:8000/products')
          if (!res2.ok) throw new Error('Fallback /products failed')
          const data2 = await res2.json()
          products.value = mapProducts(data2)
        } catch (e2) {
          console.error('Failed to load products from both sources:', e2)
        }
      } finally {
        loading.value = false
      }
    })

    function add(p) { addToCart(p) }
    function asset(u){
      if(!u) return u
      const s = String(u)
      if(/^https?:\/\//i.test(s)) return s
      const rel = s.replace(/^\/+/, '')
      const base = String(import.meta.env.BASE_URL || '/')
      // Join base and rel without losing subpath deployments
      return base.replace(/\/+$/, '/') + rel
    }
    function imgFallback(ev, raw){
      try{
        const el = ev?.target
        if(!el) return
        const triedRaw = el.getAttribute('data-tried') || ''
        const tried = new Set(triedRaw.split('|').filter(Boolean))
        const candidates = []
        const a = asset(raw)
        if(a && !tried.has(a)) candidates.push(a)
        const s = String(raw || '')
        if(s.startsWith('/')){
          const alt8000 = 'http://127.0.0.1:8000' + s
          if(!tried.has(alt8000)) candidates.push(alt8000)
          const alt3000 = 'http://localhost:3000' + s
          if(!tried.has(alt3000)) candidates.push(alt3000)
        }
        const ph = asset('/images/placeholder.svg')
        if(!tried.has(ph)) candidates.push(ph)
        for(const c of candidates){
          if(c && c !== el.src){
            tried.add(c)
            el.setAttribute('data-tried', Array.from(tried).join('|'))
            el.src = c
            return
          }
        }
        el.onerror = null
      }catch{}
    }
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

    function gridThumb(p, i){
      try{
        const imgs = Array.isArray(p?.images) && p.images.length ? p.images.slice() : (p?.image ? [p.image] : [])
        const banned = ['chart','size','sizing','dimension','dimensions','guide','table','diagram','scheme','schematic','measure','measures','measuring']
        const filtered = imgs.filter(src => {
          const s = String(src||'').toLowerCase()
          if(/_(3|6)\.[a-z0-9]+$/i.test(s)) return false
          for(const b of banned){ if(s.includes(b)) return false }
          return true
        })
        const list = filtered.length ? filtered : imgs
        if(!list.length) return p?.image
        const idx = Number.isInteger(i) ? (i % list.length) : 0
        return list[idx]
      }catch{ return p?.image }
    }

    // Thumbnails to show under the main image (max 5, exclude size charts)
    function gridImages(p){
      try {
        const imgs = Array.isArray(p?.images) && p.images.length ? p.images.slice() : (p?.image ? [p.image] : [])
        const banned = ['chart','size','sizing','dimension','dimensions','guide','table','diagram','scheme','schematic','measure','measures','measuring']
        const filtered = imgs.filter(src => {
          const s = String(src||'').toLowerCase()
          for(const b of banned){ if(s.includes(b)) return false }
          return true
        })
        const list = filtered.length ? filtered : imgs
        return list.slice(0, 5)
      } catch { return [] }
    }

    function mainImage(p, i){
      try{
        const cur = selectedImage.value?.[p.id]
        return cur || gridThumb(p, i)
      }catch{ return gridThumb(p, i) }
    }

    function pickImage(p, src){
      try{
        const map = { ...(selectedImage.value || {}) }
        map[p.id] = src
        selectedImage.value = map
      }catch{}
    }

    return { products, loading, add, formatPrice, toggleFavorite, isFavorite, toggleCompare, isCompared, filteredProducts, asset, imgFallback, gridThumb, gridImages, mainImage, pickImage, selectedImage }
  },
}
</script>

<template>
  <div class="container">
    <h1>Товары</h1>

    <div v-if="loading" class="empty muted">Загрузка...</div>
    <div v-else-if="filteredProducts.length === 0" class="empty muted">Ничего не найдено</div>

    <div v-else class="grid-premium">
      <article v-for="(p, i) in filteredProducts" :key="p.id" class="card product-card">
        <div class="thumb-wrapper">
          <router-link :to="`/product/${p.slug || p.id}`" aria-label="Перейти к товару">
            <img
              :src="asset(mainImage(p, i))"
              @error="imgFallback($event, mainImage(p, i))"
              alt=""
              class="thumb"
            />
          </router-link>

          <button
            class="compare-btn"
            :class="{ active: isCompared(p.id) }"
            @click="toggleCompare(p)"
            aria-label="Сравнить"
            title="Сравнить"
          >
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M10 4h4v2h-4zM8 8h8v2H8zM6 12h12v2H6zM4 16h16v2H4z" />
            </svg>
          </button>

          <button
            class="favorite-btn"
            :class="{ active: isFavorite(p.id) }"
            @click="toggleFavorite(p)"
            aria-label="В избранное"
            title="В избранное"
          >
            <svg viewBox="0 0 24 24" width="20" height="20" :fill="isFavorite(p.id) ? 'red' : 'none'" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 21l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 6 4 4 6.5 4c1.74 0 3.41 1.01 4.22 2.09C11.09 5.01 12.76 4 14.5 4 17 4 19 6 19 8.5c0 3.78-3.4 6.86-8.55 11.18z" />
            </svg>
          </button>
        </div>

        <div class="thumbs-row" v-if="gridImages(p).length > 1">
          <img
            v-for="t in gridImages(p)"
            :key="t"
            :src="asset(t)"
            @error="imgFallback($event, t)"
            class="thumb-mini"
            :class="{ active: selectedImage[p.id] ? selectedImage[p.id] === t : gridThumb(p, i) === t }"
            alt=""
            @click="pickImage(p, t)"
            @mouseover="pickImage(p, t)"
          />
        </div>

        <div class="title">
          <router-link :to="`/product/${p.slug || p.id}`">{{ p.name }}</router-link>
        </div>
        <div class="desc">{{ p.description }}</div>
        <div class="row">
          <div class="price">{{ formatPrice(p.price) }} ₽</div>
          <button class="btn btn-primary" @click="add(p)">В корзину</button>
        </div>
      </article>
    </div>
  </div>
  
</template>

<style scoped>
/* Keep product thumbnails responsive and bounded */
.product-card { display: flex; flex-direction: column; }
.thumb-wrapper {
  position: relative;
  /* Keep a consistent image box that adapts to width */
  aspect-ratio: 4 / 5;
  /* Fallback max/min heights for legacy browsers */
  min-height: 180px;
  max-height: 360px;
  display: grid;
  place-items: center;
  overflow: hidden;
}
.thumb {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 12px;
  background: rgba(255,255,255,0.04);
}
.thumbs-row { display: flex; gap: 6px; margin-top: 8px; flex-wrap: wrap; }
.thumb-mini { width: 46px; height: 46px; object-fit: cover; border-radius: 8px; opacity: .85; border: 1px solid rgba(255,255,255,0.15); cursor: pointer; background: rgba(255,255,255,0.04); }
.thumb-mini.active { outline: 2px solid var(--primary); opacity: 1; }
.title { font-weight: 700; margin-top: 10px; }
.desc { color: var(--text-2); font-size: 13px; min-height: 30px; margin-top: 6px; }
.row { display: flex; justify-content: space-between; align-items: center; margin-top: 20px; }
.price { font-weight: 800; }
.empty { padding: 40px; text-align: center; }

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
