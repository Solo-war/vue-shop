<template>
  <div class="container">
    <h1>Сравнение товаров</h1>

    <div v-if="compareList.length === 0" class="empty muted">Список сравнения пуст</div>

    <div v-else class="compare-wrap card">
      <div class="table-scroll">
        <table class="compare-table">
          <thead>
            <tr>
              <th>Параметр</th>
              <th v-for="p in compareList" :key="p.id">
                <div class="head-cell">
                  <img :src="p.image" alt="" class="thumb" />
                  <div class="title">{{ p.name }}</div>
                  <button class="btn btn-secondary small" @click="removeFromCompare(p.id)">Удалить</button>
                </div>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td class="label">Цена</td>
              <td v-for="p in compareList" :key="p.id + '-price'" class="value">
                {{ formatPrice(p.price) }} ₽
              </td>
            </tr>
            <tr>
              <td class="label">Описание</td>
              <td v-for="p in compareList" :key="p.id + '-desc'" class="value desc">{{ p.description || '—' }}</td>
            </tr>
            <tr>
              <td class="label">Действия</td>
              <td v-for="p in compareList" :key="p.id + '-act'" class="value">
                <div class="actions">
                  <button class="btn btn-primary small" @click="addToCart(p)">В корзину</button>
                  <button class="btn btn-secondary small" @click="removeFromCompare(p.id)">Удалить</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import { compareList, removeFromCompare } from '@/compare.js'
import { addToCart } from '@/cart.js'

export default {
  setup() {
    const formatPrice = (v) => Number(v).toLocaleString('ru-RU')
    return { compareList, formatPrice, addToCart, removeFromCompare }
  },
}
</script>

<style scoped>
.empty { padding: 40px; text-align: center; }
.compare-wrap { overflow: hidden; }
.table-scroll { overflow-x: auto; }
.compare-table { width: 100%; border-collapse: collapse; min-width: 720px; }
.compare-table th, .compare-table td { border-bottom: 1px solid rgba(255,255,255,0.08); padding: 14px; text-align: left; vertical-align: top; }
.compare-table thead th:first-child { width: 180px; }
.head-cell { display: flex; align-items: center; gap: 10px; }
.thumb { width: 44px; height: 44px; border-radius: 10px; object-fit: cover; background: rgba(255,255,255,0.06); }
.title { font-weight: 700; }
.label { color: var(--text-2); font-weight: 600; }
.value { font-weight: 600; }
.desc { color: var(--text-2); font-weight: 400; }
.actions { display: flex; gap: 8px; }
.small { padding: 8px 10px; font-size: 14px; }
</style>
