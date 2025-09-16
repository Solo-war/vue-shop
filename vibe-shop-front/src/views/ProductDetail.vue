<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { addToCart } from '@/cart.js'
import { toggleFavorite as toggleFavoriteRaw, isFavorite } from '@/favorites.js'
import { toggleCompare, isCompared } from '@/compare.js'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const error = ref('')
const products = ref([])
const product = ref(null)
const activeIdx = ref(0)
const sizeOptions = ['S','M','L','XL','2XL']
const selectedSize = ref(null)
function toggleFavorite(p){
  if (!p) return
  if (!isFavorite(p.id)) {
    if (!selectedSize.value) { alert('Выберите размер'); return }
    toggleFavoriteRaw(p, { size: selectedSize.value })
  } else {
    toggleFavoriteRaw(p)
  }
}

function fmt(n){ return Number(n||0).toLocaleString('ru-RU') }
function asset(u){
  if(!u) return u
  const s = String(u)
  if(/^https?:\/\//i.test(s)) return s
  const rel = s.replace(/^\/+/, '')
  const base = String(import.meta.env.BASE_URL || '/')
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

async function load(){
  loading.value = true
  error.value = ''
  try{
    async function fetchAll(){
      try{
        const r = await fetch('/api/products')
        if(!r.ok) throw new Error('api 3000 down')
        return await r.json()
      }catch(e){
        const r2 = await fetch('http://127.0.0.1:8000/products')
        return await r2.json()
      }
    }
    function sanitize(u){
      const s = String(u||'')
      return s || '/images/placeholder.svg'
    }
    // Prefer images that look like a full-length man facing forward by filename keywords
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
        // Bonus for combinations suggesting full-length front
        if((s.includes('full') || s.includes('полный') || s.includes('рост')) && (s.includes('front') || s.includes('анфас') || s.includes('лиц'))) score += 2
        for(const d of demote){ if(s.includes(d)) score -= 10 }
        return { src, i, score }
      })
      scored.sort((a,b) => b.score - a.score || a.i - b.i)
      return scored.map(x => x.src)
    }
    const data = await fetchAll()
    const mapped = (Array.isArray(data) ? data : []).map((it,i) => {
      const imgsRaw = Array.isArray(it.images) && it.images.length ? it.images : (it.image ? [it.image] : [])
      const imgs = reorderImages(imgsRaw.map(sanitize))
      return {
        ...it,
        id: it.id ?? i,
        name: it.name ?? it.title ?? 'Product',
        price: Number(it.price ?? 0),
        description: it.description ?? '',
        image: imgs[0] || '/images/placeholder.svg',
        images: imgs,
      }
    })
    products.value = mapped
    const keyRaw = String(route.params.key ?? '')
    // Prefer match by numeric id when key is digits
    let found = null
    if (/^\d+$/.test(keyRaw)) {
      const pid = Number(keyRaw)
      found = products.value.find(p => Number(p.id) === pid)
      if(!found && Number.isInteger(pid) && pid >= 0 && pid < products.value.length){
        found = products.value[pid]
      }
    }
    // Fallback by slug (case-insensitive)
    if(!found){
      const key = keyRaw.toLowerCase()
      found = products.value.find(p => String(p.slug||'').toLowerCase() === key)
    }
    if(!found){
      error.value = 'Товар не найден'
    }else{
      product.value = found
      activeIdx.value = 0
    }
  }catch(e){
    error.value = String(e?.message || e)
  }finally{
    loading.value = false
  }
}

function add(){
  if(!product.value) return
  if(!selectedSize.value){ alert('Выберите размер'); return }
  addToCart(product.value, { size: selectedSize.value })
}
function pickSize(s){ selectedSize.value = s }

onMounted(load)

watch(() => route.params.key, () => {
  load()
})

const imagesRaw = computed(() => {
  const arr = product.value?.images
  const list = Array.isArray(arr) && arr.length ? arr : (product.value?.image ? [product.value.image] : [])
  return list
})
// Deduplicate images to avoid repeated thumbnails and duplicate keys
const images = computed(() => {
  const mapped = imagesRaw.value.map(asset).filter(Boolean)
  return Array.from(new Set(mapped))
})

function setActive(i){ activeIdx.value = i }

function goBack(){ router.back() }
</script>

<template>
  <div class="container product">
    <button class="back" @click="goBack">← Назад</button>

    <div v-if="loading" class="muted">Загрузка...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="!product" class="muted">Товар не найден</div>
    <div v-else class="grid">
      <div class="gallery">
        <div class="main">
          <img :src="images[activeIdx]" @error="imgFallback($event, imagesRaw[activeIdx] || product?.image)" alt="" />
        </div>
        <div v-if="images.length > 1" class="thumbs">
          <button v-for="(src,i) in images" :key="src + '-' + i" :class="['thumb', {active: i===activeIdx}]" @click="setActive(i)">
            <img :src="src" @error="imgFallback($event, imagesRaw[i] || product?.image)" alt="" />
          </button>
        </div>
      </div>

      <div class="info">
        <h1 class="title">{{ product.name }}</h1>
        <div class="price">{{ fmt(product.price) }} ₽</div>
        <p class="desc">{{ product.description }}</p>

        <div class="sizes">
          <span class="sizes-label">Размер:</span>
          <button
            v-for="s in sizeOptions"
            :key="s"
            class="size-btn"
            :class="{ active: selectedSize === s }"
            @click="pickSize(s)"
          >{{ s }}</button>
        </div>

        <div class="actions">
          <button class="btn btn-primary" @click="add">В корзину</button>
          <button class="icon" :class="{active: isFavorite(product.id)}" @click="toggleFavorite(product)" title="В избранное">
            ❤
          </button>
          <button class="icon" :class="{active: isCompared(product.id)}" @click="toggleCompare(product)" title="Сравнить">
            ≈
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.product{ max-width: 1100px; margin: 16px auto; }
.back { 
  margin-bottom: 12px; 
  background: rgba(0, 0, 0, 0.05); /* чуть заметный фон */
  border: 0; 
  border-radius: 8px;
  color: var(--text-2); 
  cursor: pointer; 
  padding: 6px 12px; 
  transition: background 0.2s ease;
}

.back:hover {
  background: rgba(0, 0, 0, 0.01); /* светлее при наведении */
}

.grid{ display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 24px; }
.gallery{ display: flex; flex-direction: column; align-items: center; }
/* Responsive photo window that respects image aspect ratio
   and keeps it within sensible min/max bounds */
.gallery .main{
  background: rgba(255,255,255,0.04);
  border-radius: 16px;
  overflow: hidden;
  /* Portrait viewport */
  width: min(100%, 540px);
  aspect-ratio: 3 / 4; /* width / height => portrait */
  display: grid;
  place-items: center;
}
.gallery .main img{
  width: 100%;
  height: 100%;
  object-fit: cover; /* fill portrait area */
  display: block;
}
.thumbs{ display: flex; flex-wrap: wrap; justify-content: center; gap: 8px; margin-top: 10px; width: 100%; max-width: 645.6px; }
.thumb{ padding: 0; border: 2px solid transparent; border-radius: 10px; overflow:hidden; cursor:pointer; background: none; }
.thumb.active{ border-color: var(--brand); }
.thumb img{ width: 100%; height: 88px; object-fit: cover; display:block; }
.info .title{ font-weight: 800; margin: 0 0 6px; }
.price{ font-size: 20px; font-weight: 800; margin-bottom: 12px; }
.desc{ color: var(--text-2); white-space: pre-wrap; }
.actions{ margin-top: 16px; display:flex; gap:10px; align-items: center; }
.icon{ width: 40px; height: 40px; border-radius: 10px; border:1px solid rgba(255,255,255,0.2); background: rgba(255,255,255,0.06); color:#fff; cursor:pointer; padding: 5px;}
.icon.active{ background: rgba(255,0,0,0.15); border-color: rgba(255,0,0,0.3); }

.sizes{ display:flex; align-items:center; gap:8px; margin-top:12px; flex-wrap: wrap; }
.sizes-label{ color: var(--text-2); font-size: 12px; }
.size-btn{ cursor:pointer; padding:6px 10px; border-radius:10px; border:1px solid rgba(255,255,255,0.15); background: rgba(255,255,255,0.06); color: var(--text-1) }
.size-btn.active{ background: var(--primary); color:#fff; border-color: var(--primary); }

@media (max-width: 900px){
  .grid{ grid-template-columns: 1fr; }
  /* On small screens keep portrait ratio; width rules above already scale */
}
</style>
