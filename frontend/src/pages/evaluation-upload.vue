<script setup>
import { ref } from 'vue'
import { useDropZone, useFileDialog } from '@vueuse/core'
import { useAdminProtection } from '@/composables/useAdminProtection'
import { $api } from '@/utils/api'

// Protect this page - only admin can access
useAdminProtection()

const dropZoneRef = ref()
const fileData = ref(null)
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

// File dialog
const { open, onChange } = useFileDialog({
  accept: '.xlsx,.xls',
  multiple: false,
})

// Handle file drop
const onDrop = (droppedFiles) => {
  if (!droppedFiles || droppedFiles.length === 0) return

  const file = droppedFiles[0]

  // Check file type
  if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
    showToast('Chỉ chấp nhận file Excel (.xlsx, .xls)!', 'error')
    return
  }

  fileData.value = file
  uploadResult.value = null
}

// Handle file selection
onChange((selectedFiles) => {
  if (!selectedFiles || selectedFiles.length === 0) return

  const file = selectedFiles[0]
  fileData.value = file
  uploadResult.value = null
})

// Setup drop zone
useDropZone(dropZoneRef, onDrop)

// Upload file
const uploadFile = async () => {
  if (!fileData.value) {
    showToast('Vui lòng chọn file Excel!', 'warning')
    return
  }

  uploading.value = true
  uploadResult.value = null

  try {
    const formData = new FormData()
    formData.append('file', fileData.value)

    // Use fetch directly for file upload instead of $api
    const response = await fetch('http://localhost:8001/api/evaluations/upload', {
      method: 'POST',
      credentials: 'include',
      body: formData,
    })

    const data = await response.json()

    if (data.success) {
      uploadResult.value = data
      showToast('Upload file thành công!')
      fileData.value = null
    }
    else {
      showToast('Upload file thất bại!', 'error')
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

// Remove file
const removeFile = () => {
  fileData.value = null
  uploadResult.value = null
}

// Reset form
const resetForm = () => {
  fileData.value = null
  uploadResult.value = null
}

// Format file size
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
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

            <!-- Drag & Drop Zone -->
            <div
              ref="dropZoneRef"
              class="cursor-pointer"
              @click="() => open()"
            >
              <!-- Empty State - Show Drop Zone -->
              <div
                v-if="!fileData"
                class="drop-zone rounded pa-12 text-center"
              >
                <VIcon
                  icon="tabler-cloud-upload"
                  size="64"
                  color="primary"
                  class="mb-4"
                />
                <h4 class="text-h5 mb-2">
                  Kéo thả file Excel vào đây
                </h4>
                <p class="text-body-2 text-medium-emphasis mb-4">
                  hoặc
                </p>
                <VBtn
                  color="primary"
                  variant="tonal"
                  @click.stop="open()"
                >
                  <VIcon
                    start
                    icon="tabler-folder-open"
                  />
                  Chọn File
                </VBtn>
                <p class="text-caption text-medium-emphasis mt-4">
                  Chỉ chấp nhận file .xlsx hoặc .xls
                </p>
              </div>

              <!-- File Selected -->
              <VCard
                v-else
                variant="tonal"
                class="pa-6"
              >
                <div class="d-flex align-center gap-4">
                  <VAvatar
                    color="success"
                    variant="tonal"
                    size="56"
                  >
                    <VIcon
                      icon="tabler-file-spreadsheet"
                      size="32"
                    />
                  </VAvatar>
                  <div class="flex-grow-1">
                    <h6 class="text-h6 mb-1">
                      {{ fileData.name }}
                    </h6>
                    <p class="text-body-2 text-medium-emphasis mb-0">
                      {{ formatFileSize(fileData.size) }}
                    </p>
                  </div>
                  <VBtn
                    icon
                    variant="text"
                    color="error"
                    @click.stop="removeFile"
                  >
                    <VIcon icon="tabler-x" />
                  </VBtn>
                </div>
              </VCard>
            </div>

            <!-- Action Buttons -->
            <div
              v-if="fileData"
              class="d-flex gap-4 mt-6"
            >
              <VBtn
                color="primary"
                size="large"
                :loading="uploading"
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
                size="large"
                :disabled="uploading"
                @click="resetForm"
              >
                <VIcon
                  start
                  icon="tabler-refresh"
                />
                Reset
              </VBtn>
            </div>

            <!-- Upload Result -->
            <div v-if="uploadResult">
              <VDivider class="my-6" />

              <VAlert
                type="success"
                variant="tonal"
                prominent
              >
                <template #prepend>
                  <VIcon icon="tabler-circle-check" />
                </template>
                <VAlertTitle class="mb-2">
                  Upload thành công!
                </VAlertTitle>

                <VRow class="mt-4">
                  <VCol
                    cols="6"
                    md="3"
                  >
                    <div class="text-center">
                      <div class="text-h4 font-weight-bold text-primary mb-1">
                        {{ uploadResult.summary.total_rows }}
                      </div>
                      <div class="text-body-2 text-medium-emphasis">
                        Tổng số dòng
                      </div>
                    </div>
                  </VCol>

                  <VCol
                    cols="6"
                    md="3"
                  >
                    <div class="text-center">
                      <div class="text-h4 font-weight-bold text-success mb-1">
                        {{ uploadResult.summary.created }}
                      </div>
                      <div class="text-body-2 text-medium-emphasis">
                        Tạo mới
                      </div>
                    </div>
                  </VCol>

                  <VCol
                    cols="6"
                    md="3"
                  >
                    <div class="text-center">
                      <div class="text-h4 font-weight-bold text-info mb-1">
                        {{ uploadResult.summary.updated }}
                      </div>
                      <div class="text-body-2 text-medium-emphasis">
                        Cập nhật
                      </div>
                    </div>
                  </VCol>

                  <VCol
                    cols="6"
                    md="3"
                  >
                    <div class="text-center">
                      <div class="text-h4 font-weight-bold text-error mb-1">
                        {{ uploadResult.summary.errors }}
                      </div>
                      <div class="text-body-2 text-medium-emphasis">
                        Lỗi
                      </div>
                    </div>
                  </VCol>
                </VRow>

                <!-- Error Details -->
                <div
                  v-if="uploadResult.error_details && uploadResult.error_details.length > 0"
                  class="mt-6"
                >
                  <VDivider class="mb-4" />
                  <div class="text-h6 text-error mb-3">
                    Chi tiết lỗi:
                  </div>
                  <VList
                    density="compact"
                    class="bg-transparent"
                  >
                    <VListItem
                      v-for="(error, index) in uploadResult.error_details"
                      :key="index"
                    >
                      <template #prepend>
                        <VIcon
                          icon="tabler-alert-circle"
                          color="error"
                          size="20"
                        />
                      </template>
                      <VListItemTitle class="text-error">
                        {{ error }}
                      </VListItemTitle>
                    </VListItem>
                  </VList>
                </div>
              </VAlert>
            </div>
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

<style lang="scss" scoped>
.drop-zone {
  border: 2px dashed rgba(var(--v-theme-primary), 0.3);
  background-color: rgba(var(--v-theme-primary), 0.05);
  transition: all 0.3s ease;

  &:hover {
    border-color: rgba(var(--v-theme-primary), 0.6);
    background-color: rgba(var(--v-theme-primary), 0.1);
  }
}
</style>
