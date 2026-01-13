<script setup>
import { ref, computed } from 'vue'
import { $api } from '@/utils/api'

// State
const loading = ref(false)
const employees = ref([])
const error = ref(null)
const total = ref(0)

// Search filters
const searchName = ref('')
const searchDepartmentCode = ref('')
const searchDormId = ref('')

// Pagination
const page = ref(1)
const itemsPerPage = ref(10)
const itemsPerPageOptions = [
  { value: 10, title: '10' },
  { value: 25, title: '25' },
  { value: 50, title: '50' },
  { value: 100, title: '100' },
]

// Search employees
const searchEmployees = async (resetPage = false) => {
  // Reset to page 1 when starting a new search
  if (resetPage) {
    page.value = 1
  }

  loading.value = true
  error.value = null

  try {
    const params = new URLSearchParams()

    if (searchName.value.trim()) {
      params.append('name', searchName.value.trim())
    }
    if (searchDepartmentCode.value.trim()) {
      params.append('department_code', searchDepartmentCode.value.trim())
    }
    if (searchDormId.value.trim()) {
      params.append('dorm_id', searchDormId.value.trim())
    }

    params.append('skip', ((page.value - 1) * itemsPerPage.value).toString())
    params.append('limit', itemsPerPage.value.toString())

    const queryString = params.toString()
    const response = await $api(`/employees/search?${queryString}`)

    employees.value = response.items
    total.value = response.total
  }
  catch (err) {
    console.error('Failed to search employees:', err)
    error.value = err.message || 'Không thể tìm kiếm nhân viên'
    employees.value = []
    total.value = 0
  }
  finally {
    loading.value = false
  }
}

// Handle page change from pagination
const onPageChange = (newPage) => {
  page.value = newPage
  searchEmployees()
}

// Reset filters
const resetFilters = () => {
  searchName.value = ''
  searchDepartmentCode.value = ''
  searchDormId.value = ''
  page.value = 1
  employees.value = []
  total.value = 0
  error.value = null
}

// When items per page changes, reset to page 1 and search again
const onItemsPerPageChange = () => {
  page.value = 1
  if (employees.value.length > 0) {
    searchEmployees()
  }
}

// Format currency
const formatCurrency = (amount) => {
  if (!amount && amount !== 0) return '0 ₫'
  return new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND',
  }).format(amount)
}

// Table headers
const headers = [
  { title: 'Employee ID', key: 'id', sortable: false },
  { title: 'Tên (Trung)', key: 'name_tw', sortable: false },
  { title: 'Tên (Anh)', key: 'name_en', sortable: false },
  { title: 'Ngày sinh', key: 'dob', sortable: false },
  { title: 'Phòng ban', key: 'dept', sortable: false },
  { title: 'Mã PB', key: 'department_code', sortable: false },
  { title: 'Chức danh', key: 'job_title', sortable: false },
  { title: 'Lương', key: 'salary', sortable: false, align: 'end' },
  { title: 'SĐT 1', key: 'phone1', sortable: false },
  { title: 'Mã KTX', key: 'dorm_id', sortable: false },
]

// Total pages
const totalPages = computed(() => {
  if (total.value === 0) return 1
  return Math.ceil(total.value / itemsPerPage.value)
})
</script>

<template>
  <div>
    <!-- Search Form -->
    <VRow>
      <VCol cols="12">
        <VCard>
          <VCardTitle>
            <VIcon
              icon="tabler-search"
              class="me-2"
            />
            Tìm Kiếm Nhân Viên
          </VCardTitle>
          <VDivider />
          <VCardText>
            <VRow>
              <VCol
                cols="12"
                md="3"
              >
                <VTextField
                  v-model="searchName"
                  label="Tên nhân viên"
                  placeholder="Tìm theo tên (Trung/Anh)"
                  variant="outlined"
                  prepend-inner-icon="tabler-user"
                  clearable
                  @keyup.enter="searchEmployees(true)"
                />
              </VCol>
              <VCol
                cols="12"
                md="3"
              >
                <VTextField
                  v-model="searchDepartmentCode"
                  label="Mã phòng ban"
                  placeholder="VD: 081, 103"
                  variant="outlined"
                  prepend-inner-icon="tabler-building"
                  clearable
                  @keyup.enter="searchEmployees(true)"
                />
              </VCol>
              <VCol
                cols="12"
                md="3"
              >
                <VTextField
                  v-model="searchDormId"
                  label="Mã KTX"
                  placeholder="VD: P123"
                  variant="outlined"
                  prepend-inner-icon="tabler-home"
                  clearable
                  @keyup.enter="searchEmployees(true)"
                />
              </VCol>
              <VCol
                cols="12"
                md="3"
                class="d-flex align-end"
              >
                <VBtn
                  color="primary"
                  :block="$vuetify.display.smAndDown"
                  :width="$vuetify.display.mdAndUp ? 140 : undefined"
                  :loading="loading"
                  @click="searchEmployees(true)"
                >
                  <VIcon
                    start
                    icon="tabler-search"
                  />
                  Tìm Kiếm
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
      class="mt-4"
      @click:close="error = null"
    >
      {{ error }}
    </VAlert>

    <!-- Loading State -->
    <VRow
      v-if="loading"
      class="mt-4"
    >
      <VCol cols="12">
        <VCard>
          <VCardText class="text-center py-16">
            <VProgressCircular
              indeterminate
              color="primary"
              size="64"
            />
            <p class="text-body-1 mt-4">
              Đang tìm kiếm...
            </p>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <!-- Results Table -->
    <VRow
      v-if="!loading && employees.length > 0"
      class="mt-4"
    >
      <VCol cols="12">
        <VCard>
          <VCardTitle class="d-flex align-center justify-space-between">
            <div>
              <VIcon
                icon="tabler-table"
                class="me-2"
              />
              Kết Quả Tìm Kiếm
            </div>
            <VChip
              color="primary"
              variant="tonal"
            >
              {{ total }} nhân viên
            </VChip>
          </VCardTitle>
          <VDivider />
          <VCardText class="pa-0">
            <VDataTable
              :headers="headers"
              :items="employees"
              :items-per-page="itemsPerPage"
              hide-default-footer
              class="employee-table"
            >
              <template #item.id="{ item }">
                <VChip
                  color="primary"
                  variant="flat"
                  size="small"
                >
                  {{ item.id }}
                </VChip>
              </template>

              <template #item.name_tw="{ item }">
                <span class="font-weight-medium">{{ item.name_tw || 'N/A' }}</span>
              </template>

              <template #item.name_en="{ item }">
                {{ item.name_en || 'N/A' }}
              </template>

              <template #item.dob="{ item }">
                {{ item.dob || 'N/A' }}
              </template>

              <template #item.dept="{ item }">
                <div
                  class="text-truncate"
                  style="max-width: 200px;"
                  :title="item.dept"
                >
                  {{ item.dept || 'N/A' }}
                </div>
              </template>

              <template #item.department_code="{ item }">
                <VChip
                  color="info"
                  variant="tonal"
                  size="small"
                >
                  {{ item.department_code || 'N/A' }}
                </VChip>
              </template>

              <template #item.job_title="{ item }">
                <div
                  class="text-truncate"
                  style="max-width: 150px;"
                  :title="item.job_title"
                >
                  {{ item.job_title || 'N/A' }}
                </div>
              </template>

              <template #item.salary="{ item }">
                <span class="text-success font-weight-medium">
                  {{ item.salary ? formatCurrency(item.salary) : 'N/A' }}
                </span>
              </template>

              <template #item.phone1="{ item }">
                {{ item.phone1 || 'N/A' }}
              </template>

              <template #item.dorm_id="{ item }">
                <VChip
                  v-if="item.dorm_id"
                  color="warning"
                  variant="tonal"
                  size="small"
                >
                  {{ item.dorm_id }}
                </VChip>
                <span
                  v-else
                  class="text-medium-emphasis"
                >N/A</span>
              </template>
            </VDataTable>
          </VCardText>

          <!-- Pagination -->
          <VDivider />
          <VCardText class="d-flex align-center justify-space-between flex-wrap gap-4">
            <div class="d-flex align-center gap-3">
              <div class="text-body-2 text-medium-emphasis">
                Hiển thị {{ total === 0 ? 0 : ((page - 1) * itemsPerPage) + 1 }} - {{ Math.min(((page - 1) * itemsPerPage) + employees.length, total) }} trong tổng số {{ total }} nhân viên
              </div>
              <VSelect
                v-model="itemsPerPage"
                :items="itemsPerPageOptions"
                variant="outlined"
                density="compact"
                hide-details
                style="max-width: 100px;"
                @update:model-value="onItemsPerPageChange"
              />
            </div>
            <VPagination
              v-model="page"
              :length="totalPages"
              :total-visible="7"
              @update:model-value="onPageChange"
            />
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <!-- No Results State -->
    <VRow
      v-if="!loading && employees.length === 0 && (searchName || searchDepartmentCode || searchDormId)"
      class="mt-4"
    >
      <VCol cols="12">
        <VCard>
          <VCardText class="text-center py-16">
            <VIcon
              icon="tabler-search-off"
              size="64"
              color="grey-lighten-1"
              class="mb-4"
            />
            <p class="text-h6 text-medium-emphasis mb-2">
              Không tìm thấy kết quả
            </p>
            <p class="text-body-2 text-medium-emphasis">
              Thử thay đổi các tiêu chí tìm kiếm hoặc nhấn "Tìm Kiếm" để xem tất cả nhân viên
            </p>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <!-- Initial State -->
    <VRow
      v-if="!loading && employees.length === 0 && !searchName && !searchDepartmentCode && !searchDormId && !error"
      class="mt-4"
    >
      <VCol cols="12">
        <VCard>
          <VCardText class="text-center py-16">
            <VIcon
              icon="tabler-users"
              size="64"
              color="grey-lighten-1"
              class="mb-4"
            />
            <p class="text-h6 text-medium-emphasis mb-2">
              Tìm kiếm nhân viên
            </p>
            <p class="text-body-2 text-medium-emphasis">
              Nhập điều kiện tìm kiếm hoặc nhấn "Tìm Kiếm" để xem danh sách nhân viên theo trang
            </p>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>
  </div>
</template>

<style scoped>
.employee-table :deep(.v-data-table__td) {
  white-space: nowrap;
}
</style>
