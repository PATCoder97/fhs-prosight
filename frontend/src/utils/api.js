import { ofetch } from 'ofetch'

export const $api = ofetch.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  credentials: 'include', // Important: send HttpOnly cookies with requests
  async onRequest({ options }) {
    // HttpOnly cookies are automatically sent with credentials: 'include'
    // No need to manually add Authorization header
  },
})
