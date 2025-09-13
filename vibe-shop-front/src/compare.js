// src/compare.js
import { ref, watch } from 'vue'

export const compareList = ref([])

// Toggle product in compare list
export function toggleCompare(product) {
  const idx = compareList.value.findIndex((it) => it.id === product.id)
  if (idx === -1) {
    compareList.value.push(product)
  } else {
    compareList.value.splice(idx, 1)
  }
}

// Check if product is in compare list
export function isCompared(id) {
  return compareList.value.some((it) => it.id === id)
}

// Remove by id
export function removeFromCompare(id) {
  compareList.value = compareList.value.filter((it) => it.id !== id)
}

// --- Persist in localStorage ---
if (typeof window !== 'undefined') {
  const saved = localStorage.getItem('compare')
  if (saved) {
    try {
      compareList.value = JSON.parse(saved)
    } catch {
      compareList.value = []
    }
  }

  watch(
    compareList,
    (val) => {
      localStorage.setItem('compare', JSON.stringify(val))
    },
    { deep: true },
  )
}

