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
  // Parse OAuth callback response from URL
  // Backend returns: access_token, token_type, and user object as query params
  const urlParams = new URLSearchParams(window.location.search)
  const hashParams = new URLSearchParams(window.location.hash.substring(1))

  const error = urlParams.get('error') || hashParams.get('error')

  if (error) {
    // Handle error: redirect to login with error message
    router.push({ path: '/login', query: { error } })
    return
  }

  // Get access_token from URL params
  const accessToken = urlParams.get('access_token') || hashParams.get('access_token')

  // Get user data from URL params
  const userId = urlParams.get('user_id') || hashParams.get('user_id')
  const userRole = urlParams.get('user_role') || hashParams.get('user_role')
  const userEmail = urlParams.get('user_email') || hashParams.get('user_email')
  const userFullName = urlParams.get('user_full_name') || hashParams.get('user_full_name')
  const userAvatar = urlParams.get('user_avatar') || hashParams.get('user_avatar')
  const userProvider = urlParams.get('user_provider') || hashParams.get('user_provider')

  if (!accessToken || !userId) {
    // No token or user data found
    router.push({ path: '/login', query: { error: 'no_token' } })
    return
  }

  // Basic JWT validation: must have 3 parts (header.payload.signature)
  const parts = accessToken.split('.')
  if (parts.length !== 3) {
    // Invalid token format
    router.push({ path: '/login', query: { error: 'invalid_token' } })
    return
  }

  // Save access token to localStorage
  localStorage.setItem('access_token', accessToken)

  // Save user information to localStorage
  const user = {
    id: userId,
    role: userRole,
    email: userEmail,
    full_name: userFullName,
    avatar: userAvatar,
    provider: userProvider,
  }
  localStorage.setItem('user', JSON.stringify(user))

  // Role-based routing: if role is not "guest", redirect to home
  if (userRole && userRole !== 'guest') {
    router.push('/')
  } else {
    // Guest users - you can redirect them to a different page or show a message
    router.push('/login')
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
