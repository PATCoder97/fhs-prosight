import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

/**
 * Composable to protect pages - only ADMIN users can access
 *
 * Usage in admin-only pages:
 * ```
 * <script setup>
 * import { useAdminProtection } from '@/composables/useAdminProtection'
 *
 * useAdminProtection()
 * </script>
 * ```
 *
 * This will redirect:
 * - Unauthenticated users → /login
 * - Guest users → /welcome
 * - Regular users (non-admin) → / (home) with error message
 * - Only admin users can access the page
 */
export function useAdminProtection() {
  const router = useRouter()

  onMounted(() => {
    const storedUser = localStorage.getItem('user')

    if (!storedUser) {
      // No user data, redirect to login
      console.log('No user found, redirecting to login')
      router.push('/login')
      
      return
    }

    try {
      const user = JSON.parse(storedUser)

      // Check user role
      if (user.role === 'guest') {
        console.log('Guest user trying to access admin page, redirecting to welcome')
        router.push('/welcome')
      }
      else if (user.role !== 'admin') {
        console.log('Non-admin user trying to access admin page, redirecting to home')

        // TODO: Show toast/alert notification
        alert('⚠️ Bạn không có quyền truy cập trang này. Chỉ Admin mới được phép.')
        router.push('/')
      }

      // If role === 'admin', allow access (do nothing)
    }
    catch (error) {
      console.error('Failed to parse user data:', error)
      router.push('/login')
    }
  })
}
