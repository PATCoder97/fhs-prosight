import { ofetch } from 'ofetch'

// Runtime API base URL detection
// Priority: 1) Window config, 2) Environment variable, 3) Relative path (production), 4) Localhost (dev)
function getApiBaseUrl() {
  // Development mode: Use environment variable or localhost
  if (import.meta.env.DEV) {
    return import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001/api'
  }

  // Production mode: Always use /api which nginx will proxy to backend
  // This works on any domain without hardcoding
  return '/api'
}

export const $api = ofetch.create({
  baseURL: getApiBaseUrl(),
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
