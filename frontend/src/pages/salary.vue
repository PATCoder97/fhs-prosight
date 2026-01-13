<script setup>
import { ref, onMounted, computed } from 'vue'
import { useGuestProtection } from '@/composables/useGuestProtection'

// Protect from guest users
useGuestProtection()

// State
const loading = ref(false)
const salaryData = ref(null)
const salaryHistory = ref(null)
const selectedYear = ref(new Date().getFullYear())
const selectedMonth = ref(new Date().getMonth() + 1)
const error = ref(null)

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
  loading.value = true
  error.value = null

  try {
    const response = await $api(`/hrs-data/salary?year=${selectedYear.value}&month=${selectedMonth.value}`)
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

// Load salary history
const loadSalaryHistory = async () => {
  loading.value = true
  error.value = null

  try {
    const response = await $api(`/hrs-data/salary/history?year=${selectedYear.value}&from_month=1&to_month=12`)
    salaryHistory.value = response
  }
  catch (err) {
    console.error('Failed to load salary history:', err)
    error.value = err.message || 'Không thể tải lịch sử lương'
    salaryHistory.value = null
  }
  finally {
    loading.value = false
  }
}

// Format currency
const formatCurrency = (amount) => {
  if (!amount) return '0 ₫'
  return new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND',
  }).format(amount)
}

// Format percentage
const formatPercentage = (value) => {
  if (!value) return '0%'
  return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`
}

// Get trend color
const getTrendColor = (trend) => {
  if (!trend) return 'grey'
  if (trend === 'increasing') return 'success'
  if (trend === 'decreasing') return 'error'
  return 'warning'
}

// Get trend icon
const getTrendIcon = (trend) => {
  if (!trend) return 'tabler-minus'
  if (trend === 'increasing') return 'tabler-trending-up'
  if (trend === 'decreasing') return 'tabler-trending-down'
  return 'tabler-minus'
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

// On month/year change
const onFilterChange = () => {
  loadSalary()
}

// On view history
const onViewHistory = () => {
  loadSalaryHistory()
}

// Load data on mount
onMounted(async () => {
  await loadSalary()
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
              💰 Thông Tin Lương
            </h2>
            <p class="text-body-1 text-medium-emphasis">
              Xem thông tin lương và lịch sử lương của bạn
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

    <!-- Filter Section -->
    <VRow>
      <VCol
        cols="12"
        md="4"
      >
        <VSelect
          v-model="selectedYear"
          :items="yearOptions"
          item-title="label"
          item-value="value"
          label="Năm"
          variant="outlined"
          @update:model-value="onFilterChange"
        />
      </VCol>
      <VCol
        cols="12"
        md="4"
      >
        <VSelect
          v-model="selectedMonth"
          :items="monthOptions"
          item-title="label"
          item-value="value"
          label="Tháng"
          variant="outlined"
          @update:model-value="onFilterChange"
        />
      </VCol>
      <VCol
        cols="12"
        md="4"
        class="d-flex align-center"
      >
        <VBtn
          color="secondary"
          variant="tonal"
          block
          @click="onViewHistory"
        >
          <VIcon
            start
            icon="tabler-history"
          />
          Xem Lịch Sử
        </VBtn>
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
        <VCard>
          <VCardTitle class="d-flex align-center justify-space-between">
            <span>
              <VIcon
                icon="tabler-currency-dong"
                class="me-2"
              />
              Lương Tháng {{ selectedMonth }}/{{ selectedYear }}
            </span>
            <VChip
              color="success"
              variant="flat"
            >
              {{ formatCurrency(salaryData.net_salary) }}
            </VChip>
          </VCardTitle>

          <VDivider />

          <VCardText>
            <VRow>
              <!-- Basic Salary -->
              <VCol
                cols="12"
                md="6"
              >
                <div class="d-flex align-center justify-space-between mb-4">
                  <div class="d-flex align-center">
                    <VAvatar
                      color="primary"
                      variant="tonal"
                      class="me-3"
                    >
                      <VIcon icon="tabler-coins" />
                    </VAvatar>
                    <div>
                      <p class="text-caption text-medium-emphasis mb-0">
                        Lương Cơ Bản
                      </p>
                      <p class="text-h6 font-weight-bold mb-0">
                        {{ formatCurrency(salaryData.basic_salary) }}
                      </p>
                    </div>
                  </div>
                </div>
              </VCol>

              <!-- Allowance -->
              <VCol
                cols="12"
                md="6"
              >
                <div class="d-flex align-center justify-space-between mb-4">
                  <div class="d-flex align-center">
                    <VAvatar
                      color="info"
                      variant="tonal"
                      class="me-3"
                    >
                      <VIcon icon="tabler-gift" />
                    </VAvatar>
                    <div>
                      <p class="text-caption text-medium-emphasis mb-0">
                        Phụ Cấp
                      </p>
                      <p class="text-h6 font-weight-bold mb-0">
                        {{ formatCurrency(salaryData.allowance) }}
                      </p>
                    </div>
                  </div>
                </div>
              </VCol>

              <!-- Bonus -->
              <VCol
                cols="12"
                md="6"
              >
                <div class="d-flex align-center justify-space-between mb-4">
                  <div class="d-flex align-center">
                    <VAvatar
                      color="success"
                      variant="tonal"
                      class="me-3"
                    >
                      <VIcon icon="tabler-award" />
                    </VAvatar>
                    <div>
                      <p class="text-caption text-medium-emphasis mb-0">
                        Thưởng
                      </p>
                      <p class="text-h6 font-weight-bold mb-0">
                        {{ formatCurrency(salaryData.bonus) }}
                      </p>
                    </div>
                  </div>
                </div>
              </VCol>

              <!-- Deduction -->
              <VCol
                cols="12"
                md="6"
              >
                <div class="d-flex align-center justify-space-between mb-4">
                  <div class="d-flex align-center">
                    <VAvatar
                      color="error"
                      variant="tonal"
                      class="me-3"
                    >
                      <VIcon icon="tabler-receipt-tax" />
                    </VAvatar>
                    <div>
                      <p class="text-caption text-medium-emphasis mb-0">
                        Khấu Trừ
                      </p>
                      <p class="text-h6 font-weight-bold mb-0">
                        {{ formatCurrency(salaryData.deduction) }}
                      </p>
                    </div>
                  </div>
                </div>
              </VCol>
            </VRow>

            <VDivider class="my-4" />

            <!-- Net Salary -->
            <div class="d-flex align-center justify-space-between pa-4 bg-primary-subtle rounded">
              <div>
                <p class="text-caption text-medium-emphasis mb-1">
                  TỔNG LƯƠNG THỰC LĨNH
                </p>
                <p class="text-h4 font-weight-bold text-primary mb-0">
                  {{ formatCurrency(salaryData.net_salary) }}
                </p>
              </div>
              <VIcon
                icon="tabler-wallet"
                size="48"
                color="primary"
              />
            </div>

            <!-- Additional Info -->
            <VRow
              v-if="salaryData.payment_date || salaryData.notes"
              class="mt-4"
            >
              <VCol
                v-if="salaryData.payment_date"
                cols="12"
                md="6"
              >
                <VAlert
                  variant="tonal"
                  color="info"
                  density="compact"
                >
                  <div class="d-flex align-center">
                    <VIcon
                      icon="tabler-calendar"
                      class="me-2"
                    />
                    <span>Ngày thanh toán: <strong>{{ salaryData.payment_date }}</strong></span>
                  </div>
                </VAlert>
              </VCol>
              <VCol
                v-if="salaryData.notes"
                cols="12"
                md="6"
              >
                <VAlert
                  variant="tonal"
                  color="warning"
                  density="compact"
                >
                  <div class="d-flex align-center">
                    <VIcon
                      icon="tabler-note"
                      class="me-2"
                    />
                    <span>{{ salaryData.notes }}</span>
                  </div>
                </VAlert>
              </VCol>
            </VRow>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <!-- Salary History -->
    <VRow v-if="!loading && salaryHistory">
      <VCol cols="12">
        <VCard>
          <VCardTitle class="d-flex align-center justify-space-between">
            <span>
              <VIcon
                icon="tabler-history"
                class="me-2"
              />
              Lịch Sử Lương Năm {{ selectedYear }}
            </span>
            <VChip
              v-if="salaryHistory.trend"
              :color="getTrendColor(salaryHistory.trend)"
              variant="flat"
            >
              <VIcon
                :icon="getTrendIcon(salaryHistory.trend)"
                start
              />
              {{ salaryHistory.trend === 'increasing' ? 'Tăng' : salaryHistory.trend === 'decreasing' ? 'Giảm' : 'Ổn định' }}
            </VChip>
          </VCardTitle>

          <VDivider />

          <VCardText>
            <!-- Summary Statistics -->
            <VRow class="mb-6">
              <VCol
                cols="12"
                md="3"
              >
                <VCard
                  variant="tonal"
                  color="primary"
                >
                  <VCardText class="text-center">
                    <p class="text-caption mb-1">
                      Trung Bình
                    </p>
                    <p class="text-h6 font-weight-bold mb-0">
                      {{ formatCurrency(salaryHistory.average_salary) }}
                    </p>
                  </VCardText>
                </VCard>
              </VCol>
              <VCol
                cols="12"
                md="3"
              >
                <VCard
                  variant="tonal"
                  color="success"
                >
                  <VCardText class="text-center">
                    <p class="text-caption mb-1">
                      Cao Nhất
                    </p>
                    <p class="text-h6 font-weight-bold mb-0">
                      {{ formatCurrency(salaryHistory.max_salary) }}
                    </p>
                  </VCardText>
                </VCard>
              </VCol>
              <VCol
                cols="12"
                md="3"
              >
                <VCard
                  variant="tonal"
                  color="warning"
                >
                  <VCardText class="text-center">
                    <p class="text-caption mb-1">
                      Thấp Nhất
                    </p>
                    <p class="text-h6 font-weight-bold mb-0">
                      {{ formatCurrency(salaryHistory.min_salary) }}
                    </p>
                  </VCardText>
                </VCard>
              </VCol>
              <VCol
                cols="12"
                md="3"
              >
                <VCard
                  variant="tonal"
                  color="info"
                >
                  <VCardText class="text-center">
                    <p class="text-caption mb-1">
                      Tổng Thu Nhập
                    </p>
                    <p class="text-h6 font-weight-bold mb-0">
                      {{ formatCurrency(salaryHistory.total_income) }}
                    </p>
                  </VCardText>
                </VCard>
              </VCol>
            </VRow>

            <!-- Monthly Data Table -->
            <VTable>
              <thead>
                <tr>
                  <th>Tháng</th>
                  <th class="text-end">
                    Lương Cơ Bản
                  </th>
                  <th class="text-end">
                    Phụ Cấp
                  </th>
                  <th class="text-end">
                    Thưởng
                  </th>
                  <th class="text-end">
                    Thực Lĩnh
                  </th>
                  <th class="text-center">
                    Xu Hướng
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="item in salaryHistory.monthly_data"
                  :key="item.month"
                >
                  <td>
                    <strong>Tháng {{ item.month }}</strong>
                  </td>
                  <td class="text-end">
                    {{ formatCurrency(item.basic_salary) }}
                  </td>
                  <td class="text-end">
                    {{ formatCurrency(item.allowance) }}
                  </td>
                  <td class="text-end">
                    {{ formatCurrency(item.bonus) }}
                  </td>
                  <td class="text-end">
                    <strong>{{ formatCurrency(item.net_salary) }}</strong>
                  </td>
                  <td class="text-center">
                    <VChip
                      v-if="item.change_percentage !== null"
                      :color="item.change_percentage > 0 ? 'success' : item.change_percentage < 0 ? 'error' : 'grey'"
                      size="small"
                      variant="flat"
                    >
                      {{ formatPercentage(item.change_percentage) }}
                    </VChip>
                  </td>
                </tr>
              </tbody>
            </VTable>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <!-- No Data State -->
    <VRow v-if="!loading && !salaryData && !salaryHistory">
      <VCol cols="12">
        <VCard>
          <VCardText class="text-center py-16">
            <VIcon
              icon="tabler-file-search"
              size="64"
              color="grey-lighten-1"
              class="mb-4"
            />
            <p class="text-h6 text-medium-emphasis mb-2">
              Không có dữ liệu lương
            </p>
            <p class="text-body-2 text-medium-emphasis">
              Vui lòng chọn tháng/năm khác hoặc liên hệ bộ phận nhân sự
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
</style>
