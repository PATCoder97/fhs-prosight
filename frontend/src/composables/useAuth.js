import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

/**
 * Authentication composable
 * Checks if user is authenticated and redirects to login if not
 * Similar to role check in welcome page
 */
export function useAuth(options = {}) {
  const {
    redirectToLogin = true,
    checkRole = null, // Optional: check specific role (e.g., 'guest', 'user', 'admin')
  } = options

  const router = useRouter()
  const user = ref(null)
  const isAuthenticated = ref(false)
  const isLoading = ref(true)

  // Helper function to get cookie value
  const getCookie = (name) => {
    const value = `; ${document.cookie}`
    const parts = value.split(`; ${name}=`)
    if (parts.length === 2) return parts.pop().split(';').shift()
    return null
  }

  // Check authentication
  const checkAuth = () => {
    // Check if access_token cookie exists
    const accessToken = getCookie('access_token')

    if (!accessToken) {
      isAuthenticated.value = false
      isLoading.value = false

      if (redirectToLogin) {
        // Redirect to login with return URL
        const returnUrl = window.location.pathname + window.location.search
        router.push({
          path: '/login',
          query: returnUrl !== '/' ? { returnUrl } : {}
        })
      }
      return false
    }

    // Check localStorage for user data
    const storedUser = localStorage.getItem('user')
    if (storedUser) {
      try {
        user.value = JSON.parse(storedUser)
        isAuthenticated.value = true

        // Optional: check specific role
        if (checkRole && user.value.role !== checkRole) {
          isAuthenticated.value = false
          if (redirectToLogin) {
            router.push('/login')
          }
          return false
        }
      } catch (error) {
        console.error('Failed to parse user data:', error)
        isAuthenticated.value = false
        if (redirectToLogin) {
          router.push('/login')
        }
        return false
      }
    } else {
      // Has cookie but no user data - might be first time after OAuth
      isAuthenticated.value = true
    }

    isLoading.value = false
    return true
  }

  // Run check on mount
  onMounted(() => {
    checkAuth()
  })

  return {
    user,
    isAuthenticated,
    isLoading,
    checkAuth,
  }
}
