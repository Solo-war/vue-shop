<template>
  <div class="admin">
    <h1>Админ-панель</h1>

    <div class="tabs">
      <button :class="{active: tab==='orders'}" @click="switchTab('orders')">Заказы</button>
      <button :class="{active: tab==='payments'}" @click="switchTab('payments')">Платежи</button>
      <button :class="{active: tab==='products'}" @click="switchTab('products')">Товары</button>
      <button class="right" @click="refresh">Обновить</button>
    </div>

    <div v-if="error" class="error">{{ error }}</div>

    <div v-if="tab==='orders'">
      <div v-if="loading" class="loading">Загрузка заказов...</div>
      <table v-else class="grid">
        <thead>
          <tr>
            <th>Номер</th>
            <th>Адрес</th>
            <th>Сумма</th>
            <th>Создан</th>
            <th>Состав</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="o in orders" :key="o.order_id">
            <td>{{ o.order_id }}</td>
            <td>
              <div>{{ o.address }}</div>
              <small v-if="o.geo_lat && o.geo_lon">lat: {{o.geo_lat}}, lon: {{o.geo_lon}}</small>
            </td>
            <td>{{ formatPrice(o.amount) }} ₽</td>
            <td>{{ formatDate(o.created_at) }}</td>
            <td>
              <details>
                <summary>{{ (o.items?.length||0) }} шт.</summary>
                <ul>
                  <li v-for="(it, i) in (o.items||[])" :key="i">
                    #{{ it.id }}: {{ it.name }} — {{ it.qty }} × {{ formatPrice(it.price) }} ₽
                  </li>
                </ul>
              </details>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else-if="tab==='payments'">
      <div v-if="loading" class="loading">Загрузка платежей...</div>
      <table v-else class="grid">
        <thead>
          <tr>
            <th>Номер</th>
            <th>Статус</th>
            <th>Сумма</th>
            <th>Карта</th>
            <th>Создан</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in payments" :key="p.order_id + p.created_at">
            <td>{{ p.order_id }}</td>
            <td>{{ p.status }}</td>
            <td>{{ formatPrice(p.amount) }} ₽</td>
            <td>{{ p.card_brand }} **** {{ p.card_last4 }}</td>
            <td>{{ formatDate(p.created_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else>
      <div v-if="loading" class="loading">Загрузка товаров...</div>
      <div v-else>
        <table class="grid">
          <thead>
            <tr>
              <th>#ID</th>
              <th>Название</th>
              <th>Цена</th>
              <th>Описание</th>
              <th>Фотографии</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in products" :key="p.id + ':' + p.index">
              <td>
                <div><b>ID:</b> {{ p.id }}</div>
                <div><small>index: {{ p.index }}</small></div>
              </td>
              <td>
                <input v-model="p.name" class="input" />
              </td>
              <td>
                <input v-model.number="p.price" type="number" min="0" step="1" class="input small" />
              </td>
              <td>
                <textarea v-model="p.description" class="input" rows="3"></textarea>
              </td>
              <td class="images">
                <div class="thumbs">
                  <img v-for="(img,i) in (p.images||[])" :key="i" :src="img" alt="" />
                </div>
                <div class="uploader">
                  <input type="file" multiple accept=".jpg,.jpeg,.png,.webp" @change="onFilesChange($event, p)" />
                  <button @click="uploadImages(p)" :disabled="!pendingFiles[p.id] || uploadingId===p.id">{{ uploadingId===p.id ? 'Загрузка...' : 'Заменить фото' }}</button>
                  <button class="danger" @click="deleteAllImages(p)" :disabled="deletingId===p.id">Удалить все</button>
                </div>
              </td>
              <td>
                <button @click="saveProduct(p)" :disabled="savingIndex===p.index">{{ savingIndex===p.index ? 'Сохранение...' : 'Сохранить' }}</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/store/auth'

const auth = useAuthStore()
const tab = ref('orders')
const loading = ref(false)
const error = ref('')
// Use configurable API base: '/api' in dev (Vite proxy) or a full URL via VITE_API_BASE
const API_BASE = import.meta.env?.VITE_API_BASE || '/api'
const orders = ref([])
const payments = ref([])
const products = ref([])
const pendingFiles = ref({}) // { [id]: FileList }
const uploadingId = ref(null)
const deletingId = ref(null)
const savingIndex = ref(null)

function formatPrice(v){
  const n = Number(v||0)
  return isFinite(n) ? n.toLocaleString('ru-RU') : v
}
function formatDate(s){
  try {
    return new Date(s).toLocaleString('ru-RU')
  } catch { return s }
}

async function fetchJSON(url){
  const full = url.startsWith('http')
    ? url
    : (url.startsWith('/api') ? (API_BASE + url.replace(/^\/api/, '')) : (API_BASE + url))
  const r = await fetch(full, {
    headers: auth.token ? { Authorization: `Bearer ${auth.token}` } : {},
  })
  if(!r.ok){
    const msg = await r.text()
    throw new Error(msg || r.statusText)
  }
  return await r.json()
}

async function load(){
  loading.value = true
  error.value = ''
  try{
    if(tab.value==='orders'){
      const o = await fetchJSON('/api/admin/orders')
      orders.value = Array.isArray(o) ? o : []
    } else if(tab.value==='payments'){
      const p = await fetchJSON('/api/admin/payments')
      payments.value = Array.isArray(p) ? p : []
    } else if(tab.value==='products'){
      const list = await fetchJSON('/api/admin/products')
      products.value = Array.isArray(list) ? list : []
    }
  }catch(e){
    error.value = 'Ошибка загрузки: ' + (e?.message || e)
  }finally{
    loading.value = false
  }
}

function refresh(){ load() }
function switchTab(t){ tab.value = (t==='orders' || t==='payments') ? t : 'orders'; load() }

function onFilesChange(ev, p){
  const files = ev.target.files
  if(files && files.length){
    pendingFiles.value = { ...pendingFiles.value, [p.id]: files }
  }
}

async function uploadImages(p){
  if(!pendingFiles.value[p.id] || !p.id){ return }
  uploadingId.value = p.id
  try{
    const fd = new FormData()
    Array.from(pendingFiles.value[p.id]).forEach(f => fd.append('files', f))
    const r = await fetch(`${API_BASE}/admin/products/${p.id}/images?replace=1`, {
      method: 'POST',
      headers: auth.token ? { Authorization: `Bearer ${auth.token}` } : {},
      body: fd,
    })
    if(!r.ok){ throw new Error(await r.text()) }
    await load()
    pendingFiles.value = { ...pendingFiles.value, [p.id]: null }
  }catch(e){
    alert('Ошибка загрузки: ' + (e?.message||e))
  }finally{
    uploadingId.value = null
  }
}

async function deleteAllImages(p){
  if(!p.id) return
  if(!confirm('Удалить все фото для товара #' + p.id + '?')) return
  deletingId.value = p.id
  try{
    const r = await fetch(`${API_BASE}/admin/products/${p.id}/images`, {
      method: 'DELETE',
      headers: auth.token ? { Authorization: `Bearer ${auth.token}` } : {},
    })
    if(!r.ok){ throw new Error(await r.text()) }
    await load()
  }catch(e){
    alert('Ошибка удаления: ' + (e?.message||e))
  }finally{
    deletingId.value = null
  }
}

async function saveProduct(p){
  savingIndex.value = p.index
  try{
    const r = await fetch(`${API_BASE}/admin/products/${p.index}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        ...(auth.token ? { Authorization: `Bearer ${auth.token}` } : {}),
      },
      body: JSON.stringify({ name: p.name, price: p.price, description: p.description }),
    })
    if(!r.ok){ throw new Error(await r.text()) }
    await load()
  }catch(e){
    alert('Ошибка сохранения: ' + (e?.message||e))
  }finally{
    savingIndex.value = null
  }
}

onMounted(load)
</script>

<style scoped>
.admin{ max-width: 1200px; margin: 24px auto; padding: 0 16px; }
.tabs{ display:flex; gap:8px; align-items:center; margin-bottom:12px; }
.tabs .right{ margin-left:auto; }
.tabs button:nth-child(3){ display:none; }
button{ padding:8px 12px; border-radius:8px; border:1px solid #fff; background:#111; color: #fff; cursor:pointer; }
button.active{ background:#666; color:#fff; }
.loading{ padding:20px; color:#666; }
.error{ padding:10px; background:#fee; border:1px solid #fbb; color:#900; border-radius:8px; margin-bottom:10px; }
table.grid{ width:100%; border-collapse: collapse; background:#fff1; box-shadow: 0 6px 18px rgba(0,0,0,0.6); border-radius:10px; overflow:hidden; }
table.grid th, table.grid td{ padding:10px; border-bottom:1px solid #eee; text-align:left; vertical-align: top; }
table.grid thead th{ background:#fff3; font-weight:700; }
details summary{ cursor:pointer; }
.input{ width:100%; padding:6px 8px; border-radius:6px; border:1px solid #ddd; background:#fff; color:#000; box-sizing:border-box; }
.input.small{ width: 120px; }
.images .thumbs{ display:flex; gap:6px; flex-wrap:wrap; margin-bottom:6px; }
.images img{ width:56px; height:56px; object-fit:cover; border-radius:6px; border:1px solid #ccc; background:#fff; }
.images .uploader{ display:flex; gap:6px; align-items:center; }
.danger{ background:#b30000; border-color:#b30000; }
</style>
