// src/favorites.js
import { ref, watch } from 'vue'

export const favorites = ref([])

// Добавление / удаление
export function toggleFavorite(product) {
  const index = favorites.value.findIndex((item) => item.id === product.id)
  if (index === -1) {
    favorites.value.push(product) // добавляем
  } else {
    favorites.value.splice(index, 1) // удаляем
  }
}

// Проверка: товар в избранном?
export function isFavorite(id) {
  return favorites.value.some((item) => item.id === id)
}

// Удаление по id
export function removeFavorite(id) {
  favorites.value = favorites.value.filter((item) => item.id !== id)
}

// --- Сохраняем в localStorage ---
if (typeof window !== 'undefined') {
  const saved = localStorage.getItem('favorites')
  if (saved) {
    try {
      favorites.value = JSON.parse(saved)
    } catch {
      favorites.value = []
    }
  }

  watch(
    favorites,
    (val) => {
      localStorage.setItem('favorites', JSON.stringify(val))
    },
    { deep: true },
  )
}
