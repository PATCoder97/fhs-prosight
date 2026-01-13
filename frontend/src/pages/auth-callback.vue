<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { $api } from '@/utils/api'

definePage({
  meta: {
    layout: 'blank',
    public: true,
  },
})

const router = useRouter()

onMounted(async () => {
  try {
    // Backend now sets HttpOnly cookie and redirects to frontend
    // We need to call /auth/me to get user info
    const user = await $api('/auth/me')

    console.log('User info from /auth/me:', user)

    // Save user information to localStorage (for UI purposes only, token is in HttpOnly cookie)
    localStorage.setItem('user', JSON.stringify(user))

    // Role-based routing:
    // - Guest users -> welcome page
    // - Other users (user, admin, etc.) -> home page
    if (user.role && user.role === 'guest') {
      console.log('Redirecting to welcome - user is guest')
      router.push('/welcome')
    }
    else if (user.role) {
      console.log('Redirecting to home - user role:', user.role)
      router.push('/')
    }
    else {
      // No role assigned, redirect to login
      console.log('No role assigned - redirecting to login')
      router.push('/login')
    }
  }
  catch (error) {
    console.error('Failed to get user info:', error)

    // If we can't get user info, redirect to login with error
    router.push({ path: '/login', query: { error: 'auth_failed' } })
  }
})
</script>

<template>
  <div
    class="d-flex align-center justify-center"
    style="min-height: 100vh;"
  >
    <div class="d-flex flex-column align-center gap-4">
      <VProgressCircular
        indeterminate
        color="primary"
        size="64"
      />
      <span class="text-h6">Đang xử lý đăng nhập...</span>
    </div>
  </div>
</template>
