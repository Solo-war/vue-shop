<template>
  <div class="container">
    <h1>Товары</h1>

    <div v-if="favorites.length === 0" class="empty muted">Ничего не найдено</div>

    <div v-else class="list">
      <article v-for="(p, i) in favorites" :key="p.id" class="card item">
        <img :src="asset(thumbFor(p, i))" @error="imgFallback($event, thumbFor(p, i))" alt="" class="thumb" />

        <div class="info">
          <div class="title">{{ p.name }}</div>
          <div class="desc">{{ p.description }}</div>

          <div class="sizes">
            <span class="sizes-label">Размер:</span>
            <button
              v-for="s in sizeOptions"
              :key="s"
              class="size-btn"
              :class="{ active: getSize(p.id) === s }"
              @click.prevent="pickSize(p.id, s)"
            >{{ s }}</button>
          </div>

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
import { ref } from 'vue'
import { favorites, removeFavorite, setFavoriteSize } from '../favorites.js'
import { addToCart } from '../cart.js'

export default {
  setup() {
    const sizeOptions = ['S','M','L','XL','2XL']
    const selectedSize = ref({})
    function pickSize(id, size){
      const cur = { ...(selectedSize.value || {}) }
      cur[id] = size
      selectedSize.value = cur
      try { setFavoriteSize(id, size) } catch {}
    }
    function getSize(id){
      const s = selectedSize.value?.[id]
      if (s) return s
      const found = (favorites?.value || []).find((x) => x.id === id)
      return found?.size ?? null
    }
    function add(p) {
      const size = getSize(p.id)
      if (!size) { alert('Выберите размер'); return }
      addToCart(p, { size })
    }
    function formatPrice(v) { return Number(v).toLocaleString('ru-RU') }
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
          const alt = 'http://localhost:3000' + s
          if(!tried.has(alt)) candidates.push(alt)
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
    function thumbFor(p, i){
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
    return { favorites, add, formatPrice, removeFavorite, asset, imgFallback, thumbFor, sizeOptions, selectedSize, pickSize, getSize }
  },
}
</script>


<style scoped>
.list { display: flex; flex-direction: column; gap: 16px; }
.item { display: flex; gap: 12px; }
.thumb { width: 140px; height: 140px; object-fit: cover; border-radius: 12px; flex-shrink: 0; background: rgba(255,255,255,0.06); }
.info { display: flex; flex-direction: column; flex: 1;}
.title { font-weight: 700;  }
.desc { color: var(--text-2); font-size: 13px; margin: 4px 0; flex: 1; padding-top: 20px; }
.row { display: flex; justify-content: space-between; align-items: center; padding-top: 10px ; }
.price { font-weight: 800; }
.actions { display: flex; gap: 8px; }
.empty { padding: 40px; text-align: center; }

.sizes { display: flex; align-items: center; gap: 8px; margin-top: 10px; flex-wrap: wrap; }
.sizes-label { color: var(--text-2); font-size: 12px; }
.size-btn { cursor: pointer; padding: 6px 10px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.15); background: rgba(255,255,255,0.06); color: var(--text-1) }
.size-btn.active { background: var(--primary); color: #fff; border-color: var(--primary); }
</style>
