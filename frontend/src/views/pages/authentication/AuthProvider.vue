<script setup>
import { useTheme } from 'vuetify'

const { global } = useTheme()

const authProviders = [
  {
    name: 'Google',
    icon: 'tabler-brand-google-filled',
    color: '#db4437',
    colorInDark: '#db4437',
  },
  {
    name: 'GitHub',
    icon: 'tabler-brand-github-filled',
    color: '#272727',
    colorInDark: '#fff',
  },
]

const loginWithOAuth = provider => {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001'

  window.location.href = `${baseUrl}/api/auth/login/${provider.toLowerCase()}`
}
</script>

<template>
  <div class="d-flex flex-column gap-4">
    <VBtn
      v-for="provider in authProviders"
      :key="provider.name"
      block
      size="large"
      variant="outlined"
      :color="global.name.value === 'dark' ? provider.colorInDark : provider.color"
      @click="loginWithOAuth(provider.name)"
    >
      <VIcon
        :icon="provider.icon"
        start
      />
      Đăng nhập với {{ provider.name }}
    </VBtn>
  </div>
</template>
