<script setup>
import { ref, computed } from 'vue'
import { useGuestProtection } from '@/composables/useGuestProtection'

// Protect from guest users
useGuestProtection()

// State
const loading = ref(false)
const salaryData = ref(null)
const error = ref(null)

// Form inputs
const employeeId = ref('')
const selectedYear = ref(new Date().getFullYear())
const selectedMonth = ref(new Date().getMonth() + 1)

// Get current user
const currentUser = computed(() => {
  try {
    const storedUser = localStorage.getItem('user')
    if (storedUser) {
      return JSON.parse(storedUser)
    }
  }
  catch (error) {
    console.error('Failed to parse user data:', error)
  }
  return null
})

// Load salary data
const loadSalary = async () => {
  // Validate employee ID
  if (!employeeId.value || !employeeId.value.trim()) {
    error.value = 'Vui lòng nhập Employee ID'
    return
  }

  loading.value = true
  error.value = null
  salaryData.value = null

  try {
    const response = await $api(
      `/hrs-data/salary/${employeeId.value}?year=${selectedYear.value}&month=${selectedMonth.value}`
    )
    salaryData.value = response
  }
  catch (err) {
    console.error('Failed to load salary:', err)
    error.value = err.message || 'Không thể tải thông tin lương'
    salaryData.value = null
  }
  finally {
    loading.value = false
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

// Month options
const monthOptions = [
  { value: 1, label: 'Tháng 1' },
  { value: 2, label: 'Tháng 2' },
  { value: 3, label: 'Tháng 3' },
  { value: 4, label: 'Tháng 4' },
  { value: 5, label: 'Tháng 5' },
  { value: 6, label: 'Tháng 6' },
  { value: 7, label: 'Tháng 7' },
  { value: 8, label: 'Tháng 8' },
  { value: 9, label: 'Tháng 9' },
  { value: 10, label: 'Tháng 10' },
  { value: 11, label: 'Tháng 11' },
  { value: 12, label: 'Tháng 12' },
]

// Year options (last 5 years)
const yearOptions = computed(() => {
  const currentYear = new Date().getFullYear()
  return Array.from({ length: 5 }, (_, i) => ({
    value: currentYear - i,
    label: `Năm ${currentYear - i}`,
  }))
})
</script>

<template>
  <div>
    <!-- Page Header -->
    <VRow>
      <VCol cols="12">
        <div class="d-flex align-center justify-space-between mb-6">
          <div>
            <h2 class="text-h4 font-weight-bold mb-1">
              💰 Tra Cứu Lương
            </h2>
            <p class="text-body-1 text-medium-emphasis">
              Tra cứu thông tin lương theo Employee ID
            </p>
          </div>
          <VChip
            v-if="currentUser"
            color="primary"
            variant="tonal"
            size="large"
          >
            <VIcon
              start
              icon="tabler-user"
            />
            {{ currentUser.full_name || currentUser.email }}
          </VChip>
        </div>
      </VCol>
    </VRow>

    <!-- Search Form -->
    <VRow>
      <VCol cols="12">
        <VCard>
          <VCardTitle>
            <VIcon
              icon="tabler-search"
              class="me-2"
            />
            Thông Tin Tra Cứu
          </VCardTitle>
          <VDivider />
          <VCardText>
            <VRow>
              <VCol
                cols="12"
                md="4"
              >
                <VTextField
                  v-model="employeeId"
                  label="Employee ID"
                  placeholder="VD: VNW0014732"
                  variant="outlined"
                  prepend-inner-icon="tabler-id"
                  @keyup.enter="loadSalary"
                />
              </VCol>
              <VCol
                cols="12"
                md="3"
              >
                <VSelect
                  v-model="selectedYear"
                  :items="yearOptions"
                  item-title="label"
                  item-value="value"
                  label="Năm"
                  variant="outlined"
                />
              </VCol>
              <VCol
                cols="12"
                md="3"
              >
                <VSelect
                  v-model="selectedMonth"
                  :items="monthOptions"
                  item-title="label"
                  item-value="value"
                  label="Tháng"
                  variant="outlined"
                />
              </VCol>
              <VCol
                cols="12"
                md="2"
              >
                <VBtn
                  color="primary"
                  block
                  height="56"
                  @click="loadSalary"
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
              Đang tải dữ liệu...
            </p>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <!-- Salary Data -->
    <VRow v-if="!loading && salaryData">
      <VCol cols="12">
        <!-- Employee Info -->
        <VCard class="mb-4">
          <VCardText>
            <VRow>
              <VCol
                cols="12"
                md="6"
              >
                <div class="d-flex align-center">
                  <VAvatar
                    color="primary"
                    size="48"
                    class="me-3"
                  >
                    <VIcon
                      icon="tabler-user"
                      size="24"
                    />
                  </VAvatar>
                  <div>
                    <p class="text-caption text-medium-emphasis mb-0">
                      Nhân viên
                    </p>
                    <p class="text-h6 font-weight-bold mb-0">
                      {{ salaryData.employee_name || salaryData.employee_id }}
                    </p>
                  </div>
                </div>
              </VCol>
              <VCol
                cols="12"
                md="3"
              >
                <p class="text-caption text-medium-emphasis mb-1">
                  Employee ID
                </p>
                <VChip
                  color="info"
                  variant="flat"
                >
                  {{ salaryData.employee_id }}
                </VChip>
              </VCol>
              <VCol
                cols="12"
                md="3"
              >
                <p class="text-caption text-medium-emphasis mb-1">
                  Kỳ lương
                </p>
                <VChip
                  color="success"
                  variant="flat"
                >
                  {{ salaryData.period.month }}/{{ salaryData.period.year }}
                </VChip>
              </VCol>
            </VRow>
          </VCardText>
        </VCard>

        <!-- Summary Card -->
        <VCard class="mb-4">
          <VCardTitle>
            <VIcon
              icon="tabler-report-money"
              class="me-2"
            />
            Tổng Quan
          </VCardTitle>
          <VDivider />
          <VCardText>
            <VRow>
              <VCol
                cols="12"
                md="4"
              >
                <VCard
                  variant="tonal"
                  color="success"
                >
                  <VCardText class="text-center">
                    <VIcon
                      icon="tabler-coin"
                      size="32"
                      class="mb-2"
                    />
                    <p class="text-caption mb-1">
                      Tổng Tiền Công
                    </p>
                    <p class="text-h5 font-weight-bold mb-0">
                      {{ formatCurrency(salaryData.summary.tong_tien_cong) }}
                    </p>
                  </VCardText>
                </VCard>
              </VCol>
              <VCol
                cols="12"
                md="4"
              >
                <VCard
                  variant="tonal"
                  color="error"
                >
                  <VCardText class="text-center">
                    <VIcon
                      icon="tabler-receipt-tax"
                      size="32"
                      class="mb-2"
                    />
                    <p class="text-caption mb-1">
                      Tổng Tiền Trừ
                    </p>
                    <p class="text-h5 font-weight-bold mb-0">
                      {{ formatCurrency(salaryData.summary.tong_tien_tru) }}
                    </p>
                  </VCardText>
                </VCard>
              </VCol>
              <VCol
                cols="12"
                md="4"
              >
                <VCard
                  variant="tonal"
                  color="primary"
                >
                  <VCardText class="text-center">
                    <VIcon
                      icon="tabler-wallet"
                      size="32"
                      class="mb-2"
                    />
                    <p class="text-caption mb-1">
                      Thực Lĩnh
                    </p>
                    <p class="text-h5 font-weight-bold mb-0">
                      {{ formatCurrency(salaryData.summary.thuc_linh) }}
                    </p>
                  </VCardText>
                </VCard>
              </VCol>
            </VRow>
          </VCardText>
        </VCard>

        <!-- Income Details -->
        <VCard class="mb-4">
          <VCardTitle class="bg-success-subtle">
            <VIcon
              icon="tabler-trending-up"
              class="me-2"
            />
            Chi Tiết Thu Nhập
          </VCardTitle>
          <VDivider />
          <VCardText>
            <VTable density="comfortable">
              <tbody>
                <tr v-if="salaryData.income.luong_co_ban">
                  <td class="font-weight-medium">
                    Lương Cơ Bản
                  </td>
                  <td class="text-end">
                    {{ formatCurrency(salaryData.income.luong_co_ban) }}
                  </td>
                </tr>
                <tr v-if="salaryData.income.thuong_nang_suat">
                  <td class="font-weight-medium">
                    Thưởng Năng Suất
                  </td>
                  <td class="text-end">
                    {{ formatCurrency(salaryData.income.thuong_nang_suat) }}
                  </td>
                </tr>
                <tr v-if="salaryData.income.thuong_tet">
                  <td class="font-weight-medium">
                    Thưởng Tết
                  </td>
                  <td class="text-end">
                    {{ formatCurrency(salaryData.income.thuong_tet) }}
                  </td>
                </tr>
                <tr v-if="salaryData.income.tro_cap_com">
                  <td class="font-weight-medium">
                    Trợ Cấp Cơm
                  </td>
                  <td class="text-end">
                    {{ formatCurrency(salaryData.income.tro_cap_com) }}
                  </td>
                </tr>
                <tr v-if="salaryData.income.tro_cap_di_lai">
                  <td class="font-weight-medium">
                    Trợ Cấp Đi Lại
                  </td>
                  <td class="text-end">
                    {{ formatCurrency(salaryData.income.tro_cap_di_lai) }}
                  </td>
                </tr>
                <tr v-if="salaryData.income.thuong_chuyen_can">
                  <td class="font-weight-medium">
                    Thưởng Chuyên Cần
                  </td>
                  <td class="text-end">
                    {{ formatCurrency(salaryData.income.thuong_chuyen_can) }}
                  </td>
                </tr>
                <tr v-if="salaryData.income.phu_cap_dac_biet">
                  <td class="font-weight-medium">
                    Phụ Cấp Đặc Biệt
                  </td>
                  <td class="text-end">
                    {{ formatCurrency(salaryData.income.phu_cap_dac_biet) }}
                  </td>
                </tr>
                <tr v-if="salaryData.income.phu_cap_tac_nghiep">
                  <td class="font-weight-medium">
                    Phụ Cấp Tác Nghiệp
                  </td>
                  <td class="text-end">
                    {{ formatCurrency(salaryData.income.phu_cap_tac_nghiep) }}
                  </td>
                </tr>
                <tr v-if="salaryData.income.phi_khac">
                  <td class="font-weight-medium">
                    Phí Khác
                  </td>
                  <td class="text-end">
                    {{ formatCurrency(salaryData.income.phi_khac) }}
                  </td>
                </tr>
                <tr v-if="salaryData.income.tro_cap_com2">
                  <td class="font-weight-medium">
                    Trợ Cấp Cơm 2
                  </td>
                  <td class="text-end">
                    {{ formatCurrency(salaryData.income.tro_cap_com2) }}
                  </td>
                </tr>
              </tbody>
              <tfoot>
                <tr class="font-weight-bold bg-success-subtle">
                  <td>TỔNG THU NHẬP</td>
                  <td class="text-end text-success">
                    {{ formatCurrency(salaryData.summary.tong_tien_cong) }}
                  </td>
                </tr>
              </tfoot>
            </VTable>
          </VCardText>
        </VCard>

        <!-- Deductions Details -->
        <VCard>
          <VCardTitle class="bg-error-subtle">
            <VIcon
              icon="tabler-trending-down"
              class="me-2"
            />
            Chi Tiết Khấu Trừ
          </VCardTitle>
          <VDivider />
          <VCardText>
            <VTable density="comfortable">
              <tbody>
                <tr v-if="salaryData.deductions.bhxh">
                  <td class="font-weight-medium">
                    Bảo Hiểm Xã Hội
                  </td>
                  <td class="text-end">
                    {{ formatCurrency(salaryData.deductions.bhxh) }}
                  </td>
                </tr>
                <tr v-if="salaryData.deductions.bhyt">
                  <td class="font-weight-medium">
                    Bảo Hiểm Y Tế
                  </td>
                  <td class="text-end">
                    {{ formatCurrency(salaryData.deductions.bhyt) }}
                  </td>
                </tr>
                <tr v-if="salaryData.deductions.bh_that_nghiep">
                  <td class="font-weight-medium">
                    Bảo Hiểm Thất Nghiệp
                  </td>
                  <td class="text-end">
                    {{ formatCurrency(salaryData.deductions.bh_that_nghiep) }}
                  </td>
                </tr>
                <tr v-if="salaryData.deductions.ky_tuc_xa">
                  <td class="font-weight-medium">
                    Ký Túc Xá
                  </td>
                  <td class="text-end">
                    {{ formatCurrency(salaryData.deductions.ky_tuc_xa) }}
                  </td>
                </tr>
                <tr v-if="salaryData.deductions.cong_doan">
                  <td class="font-weight-medium">
                    Công Đoàn
                  </td>
                  <td class="text-end">
                    {{ formatCurrency(salaryData.deductions.cong_doan) }}
                  </td>
                </tr>
                <tr v-if="salaryData.deductions.thue_thu_nhap">
                  <td class="font-weight-medium">
                    Thuế Thu Nhập Cá Nhân
                  </td>
                  <td class="text-end">
                    {{ formatCurrency(salaryData.deductions.thue_thu_nhap) }}
                  </td>
                </tr>
                <tr v-if="salaryData.deductions.khac">
                  <td class="font-weight-medium">
                    Khác
                  </td>
                  <td class="text-end">
                    {{ formatCurrency(salaryData.deductions.khac) }}
                  </td>
                </tr>
              </tbody>
              <tfoot>
                <tr class="font-weight-bold bg-error-subtle">
                  <td>TỔNG KHẤU TRỪ</td>
                  <td class="text-end text-error">
                    {{ formatCurrency(salaryData.summary.tong_tien_tru) }}
                  </td>
                </tr>
              </tfoot>
            </VTable>
          </VCardText>
        </VCard>

        <!-- Net Salary -->
        <VCard class="mt-4">
          <VCardText>
            <div class="d-flex align-center justify-space-between pa-4 bg-primary-subtle rounded">
              <div>
                <p class="text-caption text-medium-emphasis mb-1">
                  TỔNG LƯƠNG THỰC LĨNH
                </p>
                <p class="text-h3 font-weight-bold text-primary mb-0">
                  {{ formatCurrency(salaryData.summary.thuc_linh) }}
                </p>
              </div>
              <VIcon
                icon="tabler-currency-dong"
                size="64"
                color="primary"
                class="opacity-50"
              />
            </div>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <!-- No Data State -->
    <VRow v-if="!loading && !salaryData && !error">
      <VCol cols="12">
        <VCard>
          <VCardText class="text-center py-16">
            <VIcon
              icon="tabler-search"
              size="64"
              color="grey-lighten-1"
              class="mb-4"
            />
            <p class="text-h6 text-medium-emphasis mb-2">
              Nhập thông tin để tra cứu
            </p>
            <p class="text-body-2 text-medium-emphasis">
              Vui lòng nhập Employee ID, chọn tháng/năm và nhấn "Tra Cứu"
            </p>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>
  </div>
</template>

<style scoped>
.bg-primary-subtle {
  background-color: rgba(var(--v-theme-primary), 0.08);
}

.bg-success-subtle {
  background-color: rgba(var(--v-theme-success), 0.08);
}

.bg-error-subtle {
  background-color: rgba(var(--v-theme-error), 0.08);
}
</style>
