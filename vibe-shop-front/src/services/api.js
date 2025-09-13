import axios from 'axios'
const api = axios.create({ baseURL: '/api' })

export const fetchProducts = async () => {
  const r = await api.get('/products')
  return r.data
}

export const fetchReviews = async (productId) => {
  const r = await api.get(`/reviews/${productId}`)
  return r.data
}

export const addReview = async (productId, payload) => {
  const r = await api.post(`/reviews/${productId}`, payload)
  return r.data
}
