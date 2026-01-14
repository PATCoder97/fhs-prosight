<script setup>
import { ref, onMounted } from 'vue'
import { useAdminProtection } from '@/composables/useAdminProtection'
import { $api } from '@/utils/api'

// Protect this page - only admin can access
useAdminProtection()

const users = ref([])
const loading = ref(false)

// LocalId dialog
const localIdDialog = ref(false)
const selectedUser = ref(null)
const newLocalId = ref('')
const localIdLoading = ref(false)

// Toast notification
const toast = ref({
  show: false,
  message: '',
  color: 'success',
})

const showToast = (message, color = 'success') => {
  toast.value = {
    show: true,
    message,
    color,
  }
}

// Load users from API
onMounted(async () => {
  await loadUsers()
})

const loadUsers = async () => {
  loading.value = true
  try {
    const response = await $api('/users')

    users.value = response.users || []
  }
  catch (error) {
    console.error('Failed to load users:', error)
    showToast('Không thể tải danh sách người dùng!', 'error')
  }
  finally {
    loading.value = false
  }
}

// Update user role
const updateUserRole = async (userId, newRole) => {
  try {
    const response = await $api(`/users/${userId}/role`, {
      method: 'PUT',
      body: JSON.stringify({ role: newRole }),
    })

    if (response.success) {
      // Update local data with response
      const user = users.value.find(u => u.id === userId)
      if (user && response.user) {
        user.role = response.user.role
      }

      showToast(response.message || 'Đã cập nhật role thành công!')
    }
  }
  catch (error) {
    console.error('Failed to update user role:', error)
    showToast('Cập nhật role thất bại!', 'error')
  }
}

// Open localId dialog
const openLocalIdDialog = (user) => {
  selectedUser.value = user
  newLocalId.value = user.localId || ''
  localIdDialog.value = true
}

// Update user localId
const updateUserLocalId = async () => {
  if (!selectedUser.value || !newLocalId.value.trim()) {
    showToast('Vui lòng nhập Local ID!', 'warning')
    return
  }

  localIdLoading.value = true
  try {
    const response = await $api(`/users/${selectedUser.value.id}/localId`, {
      method: 'PUT',
      body: JSON.stringify({ localId: newLocalId.value.trim() }),
    })

    if (response.success) {
      // Update local data with response
      const user = users.value.find(u => u.id === selectedUser.value.id)
      if (user && response.user) {
        user.localId = response.user.localId
      }

      showToast(response.message || 'Đã cập nhật Local ID thành công!')
      localIdDialog.value = false
      newLocalId.value = ''
      selectedUser.value = null
    }
  }
  catch (error) {
    console.error('Failed to update user localId:', error)
    showToast('Cập nhật Local ID thất bại!', 'error')
  }
  finally {
    localIdLoading.value = false
  }
}

// Close localId dialog
const closeLocalIdDialog = () => {
  localIdDialog.value = false
  newLocalId.value = ''
  selectedUser.value = null
}

// Get role color
const getRoleColor = role => {
  switch (role) {
  case 'admin': return 'error'
  case 'user': return 'primary'
  case 'guest': return 'warning'
  default: return 'default'
  }
}

// Get role icon
const getRoleIcon = role => {
  switch (role) {
  case 'admin': return 'tabler-shield-check'
  case 'user': return 'tabler-user'
  case 'guest': return 'tabler-user-question'
  default: return 'tabler-user'
  }
}
</script>

<template>
  <div>
    <VCard>
      <VCardTitle class="d-flex align-center justify-space-between">
        <div class="d-flex align-center gap-2">
          <VIcon
            icon="tabler-users-group"
            size="28"
          />
          <span>User Management</span>
        </div>
        <VChip
          color="error"
          variant="tonal"
        >
          <VIcon
            icon="tabler-shield-lock"
            start
          />
          Admin Only
        </VChip>
      </VCardTitle>

      <VCardText>
        <VAlert
          type="info"
          variant="tonal"
          class="mb-6"
        >
          <template #prepend>
            <VIcon icon="tabler-info-circle" />
          </template>
          <div>
            <strong>Quản lý người dùng</strong>
            <p class="mt-2">
              Trang này chỉ dành cho Admin. Bạn có thể xem danh sách người dùng và thay đổi role của họ.
            </p>
          </div>
        </VAlert>

        <!-- Loading State -->
        <div
          v-if="loading"
          class="text-center py-8"
        >
          <VProgressCircular
            indeterminate
            color="primary"
            size="64"
          />
          <p class="mt-4">
            Đang tải danh sách người dùng...
          </p>
        </div>

        <!-- Users Table -->
        <VTable v-else>
          <thead>
            <tr>
              <th class="text-left">
                ID
              </th>
              <th class="text-left">
                Tên
              </th>
              <th class="text-left">
                Email
              </th>
              <th class="text-left">
                Local ID
              </th>
              <th class="text-left">
                Provider
              </th>
              <th class="text-left">
                Role
              </th>
              <th class="text-left">
                Status
              </th>
              <th class="text-center">
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="user in users"
              :key="user.id"
            >
              <td>{{ user.id }}</td>
              <td>
                <div class="d-flex align-center gap-2">
                  <VIcon :icon="getRoleIcon(user.role)" />
                  {{ user.full_name }}
                </div>
              </td>
              <td>{{ user.email }}</td>
              <td>
                <VChip
                  v-if="user.localId"
                  color="success"
                  size="small"
                  variant="tonal"
                >
                  {{ user.localId }}
                </VChip>
                <span
                  v-else
                  class="text-medium-emphasis"
                >N/A</span>
              </td>
              <td>
                <VChip
                  size="small"
                  variant="tonal"
                >
                  {{ user.provider }}
                </VChip>
              </td>
              <td>
                <VChip
                  :color="getRoleColor(user.role)"
                  size="small"
                >
                  {{ user.role }}
                </VChip>
              </td>
              <td>
                <VChip
                  :color="user.is_active ? 'success' : 'error'"
                  size="small"
                  variant="tonal"
                >
                  {{ user.is_active ? 'Active' : 'Inactive' }}
                </VChip>
              </td>
              <td class="text-center">
                <VMenu>
                  <template #activator="{ props }">
                    <VBtn
                      icon
                      variant="text"
                      size="small"
                      v-bind="props"
                    >
                      <VIcon icon="tabler-dots-vertical" />
                    </VBtn>
                  </template>

                  <VList>
                    <VListItem @click="updateUserRole(user.id, 'admin')">
                      <template #prepend>
                        <VIcon
                          icon="tabler-shield-check"
                          color="error"
                        />
                      </template>
                      <VListItemTitle>Set as Admin</VListItemTitle>
                    </VListItem>

                    <VListItem @click="updateUserRole(user.id, 'user')">
                      <template #prepend>
                        <VIcon
                          icon="tabler-user"
                          color="primary"
                        />
                      </template>
                      <VListItemTitle>Set as User</VListItemTitle>
                    </VListItem>

                    <VListItem @click="updateUserRole(user.id, 'guest')">
                      <template #prepend>
                        <VIcon
                          icon="tabler-user-question"
                          color="warning"
                        />
                      </template>
                      <VListItemTitle>Set as Guest</VListItemTitle>
                    </VListItem>

                    <VDivider class="my-2" />

                    <VListItem @click="openLocalIdDialog(user)">
                      <template #prepend>
                        <VIcon
                          icon="tabler-id"
                          color="success"
                        />
                      </template>
                      <VListItemTitle>Set Local ID</VListItemTitle>
                    </VListItem>
                  </VList>
                </VMenu>
              </td>
            </tr>
          </tbody>
        </VTable>

        <!-- Empty State -->
        <div
          v-if="!loading && users.length === 0"
          class="text-center py-8"
        >
          <VIcon
            icon="tabler-users-off"
            size="64"
            color="disabled"
          />
          <p class="mt-4 text-disabled">
            Không có người dùng nào
          </p>
        </div>
      </VCardText>
    </VCard>

    <!-- LocalId Dialog -->
    <VDialog
      v-model="localIdDialog"
      max-width="500"
    >
      <VCard>
        <VCardTitle class="d-flex align-center gap-2">
          <VIcon
            icon="tabler-id"
            color="success"
          />
          Set Local ID
        </VCardTitle>
        <VDivider />
        <VCardText>
          <div class="mb-4">
            <div class="text-body-2 text-medium-emphasis mb-1">
              User
            </div>
            <div class="font-weight-medium">
              {{ selectedUser?.full_name }}
            </div>
            <div class="text-body-2 text-medium-emphasis">
              {{ selectedUser?.email }}
            </div>
          </div>

          <VTextField
            v-model="newLocalId"
            label="Local ID"
            placeholder="VD: VNW0018616"
            variant="outlined"
            prepend-inner-icon="tabler-id"
            :disabled="localIdLoading"
            @keyup.enter="updateUserLocalId"
          />
        </VCardText>
        <VDivider />
        <VCardActions class="px-6 py-4">
          <VSpacer />
          <VBtn
            color="grey"
            variant="text"
            :disabled="localIdLoading"
            @click="closeLocalIdDialog"
          >
            Hủy
          </VBtn>
          <VBtn
            color="success"
            variant="elevated"
            :loading="localIdLoading"
            @click="updateUserLocalId"
          >
            <VIcon
              start
              icon="tabler-check"
            />
            Cập Nhật
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Toast Notification -->
    <VSnackbar
      v-model="toast.show"
      :color="toast.color"
      :timeout="3000"
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
  </div>
</template>
