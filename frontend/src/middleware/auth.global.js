/**
 * Global authentication middleware
 * Protects routes from unauthorized access based on user role
 */

export default defineNuxtRouteMiddleware((to, from) => {
  // Skip middleware on server-side
  if (process.server) return

  // Public routes that don't require authentication
  const publicRoutes = ['/login', '/auth-callback', '/welcome']

  // Admin-only routes
  const adminRoutes = ['/user-manager']

  // Check if current route is public
  const isPublicRoute = publicRoutes.some(route => to.path.startsWith(route))

  // Check if current route is admin-only
  const isAdminRoute = adminRoutes.some(route => to.path.startsWith(route))

  // Get user from localStorage
  let user = null
  try {
    const storedUser = localStorage.getItem('user')
    if (storedUser) {
      user = JSON.parse(storedUser)
    }
  } catch (error) {
    console.error('Failed to parse user data:', error)
  }

  // If no user and trying to access protected route, redirect to login
  if (!user && !isPublicRoute) {
    console.log('No user found, redirecting to login')
    
    return navigateTo('/login')
  }

  // If user exists
  if (user) {
    // Guest users can only access welcome page
    if (user.role === 'guest') {
      // Allow access to public routes
      if (isPublicRoute) {
        return
      }

      // Redirect to welcome page if trying to access other routes
      if (to.path !== '/welcome') {
        console.log('Guest trying to access protected route, redirecting to welcome')
        
        return navigateTo('/welcome')
      }
    }

    // Non-admin users cannot access admin routes
    if (isAdminRoute && user.role !== 'admin') {
      console.log('Non-admin user trying to access admin route, redirecting to home')
      
      return navigateTo('/')
    }

    // Authenticated users (non-guest) cannot access login page
    if (user.role !== 'guest' && to.path === '/login') {
      console.log('Authenticated user trying to access login, redirecting to home')
      
      return navigateTo('/')
    }

    // Authenticated non-guest users cannot access welcome page
    if (user.role !== 'guest' && to.path === '/welcome') {
      console.log('Non-guest user trying to access welcome, redirecting to home')
      
      return navigateTo('/')
    }
  }
})
