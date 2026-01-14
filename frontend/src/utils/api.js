import { ofetch } from 'ofetch'

export const $api = ofetch.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001/api',
  credentials: 'include', // Important: send HttpOnly cookies with requests
  async onRequest({ options }) {
    // HttpOnly cookies are automatically sent with credentials: 'include'
    // No need to manually add Authorization header
  },
  async onResponseError({ response }) {
    // Extract detail message from error response
    const errorMessage = response._data?.detail || response.statusText || 'An error occurred'

    // Throw a clean error with just the message
    const error = new Error(errorMessage)
    error.statusCode = response.status
    throw error
  },
})
