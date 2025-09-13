import { ref, watch } from 'vue'

const stored = localStorage.getItem('cart')
export const cart = ref(stored ? JSON.parse(stored) : [])

// Следим за изменениями корзины и сохраняем в localStorage
watch(
  cart,
  (newCart) => {
    localStorage.setItem('cart', JSON.stringify(newCart))
  },
  { deep: true }
)

export function addToCart(product) {
  const found = cart.value.find((item) => item.id === product.id)
  if (found) {
    found.qty += 1
  } else {
    cart.value.push({ ...product, qty: 1 })
  }
}

export function removeFromCart(id) {
  cart.value = cart.value.filter((item) => item.id !== id)
}

export function clearCart() {
  cart.value = []
}
