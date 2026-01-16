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

  // Always allow public routes
  if (publicRoutes.includes(to.path)) {
    next()
    return
  }

  // For all other routes, allow navigation and let the page check authentication
  // This way OAuth callback can complete and set cookies first
  next()
})

export { router }
export default function (app) {
  app.use(router)
}
