<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

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
    // We need to call /api/auth/me to get user info
    const response = await axios.get('http://localhost:8001/api/auth/me', {
      withCredentials: true, // Important: send HttpOnly cookies
    })

    const user = response.data

    // Save user information to localStorage (for UI purposes only, token is in HttpOnly cookie)
    localStorage.setItem('user', JSON.stringify(user))

    // Role-based routing: if role is not "guest", redirect to home
    if (user.role && user.role !== 'guest') {
      router.push('/')
    }
    else {
      // Guest users - redirect to login
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
