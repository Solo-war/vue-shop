import axios from 'axios'
const api = axios.create({ baseURL: '/api' })

export const fetchProducts = async () => {
  const r = await api.get('/products')
  return r.data
}