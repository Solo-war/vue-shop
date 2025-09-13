import { defineStore } from 'pinia'
import axios from 'axios'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem('token') || null,
  }),
  actions: {
    async login(username, password) {
      const res = await axios.post(
        'http://127.0.0.1:8000/token',
        new URLSearchParams({
          username,
          password,
        })
      )
      this.token = res.data.access_token
      localStorage.setItem('token', this.token)
      await this.fetchUser()
    },
    async register(username, password) {
      try {
        const response = await axios.post('http://127.0.0.1:8000/register', {
          username,
          password,
        })
        return response.data
      } catch (error) {
        throw error
      }
    },
    async fetchUser() {
      if (!this.token) return
      const res = await axios.get('http://127.0.0.1:8000/me', {
        headers: { Authorization: `Bearer ${this.token}` },
      })
      this.user = res.data
    },
    logout() {
      this.user = null
      this.token = null
      localStorage.removeItem('token')
    },
  },
})
