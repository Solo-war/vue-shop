<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { cart, clearCart } from '../cart.js'


onMounted(() => {
  window.scrollTo(0, 0) // сразу скроллит в начало
})

const router = useRouter()
const address = ref('')
const suggestions = ref([])
const selectedSuggestion = ref(null)

// Проверяем, что пользователь выбрал подсказку с номером дома
const isAddressValid = computed(() => {
  const s = selectedSuggestion.value
  return Boolean(s && s.value === address.value && s?.data?.house)
})

const delivery = ref(null)
const orderId = ref(null)
const amount = ref(null)
const error = ref(null)

// Подсказки DaData
const DADATA_TOKEN = '8973b8a331798cdfc97a2af042393f8c65c1a5a7'

async function fetchSuggestions(query) {
  if (!query || query.length < 3) {
    suggestions.value = []
    return
  }
  try {
    const res = await fetch('https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/address', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': 'Token ' + DADATA_TOKEN,
      },
      body: JSON.stringify({ query, count: 5 })
    })
    if (!res.ok) throw new Error('Не удалось получить подсказки')
    const data = await res.json()
    suggestions.value = data.suggestions
  } catch (e) {
    console.error(e)
    suggestions.value = []
  }
}

// Простейшая оценка срока доставки (по расстоянию до Новосибирска)
const NOVOSIB = { lat: 55.0084, lon: 82.9357 }
function toRad(v) { return v * Math.PI / 180 }
function haversine(lat1, lon1, lat2, lon2) {
  const R = 6371
  const dLat = toRad(lat2 - lat1)
  const dLon = toRad(lon2 - lon1)
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2
  return 2 * R * Math.asin(Math.sqrt(a))
}
const distanceKmComputed = computed(() => {
  const s = selectedSuggestion.value
  const lat = Number.parseFloat(s?.data?.geo_lat)
  const lon = Number.parseFloat(s?.data?.geo_lon)
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) return 0
  return Math.round(haversine(lat, lon, NOVOSIB.lat, NOVOSIB.lon))
})
const showEta = computed(() => Boolean(selectedSuggestion.value?.data?.house && distanceKmComputed.value > 0))
const days = computed(() => {
  const items = cart.value
  if (!Array.isArray(items) || items.length === 0) return 1
  const totalQty = items.reduce((sum, it) => sum + (it?.qty ?? 1), 0)
  const uniqueIds = new Set(items.map(it => it?.id)).size
  let d = 1 + Math.ceil(totalQty * 0.5) + Math.ceil(uniqueIds * 0.3) + Math.ceil(distanceKmComputed.value / 700)
  return Math.max(1, Math.min(28, d))
})
const estimatedDate = computed(() => {
  const dt = new Date()
  dt.setDate(dt.getDate() + days.value)
  const dd = String(dt.getDate()).padStart(2, '0')
  const mm = String(dt.getMonth() + 1).padStart(2, '0')
  const yyyy = dt.getFullYear()
  return `${dd}.${mm}.${yyyy}`
})

async function submitOrder() {
  if (!address.value) {
    error.value = 'Введите адрес доставки'
    return
  }
  if (!isAddressValid.value) {
    error.value = 'Пожалуйста, выберите точный адрес с номером дома'
    return
  }
  try {
    const res = await fetch('http://127.0.0.1:8000/checkout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        address: address.value,
        geo_lat: parseFloat(selectedSuggestion.value?.data?.geo_lat) || null,
        geo_lon: parseFloat(selectedSuggestion.value?.data?.geo_lon) || null,
        items: cart.value.map(item => ({
          id: item.id,
          name: item.name,
          price: item.price,
          qty: item.qty
        }))
      })
    })
    let data = {}
    try {
      data = await res.json()
    } catch (e) {
      console.error('Не удалось разобрать JSON:', e)
    }
    if (!res.ok) throw new Error(data?.detail || 'Не удалось оформить заказ')

    orderId.value = data.order_id
    amount.value = data.amount
    error.value = null

    const eta = estimatedDate.value
    await router.push({
      name: 'pay',
      query: {
        order_id: String(data.order_id),
        amount: String(data.amount),
        address: address.value,
        eta: eta,
      }
    })

    clearCart()
  } catch (err) {
    error.value = err.message
  }
}
</script>

<template >
<div class="back">
  <div class="page">
    <div class="inner">
      <h1>Оформление заказа</h1>

      <div v-if="!delivery">
        <label>
          Адрес доставки:
          <input
            v-model="address"
            type="text"
            placeholder="Введите адрес"
            @input="(selectedSuggestion = null, fetchSuggestions(address))"
          />
        </label>

        <!-- Подсказки адреса -->
        <ul v-if="suggestions.length" class="suggestions">
          <li
            v-for="s in suggestions"
            :key="s.value"
            @click="(address = s.value, selectedSuggestion = s, suggestions = [])"
          >
            {{ s.value }}
          </li>
        </ul>

        <div class="eta" v-if="showEta">
          Срок доставки: <strong>{{ days }}</strong> дн. (до {{ estimatedDate }})
        </div>

        <button :disabled="!isAddressValid" @click="submitOrder">Оформить заказ</button>
        <div v-if="!isAddressValid && address" class="hint">Пожалуйста, выберите точный адрес с номером дома</div>

        <div v-if="error" class="error">{{ error }}</div>
      </div>

      <div v-else>
        <h2>Заказ оформлен!</h2>
        <p>Доставка будет осуществлена по адресу <strong>{{ delivery }}</strong>.</p>
        <button @click="router.push('/')">На главную</button>
      </div>
    </div>
  </div>
</div>
</template>

<style scoped>

.page {
  padding: 32px;
  padding-bottom: 1200px;
}

.inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 16px;
}

.suggestions {
  list-style: none;
  margin: 0;
  padding: 6px;
  border: 1px solid #ccc;
  background: #111;
  max-height: 180px;
  overflow-y: auto;
  position: absolute;
  z-index: 10;
  width: 300px;
}
.suggestions li {
  padding: 6px 10px;
  cursor: pointer;
  
  
}
.suggestions li:hover {
background: linear-gradient(135deg, var(--brand), var(--brand-2))
}

h1 {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 12px;
}

input {
  display: block;
  margin: 8px 0 20px;
  padding: 10px;
  width: 100%;
  max-width: 400px;
  border: 1px solid #ccc;
  border-radius: 6px;
}

button {
  padding: 10px 18px;
  background: linear-gradient(135deg, #ef4444, #f97316);
  border: none;
  border-radius: 8px;
  font-weight: 600;
  color: white;
  cursor: pointer;
  transition: background 0.2s ease;
}

button:hover {
  background: linear-gradient(135deg, #dd3b3b, #ce5e0e)
}

.error {
  color: #e74c3c;
  margin-top: 10px;
}

.eta {
  margin: 10px 0 16px;
  color: #374151;
}

.hint {
  margin-top: 8px;
  color: #6b7280;
  font-size: 13px;
}

</style>
