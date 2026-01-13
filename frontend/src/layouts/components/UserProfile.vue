<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { $api } from '@/utils/api'
import avatar1 from '@images/avatars/avatar-1.png'

const router = useRouter()

// User data from localStorage
const user = ref(null)

// Load user data from localStorage
onMounted(() => {
  const storedUser = localStorage.getItem('user')
  if (storedUser) {
    try {
      user.value = JSON.parse(storedUser)
    }
    catch (error) {
      console.error('Failed to parse user data:', error)
    }
  }
})

// Computed properties for user display
const userAvatar = computed(() => {
  const avatar = user.value?.avatar

  console.log('UserProfile - User avatar URL:', avatar)
  console.log('UserProfile - Full user data:', user.value)
  
  return avatar || avatar1
})

const userFullName = computed(() => user.value?.full_name || 'Guest User')

const userRole = computed(() => {
  const role = user.value?.role || 'guest'

  // Capitalize first letter
  return role.charAt(0).toUpperCase() + role.slice(1)
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

    // Continue with logout even if API call fails
  }
  finally {
    // Clear localStorage
    localStorage.removeItem('user')
    localStorage.removeItem('access_token') // In case it exists from old implementation

    // Redirect to login
    router.push('/login')
  }
}
</script>

<template>
  <VBadge
    dot
    location="bottom right"
    offset-x="3"
    offset-y="3"
    bordered
    color="success"
  >
    <VAvatar
      class="cursor-pointer"
      color="primary"
      variant="tonal"
    >
      <VImg
        v-if="user?.avatar"
        :src="userAvatar"
        referrerpolicy="no-referrer"
      />
      <VImg
        v-else
        :src="avatar1"
      />

      <!-- SECTION Menu -->
      <VMenu
        activator="parent"
        width="230"
        location="bottom end"
        offset="14px"
      >
        <VList>
          <!-- 👉 User Avatar & Name -->
          <VListItem>
            <template #prepend>
              <VListItemAction start>
                <VBadge
                  dot
                  location="bottom right"
                  offset-x="3"
                  offset-y="3"
                  color="success"
                >
                  <VAvatar
                    color="primary"
                    variant="tonal"
                  >
                    <VImg
                      v-if="user?.avatar"
                      :src="userAvatar"
                      referrerpolicy="no-referrer"
                    />
                    <VImg
                      v-else
                      :src="avatar1"
                    />
                  </VAvatar>
                </VBadge>
              </VListItemAction>
            </template>

            <VListItemTitle class="font-weight-semibold">
              {{ userFullName }}
            </VListItemTitle>
            <VListItemSubtitle>{{ userRole }}</VListItemSubtitle>
          </VListItem>

          <VDivider class="my-2" />

          <!-- 👉 Profile -->
          <VListItem link>
            <template #prepend>
              <VIcon
                class="me-2"
                icon="tabler-user"
                size="22"
              />
            </template>

            <VListItemTitle>Profile</VListItemTitle>
          </VListItem>

          <!-- 👉 Settings -->
          <VListItem link>
            <template #prepend>
              <VIcon
                class="me-2"
                icon="tabler-settings"
                size="22"
              />
            </template>

            <VListItemTitle>Settings</VListItemTitle>
          </VListItem>

          <!-- 👉 Pricing -->
          <VListItem link>
            <template #prepend>
              <VIcon
                class="me-2"
                icon="tabler-currency-dollar"
                size="22"
              />
            </template>

            <VListItemTitle>Pricing</VListItemTitle>
          </VListItem>

          <!-- 👉 FAQ -->
          <VListItem link>
            <template #prepend>
              <VIcon
                class="me-2"
                icon="tabler-help"
                size="22"
              />
            </template>

            <VListItemTitle>FAQ</VListItemTitle>
          </VListItem>

          <!-- Divider -->
          <VDivider class="my-2" />

          <!-- 👉 Logout -->
          <VListItem @click="handleLogout">
            <template #prepend>
              <VIcon
                class="me-2"
                icon="tabler-logout"
                size="22"
              />
            </template>

            <VListItemTitle>Logout</VListItemTitle>
          </VListItem>
        </VList>
      </VMenu>
      <!-- !SECTION -->
    </VAvatar>
  </VBadge>
</template>
