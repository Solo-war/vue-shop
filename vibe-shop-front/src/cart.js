import { ref, watch } from 'vue'

let storageKey = 'cart'
const stored = localStorage.getItem(storageKey)
export const cart = ref(stored ? JSON.parse(stored) : [])

// Следим за изменениями корзины и сохраняем в localStorage
watch(
  cart,
  (newCart) => {
    try { localStorage.setItem(storageKey, JSON.stringify(newCart)) } catch {}
  },
  { deep: true }
)

export function addToCart(product, options = {}) {
  const size = options.size ?? product.size ?? null
  const found = cart.value.find((item) => item.id === product.id && ((item.size ?? null) === (size ?? null)))
  if (found) {
    found.qty += 1
  } else {
    const toAdd = { ...product, qty: 1 }
    if (size) toAdd.size = size
    cart.value.push(toAdd)
  }
}

export function removeFromCart(id, size = null) {
  cart.value = cart.value.filter((item) => !(item.id === id && ((item.size ?? null) === (size ?? null))))
}

export function clearCart() {
  cart.value = []
}

// ---- Персист корзины при входе/выходе ----
function mergeCarts(primary, secondary) {
  const map = new Map()
  for (const it of Array.isArray(primary) ? primary : []) {
    const key = `${it.id}::${it.size ?? ''}`
    map.set(key, { ...it })
  }
  for (const it of Array.isArray(secondary) ? secondary : []) {
    const key = `${it.id}::${it.size ?? ''}`
    const cur = map.get(key)
    if (cur) {
      cur.qty = (cur.qty ?? 1) + (it.qty ?? 1)
    } else {
      map.set(key, { ...it })
    }
  }
  return Array.from(map.values())
}

export function syncCartOnLogin(username) {
  if (!username) return
  const userKey = `cart:${username}`
  let userStored = []
  try {
    const raw = localStorage.getItem(userKey)
    userStored = raw ? JSON.parse(raw) : []
  } catch {}
  const merged = mergeCarts(userStored, cart.value)
  cart.value = merged
  storageKey = userKey
  try { localStorage.setItem(storageKey, JSON.stringify(cart.value)) } catch {}
}

export function syncCartOnLogout() {
  storageKey = 'cart'
  try { localStorage.setItem(storageKey, JSON.stringify(cart.value)) } catch {}
}
