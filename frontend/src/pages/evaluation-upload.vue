<script setup>
import { ref } from 'vue'
import { useAdminProtection } from '@/composables/useAdminProtection'
import { $api } from '@/utils/api'

// Protect this page - only admin can access
useAdminProtection()

const file = ref(null)
const uploading = ref(false)
const uploadResult = ref(null)

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

// Upload file
const uploadFile = async () => {
  if (!file.value || file.value.length === 0) {
    showToast('Vui lòng chọn file Excel!', 'warning')
    return
  }

  uploading.value = true
  uploadResult.value = null

  try {
    const formData = new FormData()
    formData.append('file', file.value[0])

    const response = await $api('/evaluations/upload', {
      method: 'POST',
      body: formData,
    })

    if (response.success) {
      uploadResult.value = response
      showToast('Upload file thành công!')
      file.value = null
    }
  }
  catch (error) {
    console.error('Failed to upload file:', error)
    showToast('Upload file thất bại!', 'error')
    uploadResult.value = null
  }
  finally {
    uploading.value = false
  }
}

// Reset form
const resetForm = () => {
  file.value = null
  uploadResult.value = null
}
</script>

<template>
  <div>
    <VRow>
      <VCol cols="12">
        <VCard>
          <VCardTitle class="d-flex align-center justify-space-between">
            <div class="d-flex align-center gap-2">
              <VIcon
                icon="tabler-file-upload"
                size="28"
              />
              <span>Upload Evaluation File</span>
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

          <VDivider />

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
                <strong>Upload File Đánh Giá Nhân Viên</strong>
                <p class="mt-2">
                  Tải lên file Excel chứa dữ liệu đánh giá nhân viên hàng tháng. File sẽ được xử lý và cập nhật vào hệ thống.
                </p>
                <p class="mb-0">
                  <strong>Định dạng:</strong> File Excel (.xlsx) - VD: 25C月評核總表_20260108.xlsx
                </p>
              </div>
            </VAlert>

            <!-- Upload Form -->
            <VRow>
              <VCol cols="12">
                <VFileInput
                  v-model="file"
                  label="Chọn file Excel"
                  accept=".xlsx,.xls"
                  prepend-icon="tabler-file-spreadsheet"
                  show-size
                  variant="outlined"
                  :disabled="uploading"
                  clearable
                >
                  <template #prepend-inner>
                    <VIcon icon="tabler-file-spreadsheet" />
                  </template>
                </VFileInput>
              </VCol>

              <VCol
                cols="12"
                class="d-flex gap-4"
              >
                <VBtn
                  color="primary"
                  :loading="uploading"
                  :disabled="!file || file.length === 0"
                  @click="uploadFile"
                >
                  <VIcon
                    start
                    icon="tabler-upload"
                  />
                  Upload File
                </VBtn>

                <VBtn
                  color="grey"
                  variant="outlined"
                  :disabled="uploading"
                  @click="resetForm"
                >
                  <VIcon
                    start
                    icon="tabler-refresh"
                  />
                  Reset
                </VBtn>
              </VCol>
            </VRow>

            <!-- Upload Result -->
            <VRow v-if="uploadResult">
              <VCol cols="12">
                <VAlert
                  type="success"
                  variant="tonal"
                  class="mt-6"
                >
                  <template #prepend>
                    <VIcon icon="tabler-check-circle" />
                  </template>
                  <div>
                    <strong>Upload thành công!</strong>
                    <div class="mt-4">
                      <VRow>
                        <VCol
                          cols="12"
                          md="3"
                        >
                          <VCard variant="tonal">
                            <VCardText class="text-center">
                              <div class="text-h4 font-weight-bold text-primary">
                                {{ uploadResult.summary.total_rows }}
                              </div>
                              <div class="text-body-2 text-medium-emphasis mt-1">
                                Tổng số dòng
                              </div>
                            </VCardText>
                          </VCard>
                        </VCol>

                        <VCol
                          cols="12"
                          md="3"
                        >
                          <VCard variant="tonal">
                            <VCardText class="text-center">
                              <div class="text-h4 font-weight-bold text-success">
                                {{ uploadResult.summary.created }}
                              </div>
                              <div class="text-body-2 text-medium-emphasis mt-1">
                                Tạo mới
                              </div>
                            </VCardText>
                          </VCard>
                        </VCol>

                        <VCol
                          cols="12"
                          md="3"
                        >
                          <VCard variant="tonal">
                            <VCardText class="text-center">
                              <div class="text-h4 font-weight-bold text-info">
                                {{ uploadResult.summary.updated }}
                              </div>
                              <div class="text-body-2 text-medium-emphasis mt-1">
                                Cập nhật
                              </div>
                            </VCardText>
                          </VCard>
                        </VCol>

                        <VCol
                          cols="12"
                          md="3"
                        >
                          <VCard variant="tonal">
                            <VCardText class="text-center">
                              <div class="text-h4 font-weight-bold text-error">
                                {{ uploadResult.summary.errors }}
                              </div>
                              <div class="text-body-2 text-medium-emphasis mt-1">
                                Lỗi
                              </div>
                            </VCardText>
                          </VCard>
                        </VCol>
                      </VRow>
                    </div>

                    <!-- Error Details -->
                    <div
                      v-if="uploadResult.error_details && uploadResult.error_details.length > 0"
                      class="mt-6"
                    >
                      <VDivider class="mb-4" />
                      <strong class="text-error">Chi tiết lỗi:</strong>
                      <VList class="mt-2">
                        <VListItem
                          v-for="(error, index) in uploadResult.error_details"
                          :key="index"
                        >
                          <VListItemTitle class="text-error">
                            {{ error }}
                          </VListItemTitle>
                        </VListItem>
                      </VList>
                    </div>
                  </div>
                </VAlert>
              </VCol>
            </VRow>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <!-- Toast Notification -->
    <VSnackbar
      v-model="toast.show"
      :color="toast.color"
      :timeout="3000"
      location="top"
    >
      {{ toast.message }}
      <template #actions>
        <VBtn
          variant="text"
          @click="toast.show = false"
        >
          Đóng
        </VBtn>
      </template>
    </VSnackbar>
  </div>
</template>
