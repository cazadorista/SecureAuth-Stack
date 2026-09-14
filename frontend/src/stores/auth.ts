import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    isInitialized: false,
    authenticated: false,
    user: null as Record<string, any> | null
  }),
  actions: {
    async checkAuth() {
      try {
        const res = await fetch('/api/auth/me', { credentials: 'include' })
        const data = await res.json()
        
        this.authenticated = data.authenticated
        this.user = data.user || null
      } catch (err) {
        console.error('Nie udało się pobrać sesji z BFF:', err)
        this.authenticated = false
        this.user = null
      } finally {
        this.isInitialized = true
      }
    },
    login() {
      const currentUrl = encodeURIComponent(window.location.href)
      window.location.href = `/api/auth/login?redirect=${currentUrl}`
    },
    logout() {
      window.location.href = '/api/auth/logout'
    }
  }
})