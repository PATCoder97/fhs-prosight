import { defineStore } from 'pinia'
import { $api } from '@/utils/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    loaded: false, // đã check session chưa
  }),

  getters: {
    isLoggedIn: (state) => !!state.user,
    currentUser: (state) => state.user,
  },

  actions: {
    /**
     * Fetch current user from backend
     * Gọi API /auth/me để kiểm tra HttpOnly cookie
     * Cache kết quả để không gọi lại nhiều lần
     */
    async fetchMe() {
      // Nếu đã load rồi thì không gọi lại
      if (this.loaded) return

      try {
        const response = await $api('/auth/me', {
          method: 'GET',
          credentials: 'include', // Gửi HttpOnly cookie
        })

        this.user = response
        this.loaded = true
      } catch (error) {
        // Cookie không hợp lệ hoặc đã hết hạn
        console.log('Not authenticated:', error)
        this.user = null
        this.loaded = true
      }
    },

    /**
     * Logout user
     * Clear cookie và reset state
     */
    async logout() {
      try {
        await $api('/auth/logout', {
          method: 'POST',
          credentials: 'include',
        })
      } catch (error) {
        console.error('Logout error:', error)
      } finally {
        // Clear state
        this.user = null
        this.loaded = false

        // Clear localStorage (nếu có)
        localStorage.removeItem('user')
        localStorage.removeItem('access_token')
      }
    },

    /**
     * Reset store (dùng khi cần force reload)
     */
    reset() {
      this.user = null
      this.loaded = false
    },
  },
})
