<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { $api } from '@/utils/api'

// Define page metadata for routing
definePage({
  meta: {
    layout: 'blank',  // Use blank layout (no navigation, no sidebar)
    public: true,
  },
})

const router = useRouter()
const user = ref(null)

onMounted(() => {
  // Load user from localStorage
  const storedUser = localStorage.getItem('user')
  if (storedUser) {
    try {
      user.value = JSON.parse(storedUser)

      // If user is not guest, redirect to home
      if (user.value.role !== 'guest') {
        router.push('/')
      }
    }
    catch (error) {
      console.error('Failed to parse user data:', error)
      router.push('/login')
    }
  }
  else {
    // No user data, redirect to login
    router.push('/login')
  }
})

// Logout handler
const handleLogout = async () => {
  try {
    // Call backend logout endpoint to clear HttpOnly cookie
    await $api('/auth/logout', {
      method: 'POST',
    })
  }
  catch (error) {
    console.error('Logout error:', error)
  }
  finally {
    // Clear localStorage
    localStorage.removeItem('user')
    localStorage.removeItem('access_token')

    // Redirect to login
    router.push('/login')
  }
}
</script>

<template>
  <div class="auth-wrapper d-flex align-center justify-center pa-4">
    <VCard class="auth-card pa-4 pt-7" max-width="900">
      <VCardText class="text-center pa-8">
        <!-- Welcome Icon -->
        <VIcon icon="tabler-confetti" size="80" color="primary" class="mb-4" />

        <!-- Welcome Message -->
        <h1 class="text-h4 font-weight-bold mb-2">
          Chào mừng đến với FHS Pro Sight! 👋
        </h1>

        <p class="text-h6 text-medium-emphasis mb-6">
          Xin chào, {{ user?.full_name || 'Guest' }}!
        </p>

        <VDivider class="my-6" />

        <!-- Guest Information -->
        <VAlert type="info" variant="tonal" class="text-start mb-6">
          <template #prepend>
            <VIcon icon="tabler-info-circle" />
          </template>

          <div class="text-body-1">
            <strong>Tài khoản Guest</strong>
            <p class="mt-2">
              Bạn hiện đang sử dụng tài khoản Guest với quyền truy cập giới hạn.
              Để sử dụng đầy đủ các tính năng của hệ thống, vui lòng liên hệ quản trị viên để nâng cấp tài khoản.
            </p>
          </div>
        </VAlert>

        <!-- Contribution QR -->
        <VCard variant="outlined" color="warning" class="mb-6 text-center">
          <VCardText class="pa-6">
            <div class="d-flex align-center justify-center mb-4">
              <VIcon icon="tabler-qrcode" size="40" color="warning" class="me-3" />
              <h3 class="text-h5">
                Quét mã QR để đóng góp
              </h3>
            </div>

            <!-- QR Image -->
            <VImg src="/images/qr.png" max-width="260" aspect-ratio="1" class="mx-auto rounded-lg elevation-2"
              alt="QR đóng góp FHS Pro Sight" cover />

            <p class="text-body-2 text-medium-emphasis mt-4">
              Nội dung chuyển khoản là gmail đăng nhập của bạn để quản trị viên dễ dàng xác nhận.
            </p>
          </VCardText>
        </VCard>


        <!-- Logout Button -->
        <VBtn color="error" variant="outlined" size="large" prepend-icon="tabler-logout" @click="handleLogout">
          Đăng xuất
        </VBtn>
      </VCardText>
    </VCard>
  </div>
</template>

<style scoped lang="scss">
@use "@core/scss/template/pages/page-auth.scss";

.auth-wrapper {
  min-block-size: 100vh;
  min-block-size: 100dvh;
}

.auth-card {
  z-index: 1;
}

.text-medium-emphasis {
  opacity: 0.7;
}
</style>
