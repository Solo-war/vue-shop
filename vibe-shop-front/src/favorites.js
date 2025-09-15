// src/favorites.js
import { ref, watch } from 'vue'

export const favorites = ref([])

// Добавить/убрать из избранного. Новые — наверх. Сохраняем размер.
export function toggleFavorite(product, options = {}) {
  const index = favorites.value.findIndex((item) => item.id === product.id)
  if (index === -1) {
    const size = options.size ?? product.size ?? null
    const toAdd = size ? { ...product, size } : { ...product }
    favorites.value.unshift(toAdd) // новый — в начало
  } else {
    favorites.value.splice(index, 1)
  }
}

// Проверка: товар в избранном
export function isFavorite(id) {
  return favorites.value.some((item) => item.id === id)
}

// Удалить по id
export function removeFavorite(id) {
  favorites.value = favorites.value.filter((item) => item.id !== id)
}

// Обновить/установить размер у товара в избранном
export function setFavoriteSize(id, size) {
  const idx = favorites.value.findIndex((it) => it.id === id)
  if (idx !== -1) {
    const cur = favorites.value[idx]
    favorites.value.splice(idx, 1, { ...cur, size: size ?? null })
  }
}

// --- Персист в localStorage ---
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

