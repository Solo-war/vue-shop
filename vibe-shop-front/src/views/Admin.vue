<template>
  <div class="admin">
    <h1>Админ‑панель</h1>

    <div class="tabs">
      <button :class="{active: tab==='orders'}" @click="tab='orders'">Заказы</button>
      <button :class="{active: tab==='payments'}" @click="tab='payments'">Платежи</button>
      <button class="right" @click="refresh">Обновить</button>
    </div>

    <div v-if="error" class="error">{{ error }}</div>

    <div v-if="tab==='orders'">
      <div v-if="loading" class="loading">Загрузка заказов...</div>
      <table v-else class="grid">
        <thead>
          <tr>
            <th>Заказ</th>
            <th>Адрес</th>
            <th>Сумма</th>
            <th>Создан</th>
            <th>Товары</th>
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
                <summary>{{ (o.items?.length||0) }} тов.</summary>
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

    <div v-else>
      <div v-if="loading" class="loading">Загрузка платежей...</div>
      <table v-else class="grid">
        <thead>
          <tr>
            <th>Заказ</th>
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/store/auth'

const auth = useAuthStore()
const tab = ref('orders')
const loading = ref(false)
const error = ref('')
const orders = ref([])
const payments = ref([])

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
  const r = await fetch(url, {
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
    const [o,p] = await Promise.all([
      fetchJSON('/api/admin/orders'),
      fetchJSON('/api/admin/payments'),
    ])
    orders.value = Array.isArray(o) ? o : []
    payments.value = Array.isArray(p) ? p : []
  }catch(e){
    error.value = 'Не удалось загрузить данные: ' + (e?.message || e)
  }finally{
    loading.value = false
  }
}

function refresh(){ load() }

onMounted(load)
</script>

<style scoped>
.admin{ max-width: 1200px; margin: 24px auto; padding: 0 16px; }
.tabs{ display:flex; gap:8px; align-items:center; margin-bottom:12px; }
.tabs .right{ margin-left:auto; }
button{ padding:8px 12px; border-radius:8px; border:1px solid #fff; background:#111; color: #fff; cursor:pointer; }
button.active{ background:#666; color:#fff; }
.loading{ padding:20px; color:#666; }
.error{ padding:10px; background:#fee; border:1px solid #fbb; color:#900; border-radius:8px; margin-bottom:10px; }
table.grid{ width:100%; border-collapse: collapse; background:#fff1; box-shadow: 0 6px 18px rgba(0,0,0,0.6); border-radius:10px; overflow:hidden; }
table.grid th, table.grid td{ padding:10px; border-bottom:1px solid #eee; text-align:left; vertical-align: top; }
table.grid thead th{ background:#fff3; font-weight:700; }
details summary{ cursor:pointer; }
</style>

