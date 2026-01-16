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
    '/pages/authentication/login-v1',
    '/pages/authentication/login-v2',
    '/pages/authentication/register-v1',
    '/pages/authentication/register-v2',
    '/pages/authentication/forgot-password-v1',
    '/pages/authentication/forgot-password-v2',
  ]

  // Check if user is authenticated (has access token cookie)
  const isAuthenticated = document.cookie.split('; ').some(cookie => cookie.startsWith('access_token='))

  // If route requires auth and user is not authenticated, redirect to login
  if (!publicRoutes.includes(to.path) && !isAuthenticated) {
    // Save the intended destination to redirect after login
    const returnUrl = to.fullPath

    next({
      path: '/login',
      query: { returnUrl }
    })
  } else if (to.path === '/login' && isAuthenticated) {
    // If user is already authenticated and tries to access login page, redirect to home
    next('/')
  } else {
    // Allow navigation
    next()
  }
})

export { router }
export default function (app) {
  app.use(router)
}
