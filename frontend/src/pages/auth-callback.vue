<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

definePage({
  meta: {
    layout: 'blank',
    public: true,
  },
})

const router = useRouter()

onMounted(() => {
  // Parse OAuth callback token from URL
  // Backend can return token via query (?token=...) or fragment (#token=...)
  const urlParams = new URLSearchParams(window.location.search)
  const hashParams = new URLSearchParams(window.location.hash.substring(1))

  const token = urlParams.get('token') || hashParams.get('token')
  const error = urlParams.get('error')

  if (error) {
    // Handle error: redirect to login with error message
    router.push({ path: '/login', query: { error } })
    return
  }

  if (token) {
    // Basic JWT validation: must have 3 parts (header.payload.signature)
    const parts = token.split('.')
    if (parts.length === 3) {
      // Token format is valid, save to localStorage
      localStorage.setItem('auth_token', token)

      // Redirect to dashboard or home
      router.push('/')
    } else {
      // Invalid token format
      router.push({ path: '/login', query: { error: 'invalid_token' } })
    }
  } else {
    // No token found
    router.push({ path: '/login', query: { error: 'no_token' } })
  }
})
</script>

<template>
  <div class="d-flex align-center justify-center" style="min-height: 100vh;">
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
