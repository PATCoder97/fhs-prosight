import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

/**
 * Composable to protect pages from guest users
 *
 * Usage in any protected page:
 * ```
 * <script setup>
 * import { useGuestProtection } from '@/composables/useGuestProtection'
 *
 * useGuestProtection()
 * </script>
 * ```
 *
 * This will automatically redirect guest users to /welcome page
 */
export function useGuestProtection() {
  const router = useRouter()

  onMounted(() => {
    const storedUser = localStorage.getItem('user')

    if (storedUser) {
      try {
        const user = JSON.parse(storedUser)

        // If user is guest, redirect to welcome page
        if (user.role === 'guest') {
          console.log('Guest user detected, redirecting to welcome page')
          router.push('/welcome')
        }
      }
      catch (error) {
        console.error('Failed to parse user data:', error)

        // If user data is corrupted, redirect to login
        router.push('/login')
      }
    }

    // If no user data, do nothing (let middleware handle redirect to login)
  })
}
