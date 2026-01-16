import { setupLayouts } from 'virtual:meta-layouts'
import { createRouter, createWebHistory } from 'vue-router/auto'

function recursiveLayouts(route) {
  if (route.children) {
    for (let i = 0; i < route.children.length; i++)
      route.children[i] = recursiveLayouts(route.children[i])

    return route
  }

  return setupLayouts([route])[0]
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior(to) {
    if (to.hash)
      return { el: to.hash, behavior: 'smooth', top: 60 }

    return { top: 0 }
  },
  extendRoutes: pages => [
    ...[...pages].map(route => recursiveLayouts(route)),
  ],
})

// Route Guard: Protect routes that require authentication
router.beforeEach((to, from, next) => {
  // Public routes that don't require authentication
  const publicRoutes = [
    '/',  // Allow home page (OAuth callback redirects here)
    '/login',
    '/register',
    '/forgot-password',
    '/auth-callback',  // OAuth callback handler
    '/pages/authentication/login-v1',
    '/pages/authentication/login-v2',
    '/pages/authentication/register-v1',
    '/pages/authentication/register-v2',
    '/pages/authentication/forgot-password-v1',
    '/pages/authentication/forgot-password-v2',
  ]

  // Helper to get cookie value
  const getCookie = (name) => {
    const value = `; ${document.cookie}`
    const parts = value.split(`; ${name}=`)
    if (parts.length === 2) return parts.pop().split(';').shift()
    return null
  }

  // Always allow public routes
  if (publicRoutes.includes(to.path)) {
    next()
    return
  }

  // For all other routes, check authentication
  const accessToken = getCookie('access_token')

  if (!accessToken) {
    // No auth token - redirect to login with returnUrl
    next({
      path: '/login',
      query: { returnUrl: to.fullPath }
    })
    return
  }

  // Has token - allow access
  next()
})

export { router }
export default function (app) {
  app.use(router)
}
