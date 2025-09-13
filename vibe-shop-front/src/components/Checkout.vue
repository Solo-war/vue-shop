<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { cart, clearCart } from '../cart.js'

const router = useRouter()
const address = ref('')
const suggestions = ref([])
// Разрешаем отправку только если выбран адрес из подсказок DaData
const isAddressValid = ref(false)
const delivery = ref(null)
const orderId = ref(null)
const amount = ref(null)
const error = ref(null)

// 👉 здесь вставь свой API-ключ от Dadata
const DADATA_TOKEN = "8973b8a331798cdfc97a2af042393f8c65c1a5a7"

// Загружаем подсказки при вводе
async function fetchSuggestions(query) {
  if (!query || query.length < 3) { 
    suggestions.value = []
    isAddressValid.value = false
    return
  }

  try {
    const res = await fetch("https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/address", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": "Token " + DADATA_TOKEN,
      },
      body: JSON.stringify({ query, count: 5 })
    })

    if (!res.ok) throw new Error("Ошибка подсказок")

    const data = await res.json()
    suggestions.value = data.suggestions.map(s => s.value)
    if (!suggestions.value.includes(address.value)) {
      isAddressValid.value = false
    }
  } catch (e) {
    console.error(e)
    suggestions.value = []
    isAddressValid.value = false
  }
}

// Отправка заказа
async function submitOrder() {
  if (!address.value) {
    error.value = "Введите адрес доставки"
    return
  }

  if (!isAddressValid.value) {
    error.value = "ВВедите адресс из списка"
    return
  }

  try {
    const res = await fetch("http://127.0.0.1:8000/checkout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        address: address.value,
        items: cart.value.map(item => ({
          id: item.id,
          name: item.name,
          price: item.price,
          qty: item.qty
        }))
      })
    })

    // читаем JSON только один раз
    let data = {}
    try {
      data = await res.json()
    } catch (e) {
      console.error("Не удалось распарсить JSON:", e)
    }

    console.log("Ответ сервера:", res.status, data)

    if (!res.ok) {
      throw new Error(data?.detail || "Ошибка при оформлении заказа")
    }

    // сохраняем данные заказа
    orderId.value = data.order_id
    amount.value = data.amount
    error.value = null

    // редиректим на оплату
    await router.push({
      name: "pay",
      query: { 
        order_id: String(data.order_id), 
        amount: String(data.amount) 
      }
    })

    // очищаем корзину
    clearCart()
  } catch (err) {
    error.value = err.message
  }
}

</script>

<template>
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
            @input="(isAddressValid = false, fetchSuggestions(address))"
          />
        </label>

        <!-- список подсказок -->
        <ul v-if="suggestions.length" class="suggestions">
          <li
            v-for="s in suggestions"
            :key="s"
            @click="(address = s, isAddressValid = true, suggestions = [])"
          >
            {{ s }}
          </li>
        </ul>

        <button @click="submitOrder">Подтвердить заказ</button>

        <div v-if="error" class="error">{{ error }}</div>
      </div>

      <div v-else>
        <h2>Спасибо за заказ!</h2>
        <p>Ваш заказ будет доставлен примерно в <strong>{{ delivery }}</strong>.</p>
        <button @click="router.push('/')">На главную</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page {
  padding: 32px 0;
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
  background: #fff;
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
  background: #f0f0f0;
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
  background: #4caf50;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  color: white;
  cursor: pointer;
  transition: background 0.2s ease;
}

button:hover {
  background: #45a049;
}

.error {
  color: #e74c3c;
  margin-top: 10px;
}
</style>
