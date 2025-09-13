<script setup>
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const order_id = route.query.order_id || ''
const amount = route.query.amount || 0

const card_number = ref('')
const exp_month = ref('')
const exp_year = ref('')
const name = ref('')
const result = ref(null)
const error = ref(null)

// Автоформатирование номера карты
watch(card_number, (val) => {
  // Убираем все пробелы
  let digits = val.replace(/\D/g, '')
  // Разбиваем по 4 символа
  let parts = digits.match(/.{1,4}/g)
  card_number.value = parts ? parts.join(' ') : ''
})

async function pay() {
  if (!card_number.value) {
    alert('Введите тестовый номер карты (например 0000 0000 0000 0000)')
    return
  }
  try {
    const res = await fetch('http://127.0.0.1:8000/pay-mock', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        order_id,
        card_number: card_number.value.replace(/\s+/g, ''), // отправляем без пробелов
        exp_month: exp_month.value,
        exp_year: exp_year.value,
        name: name.value
      })
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || JSON.stringify(data))
    result.value = data
    localStorage.removeItem('cart')
  } catch (e) {
    console.error(e)
    error.value = e.message
  }
}
</script>

<template>
  <div class="pay-page">
    <div class="card">
      <h1 class="title">Оплата заказа</h1>
      <p class="order-info">
        Заказ: <strong>#{{ order_id }}</strong><br />
        Сумма: <strong>{{ amount }} ₽</strong>
      </p>

      <div class="form">
        <label>
          Номер карты
          <input v-model="card_number" maxlength="19" placeholder="0000 0000 0000 0000" />
        </label>

        <div class="row">
          <label>
            MM
            <input v-model="exp_month" placeholder="MM" maxlength="2" />
          </label>
          <label>
            YY
            <input v-model="exp_year" placeholder="YY" maxlength="2" />
          </label>
        </div>

        <label>
          Имя на карте
          <input v-model="name" placeholder="IVAN IVANOV" />
        </label>

        <button class="btn" @click="pay">💳 Оплатить</button>
      </div>
    <div v-if="result" class="result">
      <h3 :class="result.status === 'succeeded' ? 'success' : 'error'">
        {{ result.status === 'succeeded' ? '✅ Оплата прошла успешно' : '❌ Ошибка оплаты' }}
      </h3>
      <p>{{ result.message }}</p>
      <p v-if="result.transaction_id">ID транзакции: <strong>{{ result.transaction_id }}</strong></p>

      <p class="delivery">
        Ожидаемое время доставки: 
        <strong>{{ result.delivery_time }}</strong>
      </p>

      <button class="btn-secondary" @click="$router.push('/')">На главную</button>
    </div>

    <div v-if="error" class="error">{{ error }}</div>
  </div>
  </div>
</template>

<style scoped>
.pay-page {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px 20px;
  background: #f9fafb;
  min-height: 10vh;
}

.card {
  background: #fff;
  padding: 30px;
  border-radius: 16px;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.08);
  max-width: 420px;
  width: 100%;
}

.title {
  font-size: 22px;
  font-weight: 600;
  margin-bottom: 12px;
  text-align: center;
}

.order-info {
  font-size: 16px;
  margin-bottom: 20px;
  text-align: center;
  color: #374151;
}

.form label {
  display: block;
  font-size: 14px;
  margin-bottom: 12px;
  color: #374151;
}

input {
  width: 100%;
  padding: 10px 12px;
  margin-top: 4px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  transition: border 0.2s;
}

input:focus {
  border-color: #2563eb;
}

.row {
  display: flex;
  gap: 12px;
}

.btn {
  width: 100%;
  padding: 12px;
  margin-top: 10px;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.btn:hover {
  background: #1d4ed8;
}

.btn-secondary {
  margin-top: 15px;
  padding: 10px;
  width: 100%;
  border: 1px solid #d1d5db;
  background: #f3f4f6;
  border-radius: 8px;
  cursor: pointer;
  font-size: 15px;
  transition: background 0.2s;
}

.btn-secondary:hover {
  background: #e5e7eb;
}

.result {
  margin-top: 20px;
  padding: 15px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 10px;
}

.error {
  margin-top: 15px;
  color: #dc2626;
  text-align: center;
  font-weight: 500;
}
</style>
