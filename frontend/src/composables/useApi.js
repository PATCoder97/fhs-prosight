import { createFetch } from '@vueuse/core'
import { destr } from 'destr'

// Runtime API base URL detection
function getApiBaseUrl() {
  // Production: Use relative path /api which nginx will proxy to backend
  if (import.meta.env.PROD) {
    return '/api'
  }
  // Development: Use VITE_API_BASE_URL or fallback to /api
  return import.meta.env.VITE_API_BASE_URL || '/api'
}

export const useApi = createFetch({
  baseUrl: getApiBaseUrl(),
  fetchOptions: {
    headers: {
      Accept: 'application/json',
    },
  },
  options: {
    refetch: true,
    async beforeFetch({ options }) {
      const accessToken = useCookie('accessToken').value
      if (accessToken) {
        options.headers = {
          ...options.headers,
          Authorization: `Bearer ${accessToken}`,
        }
      }

      return { options }
    },
    afterFetch(ctx) {
      const { data, response } = ctx

      // Parse data if it's JSON
      let parsedData = null
      try {
        parsedData = destr(data)
      }
      catch (error) {
        console.error(error)
      }

      return { data: parsedData, response }
    },
  },
})
