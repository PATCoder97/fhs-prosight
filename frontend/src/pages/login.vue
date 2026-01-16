<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AuthProvider from '@/views/pages/authentication/AuthProvider.vue'
import { useGenerateImageVariant } from '@core/composable/useGenerateImageVariant'
import authV2LoginIllustrationBorderedDark from '@images/pages/auth-v2-login-illustration-bordered-dark.png'
import authV2LoginIllustrationBorderedLight from '@images/pages/auth-v2-login-illustration-bordered-light.png'
import authV2LoginIllustrationDark from '@images/pages/auth-v2-login-illustration-dark.png'
import authV2LoginIllustrationLight from '@images/pages/auth-v2-login-illustration-light.png'
import authV2MaskDark from '@images/pages/misc-mask-dark.png'
import authV2MaskLight from '@images/pages/misc-mask-light.png'
import { VNodeRenderer } from '@layouts/components/VNodeRenderer'
import { themeConfig } from '@themeConfig'

definePage({
  meta: {
    layout: 'blank',
    public: true,
  },
})

const route = useRoute()
const router = useRouter()

// Toast notification
const toast = ref({
  show: false,
  message: '',
  color: 'error',
})

const showToast = (message, color = 'error') => {
  toast.value = {
    show: true,
    message,
    color,
  }
}

const errorMessages = {
  access_denied: 'Bạn đã hủy đăng nhập. Vui lòng thử lại.',
  invalid_token: 'Token không hợp lệ. Vui lòng thử đăng nhập lại.',
  no_token: 'Không nhận được token. Vui lòng thử đăng nhập lại.',
  auth_failed: 'Xác thực thất bại. Vui lòng thử đăng nhập lại.',
  default: 'Đã xảy ra lỗi. Vui lòng thử lại.',
}

onMounted(() => {
  const error = route.query.error
  if (error) {
    const message = errorMessages[error] || errorMessages.default
    showToast(message, 'error')

    // Clear error from URL (clean URL)
    router.replace({ query: {} })
  }
})

const authThemeImg = useGenerateImageVariant(authV2LoginIllustrationLight, authV2LoginIllustrationDark, authV2LoginIllustrationBorderedLight, authV2LoginIllustrationBorderedDark, true)
const authThemeMask = useGenerateImageVariant(authV2MaskLight, authV2MaskDark)
</script>

<template>
  <a href="javascript:void(0)">
    <div class="auth-logo d-flex align-center gap-x-3">
      <VNodeRenderer :nodes="themeConfig.app.logo" />
      <h1 class="auth-title">
        {{ themeConfig.app.title }}
      </h1>
    </div>
  </a>

  <VRow
    no-gutters
    class="auth-wrapper bg-surface"
  >
    <VCol
      md="8"
      class="d-none d-md-flex"
    >
      <div class="position-relative bg-background w-100 me-0">
        <div
          class="d-flex align-center justify-center w-100 h-100"
          style="padding-inline: 6.25rem;"
        >
          <VImg
            max-width="613"
            :src="authThemeImg"
            class="auth-illustration mt-16 mb-2"
          />
        </div>

        <img
          class="auth-footer-mask flip-in-rtl"
          :src="authThemeMask"
          alt="auth-footer-mask"
          height="280"
          width="100"
        >
      </div>
    </VCol>

    <VCol
      cols="12"
      md="4"
      class="auth-card-v2 d-flex align-center justify-center"
    >
      <VCard
        flat
        :max-width="500"
        class="mt-12 mt-sm-0 pa-6"
      >
        <VCardText>
          <h4 class="text-h4 mb-1">
            Chào mừng đến với <span class="text-capitalize">{{ themeConfig.app.title }}</span>! 👋🏻
          </h4>
          <p class="mb-6">
            Vui lòng đăng nhập bằng tài khoản Google hoặc GitHub
          </p>
        </VCardText>
        <VCardText>
          <AuthProvider />
        </VCardText>
      </VCard>
    </VCol>
  </VRow>

  <!-- Toast Notification -->
  <VSnackbar
    v-model="toast.show"
    :color="toast.color"
    :timeout="5000"
    location="top end"
    transition="slide-x-reverse-transition"
    rounded="lg"
    elevation="8"
    min-width="300"
    max-width="400"
  >
    <div class="d-flex align-center gap-3">
      <VIcon
        :icon="toast.color === 'success' ? 'tabler-circle-check' : toast.color === 'warning' ? 'tabler-alert-triangle' : 'tabler-circle-x'"
        size="24"
      />
      <span>{{ toast.message }}</span>
    </div>
    <template #actions>
      <VBtn
        variant="text"
        icon="tabler-x"
        size="small"
        @click="toast.show = false"
      />
    </template>
  </VSnackbar>
</template>

<style lang="scss">
@use "@core/scss/template/pages/page-auth";
</style>
