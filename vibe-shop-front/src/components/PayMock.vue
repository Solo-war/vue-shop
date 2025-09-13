<script setup>
import { ref, watch, computed, onBeforeUnmount } from 'vue'
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

// Delayed receipt generation state
const isGeneratingReceipt = ref(false)
const receiptSecondsLeft = ref(0)
const receiptTotalSeconds = ref(0)
const receipt = ref(null)
let receiptTimerId = null
let receiptCountdownId = null

// Confetti celebration state
const showConfetti = ref(false)
const confettiPieces = ref([])
let confettiHideTimerId = null


const rawNumber = computed(() => card_number.value.replace(/\s+/g, ''))

function luhnCheck(num) {
  if (!/^\d+$/.test(num)) return false
  let sum = 0
  let dbl = false
  for (let i = num.length - 1; i >= 0; i--) {
    let d = Number(num[i])
    if (dbl) { d *= 2; if (d > 9) d -= 9 }
    sum += d; dbl = !dbl
  }
  return sum % 10 === 0
}

function detectBrand(num) {
  if (/^4\d{15}$/.test(num)) return 'visa'
  if (/^\d{16}$/.test(num)) {
    const first2 = parseInt(num.slice(0,2), 10)
    const first4 = parseInt(num.slice(0,4), 10)
    const first6 = parseInt(num.slice(0,6), 10)
    if (first2 >= 51 && first2 <= 55) return 'mastercard'
    if (first4 >= 2221 && first4 <= 2720) return 'mastercard'
    if (first6 >= 222100 && first6 <= 272099) return 'mastercard'
  }
  if (/^\d{16}$/.test(num)) {
    const first4 = parseInt(num.slice(0,4), 10)
    if (first4 >= 2200 && first4 <= 2204) return 'mir'
  }
  return 'unknown'
}

const brand = computed(() => detectBrand(rawNumber.value))
// Accept any 16-digit card that falls into a known brand range (Visa/MasterCard/MIR),
// without enforcing the Luhn check (mock environment).
const isCardValid = computed(() => {
  const n = rawNumber.value
  const b = brand.value
  return b !== 'unknown' && /^\d{16}$/.test(n)
})

const isExpValid = computed(() => {
  const mm = exp_month.value; const yy = exp_year.value
  return /^\d{2}$/.test(mm) && /^\d{2}$/.test(yy) && Number(mm) >= 1 && Number(mm) <= 12
})
const isNameValid = computed(() => name.value.trim().length >= 2)
const canPay = computed(() => isCardValid.value && isExpValid.value && isNameValid.value)

//
watch(card_number, (val) => {
  // РЈР±РёСЂР°РµРј РІСЃРµ РїСЂРѕР±РµР»С‹
  let digits = val.replace(/\D/g, '')
  // Р Р°Р·Р±РёРІР°РµРј РїРѕ 4 СЃРёРјРІРѕР»Р°
  let parts = digits.match(/.{1,4}/g)
  card_number.value = parts ? parts.join(' ') : ''
})

async function pay() {
  if (!canPay.value) {
    alert('Enter valid card details (Visa/MasterCard/MIR)')
    return
  }
  try {
    const res = await fetch('http://127.0.0.1:8000/pay-mock', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        order_id,
        card_number: card_number.value.replace(/\s+/g, ''), // no spaces
        exp_month: exp_month.value,
        exp_year: exp_year.value,
        name: name.value
      })
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || JSON.stringify(data))
    result.value = data
    localStorage.removeItem('cart')

    if (data?.status === 'succeeded') {
      startReceiptGeneration()
      launchConfetti()
    }
  } catch (e) {
    console.error(e)
    error.value = e.message
  }
}

function startReceiptGeneration() {
  // Random delay between 10 and 60 seconds (inclusive)
  const delaySec = Math.floor(Math.random() * (60 - 10 + 1)) + 10
  receiptSecondsLeft.value = delaySec
  receiptTotalSeconds.value = delaySec
  isGeneratingReceipt.value = true

  // Countdown
  if (receiptCountdownId) clearInterval(receiptCountdownId)
  receiptCountdownId = setInterval(() => {
    if (receiptSecondsLeft.value > 0) receiptSecondsLeft.value--
  }, 1000)

  // Finalize
  if (receiptTimerId) clearTimeout(receiptTimerId)
  receiptTimerId = setTimeout(() => {
    generateReceipt()
  }, delaySec * 1000)
}

function launchConfetti() {
  const count = 120
  confettiPieces.value = Array.from({ length: count }, (_, i) => ({
    id: i,
    left: Math.random() * 100,
    delay: Math.floor(Math.random() * 350),
    duration: 2200 + Math.floor(Math.random() * 2200),
    hue: Math.floor(Math.random() * 360),
    w: 6 + Math.floor(Math.random() * 6),
    h: 8 + Math.floor(Math.random() * 10),
    spinDir: Math.random() > 0.5 ? 1 : -1,
  }))
  showConfetti.value = true
  if (confettiHideTimerId) clearTimeout(confettiHideTimerId)
  confettiHideTimerId = setTimeout(() => {
    showConfetti.value = false
  }, 4500)
}

function maskCard(num) {
  const n = String(num || '')
  if (n.length < 4) return '**** **** **** ****'
  return `**** **** **** ${n.slice(-4)}`
}

function generateReceipt() {
  isGeneratingReceipt.value = false
  if (receiptCountdownId) clearInterval(receiptCountdownId)

  const now = new Date()
  const ts = now.toLocaleString()
  const txn = result.value?.transaction_id || Math.random().toString(36).slice(2, 12)

  receipt.value = {
    orderId: String(order_id || '').trim(),
    amount: Number(amount || 0),
    transactionId: txn,
    paidAt: ts,
    cardMasked: maskCard(rawNumber.value),
    name: name.value.trim() || 'CUSTOMER',
    status: 'PAID'
  }
}

function downloadReceiptTxt() {
  if (!receipt.value) return
  const r = receipt.value
  const lines = [
    'Vibe Shop — Payment Receipt',
    '-----------------------------------',
    `Status: ${r.status}`,
    `Paid at: ${r.paidAt}`,
    `Order ID: #${r.orderId}`,
    `Transaction ID: ${r.transactionId}`,
    `Amount: ${r.amount} RUB`,
    `Card: ${r.cardMasked}`,
    `Name: ${r.name}`,
  ]
  const blob = new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `receipt_${r.orderId || r.transactionId}.txt`
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

function printReceipt() {
  window.print()
}

onBeforeUnmount(() => {
  if (receiptTimerId) clearTimeout(receiptTimerId)
  if (receiptCountdownId) clearInterval(receiptCountdownId)
  if (confettiHideTimerId) clearTimeout(confettiHideTimerId)
})
</script>

<template>
  <div class="pay-page">
    <div class="card">
      <h1 class="title">Payment</h1>
      <p class="order-info">
        Order: <strong>#{{ order_id }}</strong><br />
        Amount: <strong>{{ amount }} RUB</strong>
      </p>

      <div class="form">
        <label>
          Card number
          <input v-model="card_number" maxlength="19" placeholder="0000 0000 0000 0000" />
          <small v-if="brand !== 'unknown'" style="color:#374151;display:block;margin-top:4px;">Brand: {{ brand.toUpperCase() }}</small>
          <small v-if="card_number && !isCardValid" style="color:#dc2626;display:block;margin-top:4px;">Invalid card number</small>
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
          Name on card
          <input v-model="name" placeholder="IVAN IVANOV" />
        </label>

        <button class="btn" @click="pay">Pay</button>
      </div>
    <div v-if="result" class="result">
      <h3 :class="result.status === 'succeeded' ? 'success' : 'error'">
        {{ result.status === 'succeeded' ? 'Payment succeeded' : 'Payment error' }}
      </h3>
      <p>{{ result.message }}</p>
      <p v-if="result.transaction_id">Transaction ID: <strong>{{ result.transaction_id }}</strong></p>

      <p class="delivery">
        Estimated delivery date:
        <strong>{{ result.delivery_time }}</strong>
      </p>

      <div v-if="result.status === 'succeeded'" class="receipt-block">
        <div v-if="isGeneratingReceipt" class="receipt-progress">
          <span>Generating receipt…</span>
          <span v-if="receiptSecondsLeft"> (~{{ receiptSecondsLeft }}s)</span>
          <div class="bar"><div class="fill" :style="{ width: (receiptTotalSeconds ? (100 - Math.round((receiptSecondsLeft / receiptTotalSeconds) * 100)) : 0) + '%' }"></div></div>
        </div>

        <div v-else-if="receipt" class="receipt">
          <h4>Payment Receipt</h4>
          <div class="line"><strong>Status:</strong> {{ receipt.status }}</div>
          <div class="line"><strong>Paid at:</strong> {{ receipt.paidAt }}</div>
          <div class="line"><strong>Order ID:</strong> #{{ receipt.orderId }}</div>
          <div class="line"><strong>Transaction ID:</strong> {{ receipt.transactionId }}</div>
          <div class="line"><strong>Amount:</strong> {{ receipt.amount }} RUB</div>
          <div class="line"><strong>Card:</strong> {{ receipt.cardMasked }}</div>
          <div class="line"><strong>Name:</strong> {{ receipt.name }}</div>
          <div class="receipt-actions">
            <button class="btn" @click="downloadReceiptTxt">Download .txt</button>
            <button class="btn-secondary" @click="printReceipt">Print / Save PDF</button>
          </div>
        </div>
      </div>

      <button class="btn-secondary" @click="$router.push('/')">Back to Home</button>
    </div>

    <div v-if="error" class="error">{{ error }}</div>

    <!-- Confetti celebration overlay -->
    <div v-if="showConfetti" class="confetti">
      <div
        v-for="p in confettiPieces"
        :key="p.id"
        class="confetti-piece"
        :style="{
          left: p.left + '%',
          '--delay': p.delay + 'ms',
          '--dur': p.duration + 'ms',
          '--hue': p.hue,
          '--w': p.w + 'px',
          '--h': p.h + 'px',
          '--spinDir': p.spinDir
        }"
      >
        <div class="confetti-piece-inner"></div>
      </div>
    </div>
  </div>
  </div>
</template>

<style scoped>
.pay-page { display: flex; justify-content: center; align-items: center; padding: 40px 20px; min-height: 10vh; }

.card { max-width: 460px; width: 100%; }

.title {
  font-size: 22px;
  font-weight: 600;
  margin-bottom: 12px;
  text-align: center;
}

.order-info { font-size: 16px; margin-bottom: 20px; text-align: center; color: var(--text-2); }

.form label { display: block; font-size: 14px; margin-bottom: 12px; color: var(--text-2); }

input { width: 100%; margin-top: 4px; }

.row {
  display: flex;
  gap: 12px;
}

.btn { width: 100%; margin-top: 10px; }

.btn-secondary { margin-top: 15px; width: 100%; }

.result { margin-top: 20px; padding: 15px; background: rgba(34,197,94,0.12); border: 1px solid rgba(34,197,94,0.35); border-radius: 12px; }

.error { margin-top: 15px; color: var(--danger); text-align: center; font-weight: 600; }

/* Receipt styles */
.receipt-block { margin-top: 12px; }
.receipt-progress { color: #374151; font-size: 14px; }
.receipt-progress .bar { margin-top: 8px; height: 8px; background: rgba(255,255,255,0.08); border-radius: 999px; overflow: hidden; }
.receipt-progress .fill { height: 100%; background: linear-gradient(135deg, #22c55e, #14b8a6); width: 0%; transition: width 0.3s ease; }
.receipt { border: 1px dashed rgba(255,255,255,0.18); border-radius: 12px; padding: 12px; background: rgba(255,255,255,0.04); }
.receipt h4 { margin: 0 0 8px; }
.receipt .line { margin: 4px 0; }
.receipt-actions { display: flex; gap: 8px; margin-top: 10px; }

/* Confetti */
.confetti {
  position: fixed;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
  z-index: 9999;
}
.confetti-piece {
  position: absolute;
  top: -12px;
  left: 0;
  width: var(--w);
  height: var(--h);
  transform: translateY(-100vh);
  animation: confetti-fall var(--dur) cubic-bezier(.2,.7,.2,1) var(--delay) forwards;
}
.confetti-piece-inner {
  width: 100%;
  height: 100%;
  background: hsl(var(--hue), 90%, 60%);
  border-radius: 2px;
  display: block;
  transform-origin: center;
  animation: confetti-spin var(--dur) linear var(--delay) forwards;
}

@keyframes confetti-fall {
  0%   { transform: translateY(-100vh); opacity: 0; }
  10%  { opacity: 1; }
  100% { transform: translateY(105vh); opacity: 1; }
}
@keyframes confetti-spin {
  to { transform: rotate(calc(720deg * var(--spinDir))); }
}
</style>







