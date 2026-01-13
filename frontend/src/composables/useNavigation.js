import { computed } from 'vue'

/**
 * Composable to filter navigation items based on user role
 *
 * Usage:
 * ```
 * import { useNavigation } from '@/composables/useNavigation'
 *
 * const { filterNavByRole } = useNavigation()
 * const filteredNav = filterNavByRole(navItems)
 * ```
 */
export function useNavigation() {
  /**
   * Get current user from localStorage
   */
  const getCurrentUser = () => {
    try {
      const storedUser = localStorage.getItem('user')
      if (storedUser) {
        return JSON.parse(storedUser)
      }
    }
    catch (error) {
      console.error('Failed to parse user data:', error)
    }
    return null
  }

  /**
   * Check if user has required role to see a navigation item
   * @param {string|string[]} requiredRole - Required role(s) to see the item
   * @param {string} userRole - Current user's role
   * @returns {boolean}
   */
  const hasRequiredRole = (requiredRole, userRole) => {
    if (!requiredRole) return true // No role requirement

    // If requiredRole is an array, check if user role is in the array
    if (Array.isArray(requiredRole)) {
      return requiredRole.includes(userRole)
    }

    // If requiredRole is a string, check exact match
    return requiredRole === userRole
  }

  /**
   * Filter navigation items based on user role
   * @param {Array} navItems - Navigation items array
   * @returns {Array} Filtered navigation items
   */
  const filterNavByRole = (navItems) => {
    const user = getCurrentUser()
    const userRole = user?.role || 'guest'

    return navItems
      .filter(item => {
        // Check if item has role requirement
        if (item.requireRole) {
          return hasRequiredRole(item.requireRole, userRole)
        }
        return true // Show item if no role requirement
      })
      .map(item => {
        // If item has children, filter them recursively
        if (item.children && item.children.length > 0) {
          return {
            ...item,
            children: filterNavByRole(item.children),
          }
        }
        return item
      })
      // Remove items with no visible children
      .filter(item => {
        if (item.children) {
          return item.children.length > 0
        }
        return true
      })
  }

  /**
   * Computed filtered navigation
   * @param {Array} navItems - Raw navigation items
   * @returns {ComputedRef<Array>} Filtered navigation items
   */
  const filteredNav = (navItems) => {
    return computed(() => filterNavByRole(navItems))
  }

  return {
    getCurrentUser,
    hasRequiredRole,
    filterNavByRole,
    filteredNav,
  }
}
