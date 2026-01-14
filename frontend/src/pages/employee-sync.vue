<script setup>
import { ref, computed } from 'vue'
import { useGuestProtection } from '@/composables/useGuestProtection'
import { $api } from '@/utils/api'
import { formatEmployeeId, formatCurrency } from '@/utils/formatters'

// Protect from guest users
useGuestProtection()

// State
const loading = ref(false)
const syncedEmployee = ref(null)
const error = ref(null)

// Form inputs
const employeeId = ref('')
const selectedSource = ref('hrs')
const covidToken = ref('')

// Source options
const sourceOptions = [
  { value: 'hrs', label: 'HRS System' },
  { value: 'covid', label: 'COVID System' },
]

// Sync employee data
const syncEmployee = async () => {
  // Auto-format employee ID before validation
  const formattedId = formatEmployeeId(employeeId.value)

  // Validate employee ID
  if (!formattedId || !formattedId.trim()) {
    error.value = 'Vui lòng nhập Employee ID'
    return
  }

  // Validate COVID token if COVID source is selected
  if (selectedSource.value === 'covid' && (!covidToken.value || !covidToken.value.trim())) {
    error.value = 'Vui lòng nhập token cho COVID System'
    return
  }

  // Update employeeId with formatted value
  employeeId.value = formattedId

  loading.value = true
  error.value = null
  syncedEmployee.value = null

  try {
    // Extract numeric ID from formatted ID (VNW0014732 → 14732)
    const numericId = formattedId.replace(/^VNW0*/i, '')

    const requestBody = {
      emp_id: parseInt(numericId),
      source: selectedSource.value,
    }

    // Add token only if COVID source
    if (selectedSource.value === 'covid') {
      requestBody.token = covidToken.value
    }

    const response = await $api('/employees/sync', {
      method: 'POST',
      body: requestBody,
    })

    syncedEmployee.value = response
  }
  catch (err) {
    console.error('Failed to sync employee:', err)
    error.value = err.message || 'Không thể đồng bộ nhân viên'
    syncedEmployee.value = null
  }
  finally {
    loading.value = false
  }
}

// Reset form
const resetForm = () => {
  employeeId.value = ''
  selectedSource.value = 'hrs'
  covidToken.value = ''
  syncedEmployee.value = null
  error.value = null
}

// Check if COVID source is selected
const isCovidSource = computed(() => selectedSource.value === 'covid')
</script>

<template>
  <!-- Sync Form -->
  <VRow>
      <VCol cols="12">
        <VCard>
          <VCardTitle>
            <VIcon
              icon="tabler-refresh"
              class="me-2"
            />
            Đồng Bộ Nhân Viên
          </VCardTitle>
          <VDivider />
          <VCardText>
            <VRow>
              <VCol
                cols="12"
                md="3"
              >
                <VTextField
                  v-model="employeeId"
                  label="Employee ID"
                  placeholder="VD: 14732 hoặc VNW0014732"
                  variant="outlined"
                  prepend-inner-icon="tabler-id"
                  clearable
                  @keyup.enter="syncEmployee"
                />
              </VCol>
              <VCol
                cols="12"
                md="3"
              >
                <VSelect
                  v-model="selectedSource"
                  :items="sourceOptions"
                  item-title="label"
                  item-value="value"
                  label="Nguồn dữ liệu"
                  variant="outlined"
                  prepend-inner-icon="tabler-database"
                />
              </VCol>
              <VCol
                cols="12"
                md="3"
              >
                <VTextField
                  v-model="covidToken"
                  label="COVID Token"
                  placeholder="Nhập token"
                  variant="outlined"
                  prepend-inner-icon="tabler-key"
                  type="password"
                  clearable
                  @keyup.enter="syncEmployee"
                />
              </VCol>
              <VCol
                cols="12"
                md="3"
                class="d-flex align-end justify-end"
              >
                <VBtn
                  color="primary"
                  :block="$vuetify.display.smAndDown"
                  :width="$vuetify.display.mdAndUp ? 140 : undefined"
                  :loading="loading"
                  @click="syncEmployee"
                >
                  <VIcon
                    start
                    icon="tabler-search"
                  />
                  Tra Cứu
                </VBtn>
              </VCol>
            </VRow>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <!-- Error Alert -->
    <VAlert
      v-if="error"
      type="error"
      variant="tonal"
      closable
      class="mb-6"
      @click:close="error = null"
    >
      {{ error }}
    </VAlert>

    <!-- Loading State -->
    <VRow v-if="loading">
      <VCol cols="12">
        <VCard>
          <VCardText class="text-center py-16">
            <VProgressCircular
              indeterminate
              color="primary"
              size="64"
            />
            <p class="text-body-1 mt-4">
              Đang đồng bộ dữ liệu...
            </p>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <!-- Synced Employee Data -->
    <VRow v-if="!loading && syncedEmployee">
      <VCol cols="12">
        <!-- Success Alert -->
        <VAlert
          type="success"
          variant="tonal"
          class="mb-4"
        >
          <div class="d-flex align-center justify-space-between">
            <div>
              <strong>Đồng bộ thành công!</strong>
              <p class="mb-0 mt-1">
                Dữ liệu nhân viên đã được đồng bộ từ {{ selectedSource === 'hrs' ? 'HRS System' : 'COVID System' }}
              </p>
            </div>
            <VBtn
              variant="text"
              color="success"
              @click="resetForm"
            >
              <VIcon
                start
                icon="tabler-plus"
              />
              Đồng Bộ Mới
            </VBtn>
          </div>
        </VAlert>

        <!-- Employee Info Card -->
        <VCard class="mb-4">
          <VCardTitle class="bg-primary-subtle">
            <VIcon
              icon="tabler-user"
              class="me-2"
            />
            Thông Tin Cá Nhân
          </VCardTitle>
          <VDivider />
          <VCardText>
            <VRow>
              <VCol
                cols="12"
                md="4"
              >
                <div class="mb-4">
                  <p class="text-caption text-medium-emphasis mb-1">
                    Employee ID
                  </p>
                  <VChip
                    color="primary"
                    variant="flat"
                  >
                    {{ syncedEmployee.id }}
                  </VChip>
                </div>

                <div class="mb-4">
                  <p class="text-caption text-medium-emphasis mb-1">
                    Tên (Tiếng Trung)
                  </p>
                  <p class="text-body-1 mb-0">
                    {{ syncedEmployee.name_tw || 'N/A' }}
                  </p>
                </div>

                <div class="mb-4">
                  <p class="text-caption text-medium-emphasis mb-1">
                    Tên (Tiếng Anh)
                  </p>
                  <p class="text-body-1 mb-0">
                    {{ syncedEmployee.name_en || 'N/A' }}
                  </p>
                </div>

                <div class="mb-4">
                  <p class="text-caption text-medium-emphasis mb-1">
                    Ngày sinh
                  </p>
                  <p class="text-body-1 mb-0">
                    {{ syncedEmployee.dob || 'N/A' }}
                  </p>
                </div>
              </VCol>

              <VCol
                cols="12"
                md="4"
              >
                <div class="mb-4">
                  <p class="text-caption text-medium-emphasis mb-1">
                    Giới tính
                  </p>
                  <p class="text-body-1 mb-0">
                    {{ syncedEmployee.sex || 'N/A' }}
                  </p>
                </div>

                <div class="mb-4">
                  <p class="text-caption text-medium-emphasis mb-1">
                    Quốc tịch
                  </p>
                  <p class="text-body-1 mb-0">
                    {{ syncedEmployee.nationality || 'N/A' }}
                  </p>
                </div>

                <div class="mb-4">
                  <p class="text-caption text-medium-emphasis mb-1">
                    Số CMND/CCCD
                  </p>
                  <p class="text-body-1 mb-0">
                    {{ syncedEmployee.identity_number || 'N/A' }}
                  </p>
                </div>

                <div class="mb-4">
                  <p class="text-caption text-medium-emphasis mb-1">
                    Tên vợ/chồng
                  </p>
                  <p class="text-body-1 mb-0">
                    {{ syncedEmployee.spouse_name || 'N/A' }}
                  </p>
                </div>
              </VCol>

              <VCol
                cols="12"
                md="4"
              >
                <div class="mb-4">
                  <p class="text-caption text-medium-emphasis mb-1">
                    SĐT 1
                  </p>
                  <p class="text-body-1 mb-0">
                    {{ syncedEmployee.phone1 || 'N/A' }}
                  </p>
                </div>

                <div class="mb-4">
                  <p class="text-caption text-medium-emphasis mb-1">
                    SĐT 2
                  </p>
                  <p class="text-body-1 mb-0">
                    {{ syncedEmployee.phone2 || 'N/A' }}
                  </p>
                </div>

                <div class="mb-4">
                  <p class="text-caption text-medium-emphasis mb-1">
                    Mã KTX
                  </p>
                  <p class="text-body-1 mb-0">
                    {{ syncedEmployee.dorm_id || 'N/A' }}
                  </p>
                </div>
              </VCol>
            </VRow>
          </VCardText>
        </VCard>

        <!-- Work Info Card -->
        <VCard class="mb-4">
          <VCardTitle class="bg-success-subtle">
            <VIcon
              icon="tabler-briefcase"
              class="me-2"
            />
            Thông Tin Công Việc
          </VCardTitle>
          <VDivider />
          <VCardText>
            <VRow>
              <VCol
                cols="12"
                md="6"
              >
                <div class="mb-4">
                  <p class="text-caption text-medium-emphasis mb-1">
                    Phòng ban
                  </p>
                  <p class="text-body-1 mb-0">
                    {{ syncedEmployee.dept || 'N/A' }}
                  </p>
                </div>

                <div class="mb-4">
                  <p class="text-caption text-medium-emphasis mb-1">
                    Mã phòng ban
                  </p>
                  <p class="text-body-1 mb-0">
                    {{ syncedEmployee.department_code || 'N/A' }}
                  </p>
                </div>

                <div class="mb-4">
                  <p class="text-caption text-medium-emphasis mb-1">
                    Chức danh
                  </p>
                  <p class="text-body-1 mb-0">
                    {{ syncedEmployee.job_title || 'N/A' }}
                  </p>
                </div>
              </VCol>

              <VCol
                cols="12"
                md="6"
              >
                <div class="mb-4">
                  <p class="text-caption text-medium-emphasis mb-1">
                    Loại công việc
                  </p>
                  <p class="text-body-1 mb-0">
                    {{ syncedEmployee.job_type || 'N/A' }}
                  </p>
                </div>

                <div class="mb-4">
                  <p class="text-caption text-medium-emphasis mb-1">
                    Ngày vào công ty
                  </p>
                  <p class="text-body-1 mb-0">
                    {{ syncedEmployee.start_date || 'N/A' }}
                  </p>
                </div>

                <div class="mb-4">
                  <p class="text-caption text-medium-emphasis mb-1">
                    Lương
                  </p>
                  <p class="text-h6 text-success mb-0">
                    {{ syncedEmployee.salary ? formatCurrency(syncedEmployee.salary) : 'N/A' }}
                  </p>
                </div>
              </VCol>
            </VRow>
          </VCardText>
        </VCard>

        <!-- Address Info Card -->
        <VCard>
          <VCardTitle class="bg-info-subtle">
            <VIcon
              icon="tabler-map-pin"
              class="me-2"
            />
            Thông Tin Địa Chỉ
          </VCardTitle>
          <VDivider />
          <VCardText>
            <VRow>
              <VCol
                cols="12"
                md="6"
              >
                <div class="mb-4">
                  <p class="text-caption text-medium-emphasis mb-1">
                    Địa chỉ 1
                  </p>
                  <p class="text-body-1 mb-0">
                    {{ syncedEmployee.address1 || 'N/A' }}
                  </p>
                </div>
              </VCol>

              <VCol
                cols="12"
                md="6"
              >
                <div class="mb-4">
                  <p class="text-caption text-medium-emphasis mb-1">
                    Địa chỉ 2
                  </p>
                  <p class="text-body-1 mb-0">
                    {{ syncedEmployee.address2 || 'N/A' }}
                  </p>
                </div>
              </VCol>
            </VRow>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <!-- No Data State -->
    <VRow v-if="!loading && !syncedEmployee && !error">
      <VCol cols="12">
        <VCard>
          <VCardText class="text-center py-16">
            <VIcon
              icon="tabler-refresh"
              size="64"
              color="grey-lighten-1"
              class="mb-4"
            />
            <p class="text-h6 text-medium-emphasis mb-2">
              Nhập thông tin để đồng bộ
            </p>
            <p class="text-body-2 text-medium-emphasis">
              Vui lòng nhập Employee ID, chọn nguồn dữ liệu, sau đó nhấn "Đồng Bộ"
            </p>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>
</template>

<style scoped>
.bg-primary-subtle {
  background-color: rgba(var(--v-theme-primary), 0.08);
}

.bg-success-subtle {
  background-color: rgba(var(--v-theme-success), 0.08);
}

.bg-info-subtle {
  background-color: rgba(var(--v-theme-info), 0.08);
}
</style>
