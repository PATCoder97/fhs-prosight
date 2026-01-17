<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAdminProtection } from '@/composables/useAdminProtection'
import { $api } from '@/utils/api'

// Protect this page - only admin can access
useAdminProtection()

const apiKeys = ref([])
const loading = ref(false)
const createDialog = ref(false)
const deleteDialog = ref(false)
const selectedKey = ref(null)
const showApiKey = ref(false)
const createdApiKey = ref('')

// Form data for creating new API key
const newKeyForm = ref({
  name: '',
  description: '',
  scopes: [],
  expires_days: 365,
})

// Available scopes
const availableScopes = [
  { value: 'evaluations:import', title: 'Import Đánh Giá (Evaluations)' },
  { value: 'dormitory-bills:import', title: 'Import Hóa Đơn KTX (Dormitory Bills)' },
]

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

// Load API keys from backend
onMounted(async () => {
  await loadApiKeys()
})

const loadApiKeys = async () => {
  loading.value = true
  try {
    const response = await $api('/api-keys')
    apiKeys.value = response.keys || []
  }
  catch (error) {
    console.error('Failed to load API keys:', error)
    showToast('Không thể tải danh sách API keys!', 'error')
  }
  finally {
    loading.value = false
  }
}

// Create new API key
const createApiKey = async () => {
  if (!newKeyForm.value.name.trim()) {
    showToast('Vui lòng nhập tên API key!', 'warning')
    return
  }

  if (newKeyForm.value.scopes.length === 0) {
    showToast('Vui lòng chọn ít nhất 1 scope!', 'warning')
    return
  }

  loading.value = true
  try {
    const response = await $api('/api-keys', {
      method: 'POST',
      body: JSON.stringify(newKeyForm.value),
    })

    // Show the created API key (only shown once!)
    createdApiKey.value = response.api_key
    showApiKey.value = true
    createDialog.value = false

    // Reload the list
    await loadApiKeys()

    showToast('API key đã được tạo thành công!', 'success')

    // Reset form
    newKeyForm.value = {
      name: '',
      description: '',
      scopes: [],
      expires_days: 365,
    }
  }
  catch (error) {
    console.error('Failed to create API key:', error)
    showToast(error.message || 'Tạo API key thất bại!', 'error')
  }
  finally {
    loading.value = false
  }
}

// Revoke API key
const revokeApiKey = async () => {
  if (!selectedKey.value) return

  loading.value = true
  try {
    await $api(`/api-keys/${selectedKey.value.id}`, {
      method: 'DELETE',
    })

    deleteDialog.value = false
    await loadApiKeys()
    showToast('API key đã được vô hiệu hóa!', 'success')
  }
  catch (error) {
    console.error('Failed to revoke API key:', error)
    showToast(error.message || 'Vô hiệu hóa API key thất bại!', 'error')
  }
  finally {
    loading.value = false
  }
}

// Open revoke dialog
const openRevokeDialog = (key) => {
  selectedKey.value = key
  deleteDialog.value = true
}

// Copy API key to clipboard
const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    showToast('Đã copy vào clipboard!', 'success')
  }
  catch (error) {
    showToast('Không thể copy!', 'error')
  }
}

// Format date
const formatDate = (dateString) => {
  if (!dateString) return 'Không giới hạn'
  return new Date(dateString).toLocaleString('vi-VN')
}

// Get status color
const getStatusColor = (key) => {
  if (!key.is_active) return 'error'
  if (key.expires_at && new Date(key.expires_at) < new Date()) return 'warning'
  return 'success'
}

// Get status text
const getStatusText = (key) => {
  if (!key.is_active) return 'Đã vô hiệu hóa'
  if (key.expires_at && new Date(key.expires_at) < new Date()) return 'Đã hết hạn'
  return 'Hoạt động'
}

// Table headers
const headers = [
  { title: 'Tên', key: 'name', sortable: true },
  { title: 'Prefix', key: 'key_prefix', sortable: false },
  { title: 'Scopes', key: 'scopes', sortable: false },
  { title: 'Trạng thái', key: 'is_active', sortable: true },
  { title: 'Ngày tạo', key: 'created_at', sortable: true },
  { title: 'Hết hạn', key: 'expires_at', sortable: true },
  { title: 'Lần dùng cuối', key: 'last_used_at', sortable: true },
  { title: 'Hành động', key: 'actions', sortable: false },
]
</script>

<template>
  <div>
    <!-- Page Header -->
    <VRow class="mb-6">
      <VCol cols="12">
        <div class="d-flex justify-space-between align-center">
          <div>
            <h2 class="text-h4 mb-2">
              Quản Lý API Keys
            </h2>
            <p class="text-body-1 text-medium-emphasis">
              Tạo và quản lý API keys cho external integrations
            </p>
          </div>
          <VBtn
            color="primary"
            prepend-icon="tabler-plus"
            @click="createDialog = true"
          >
            Tạo API Key
          </VBtn>
        </div>
      </VCol>
    </VRow>

    <!-- API Keys Table -->
    <VCard>
      <VCardText>
        <VDataTable
          :headers="headers"
          :items="apiKeys"
          :loading="loading"
          loading-text="Đang tải dữ liệu..."
          no-data-text="Chưa có API key nào"
          items-per-page="10"
        >
          <!-- Name column -->
          <template #item.name="{ item }">
            <div>
              <div class="font-weight-medium">
                {{ item.name }}
              </div>
              <div
                v-if="item.description"
                class="text-caption text-medium-emphasis"
              >
                {{ item.description }}
              </div>
            </div>
          </template>

          <!-- Prefix column -->
          <template #item.key_prefix="{ item }">
            <VChip
              size="small"
              variant="tonal"
              color="secondary"
            >
              {{ item.key_prefix }}
            </VChip>
          </template>

          <!-- Scopes column -->
          <template #item.scopes="{ item }">
            <VChip
              v-for="scope in item.scopes.split(',')"
              :key="scope"
              size="small"
              variant="tonal"
              color="info"
              class="me-1"
            >
              {{ scope.trim() }}
            </VChip>
          </template>

          <!-- Status column -->
          <template #item.is_active="{ item }">
            <VChip
              size="small"
              :color="getStatusColor(item)"
            >
              {{ getStatusText(item) }}
            </VChip>
          </template>

          <!-- Created at column -->
          <template #item.created_at="{ item }">
            {{ formatDate(item.created_at) }}
          </template>

          <!-- Expires at column -->
          <template #item.expires_at="{ item }">
            {{ formatDate(item.expires_at) }}
          </template>

          <!-- Last used at column -->
          <template #item.last_used_at="{ item }">
            {{ item.last_used_at ? formatDate(item.last_used_at) : 'Chưa sử dụng' }}
          </template>

          <!-- Actions column -->
          <template #item.actions="{ item }">
            <VBtn
              v-if="item.is_active"
              icon
              variant="text"
              color="error"
              size="small"
              @click="openRevokeDialog(item)"
            >
              <VIcon icon="tabler-trash" />
              <VTooltip activator="parent">
                Vô hiệu hóa
              </VTooltip>
            </VBtn>
          </template>
        </VDataTable>
      </VCardText>
    </VCard>

    <!-- Create API Key Dialog -->
    <VDialog
      v-model="createDialog"
      max-width="600"
      persistent
    >
      <VCard>
        <VCardTitle class="d-flex justify-space-between align-center">
          <span>Tạo API Key Mới</span>
          <VBtn
            icon
            variant="text"
            @click="createDialog = false"
          >
            <VIcon icon="tabler-x" />
          </VBtn>
        </VCardTitle>

        <VCardText>
          <VForm @submit.prevent="createApiKey">
            <VRow>
              <VCol cols="12">
                <VTextField
                  v-model="newKeyForm.name"
                  label="Tên API Key *"
                  placeholder="VD: HRS Import Service"
                  :rules="[v => !!v || 'Tên là bắt buộc']"
                />
              </VCol>

              <VCol cols="12">
                <VTextarea
                  v-model="newKeyForm.description"
                  label="Mô tả"
                  placeholder="VD: API key cho import tự động từ HRS"
                  rows="2"
                />
              </VCol>

              <VCol cols="12">
                <VSelect
                  v-model="newKeyForm.scopes"
                  :items="availableScopes"
                  label="Scopes (Quyền truy cập) *"
                  multiple
                  chips
                  :rules="[v => v.length > 0 || 'Chọn ít nhất 1 scope']"
                />
              </VCol>

              <VCol cols="12">
                <VTextField
                  v-model.number="newKeyForm.expires_days"
                  label="Số ngày hết hạn"
                  type="number"
                  hint="Để trống = không giới hạn"
                  persistent-hint
                />
              </VCol>
            </VRow>
          </VForm>
        </VCardText>

        <VCardActions>
          <VSpacer />
          <VBtn
            color="secondary"
            variant="text"
            @click="createDialog = false"
          >
            Hủy
          </VBtn>
          <VBtn
            color="primary"
            :loading="loading"
            @click="createApiKey"
          >
            Tạo API Key
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Show Created API Key Dialog -->
    <VDialog
      v-model="showApiKey"
      max-width="700"
      persistent
    >
      <VCard>
        <VCardTitle class="text-h5">
          🎉 API Key đã được tạo!
        </VCardTitle>

        <VCardText>
          <VAlert
            type="warning"
            variant="tonal"
            class="mb-4"
          >
            <strong>⚠️ LƯU Ý QUAN TRỌNG:</strong>
            <br>
            API key chỉ hiển thị MỘT LẦN DUY NHẤT này. Vui lòng copy và lưu vào nơi an toàn!
          </VAlert>

          <div class="d-flex align-center pa-4 bg-surface rounded">
            <code class="flex-grow-1 text-break">{{ createdApiKey }}</code>
            <VBtn
              icon
              variant="text"
              color="primary"
              @click="copyToClipboard(createdApiKey)"
            >
              <VIcon icon="tabler-copy" />
            </VBtn>
          </div>

          <VAlert
            type="info"
            variant="tonal"
            class="mt-4"
          >
            <strong>Cách sử dụng:</strong>
            <br>
            Thêm header <code>X-API-Key: {{ createdApiKey.substring(0, 20) }}...</code> vào request
          </VAlert>
        </VCardText>

        <VCardActions>
          <VSpacer />
          <VBtn
            color="primary"
            @click="showApiKey = false; createdApiKey = ''"
          >
            Đã lưu, đóng
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Delete Confirmation Dialog -->
    <VDialog
      v-model="deleteDialog"
      max-width="500"
    >
      <VCard>
        <VCardTitle>Xác nhận vô hiệu hóa</VCardTitle>

        <VCardText>
          Bạn có chắc chắn muốn vô hiệu hóa API key
          <strong>{{ selectedKey?.name }}</strong>?
          <br><br>
          Key sẽ không thể sử dụng được nữa nhưng vẫn giữ lại trong database để audit.
        </VCardText>

        <VCardActions>
          <VSpacer />
          <VBtn
            color="secondary"
            variant="text"
            @click="deleteDialog = false"
          >
            Hủy
          </VBtn>
          <VBtn
            color="error"
            :loading="loading"
            @click="revokeApiKey"
          >
            Vô hiệu hóa
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

<style scoped>
code {
  background-color: rgba(var(--v-theme-on-surface), 0.05);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
}
</style>
