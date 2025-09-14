<template>
  <div class="container">
    <h1>Товары</h1>

    <div v-if="favorites.length === 0" class="empty muted">Ничего не найдено</div>

    <div v-else class="list">
      <article v-for="p in favorites" :key="p.id" class="card item">
        <img :src="asset(p.image)" @error="imgFallback($event, p.image)" alt="" class="thumb" />

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
    return { favorites, add, formatPrice, removeFavorite, asset, imgFallback }
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
.row { display: flex; justify-content: space-between; align-items: center; padding-top: 10px ; }
.price { font-weight: 800; }
.actions { display: flex; gap: 8px; }
.empty { padding: 40px; text-align: center; }
</style>
