<script setup>
import { ref, computed } from 'vue'
import { useGuestProtection } from '@/composables/useGuestProtection'

// Protect from guest users
useGuestProtection()

// State
const loading = ref(false)
const historyData = ref(null)
const error = ref(null)

// Form inputs
const employeeId = ref('')
const selectedYear = ref(new Date().getFullYear())
const fromMonth = ref(1)
const toMonth = ref(12)

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

// Load salary history data
const loadSalaryHistory = async () => {
  // Validate employee ID
  if (!employeeId.value || !employeeId.value.trim()) {
    error.value = 'Vui lòng nhập Employee ID'
    return
  }

  // Validate month range
  if (fromMonth.value > toMonth.value) {
    error.value = 'Tháng bắt đầu phải nhỏ hơn hoặc bằng tháng kết thúc'
    return
  }

  loading.value = true
  error.value = null
  historyData.value = null

  try {
    const response = await $api(
      `/hrs-data/salary/history/${employeeId.value}?year=${selectedYear.value}&from_month=${fromMonth.value}&to_month=${toMonth.value}`
    )
    historyData.value = response
  }
  catch (err) {
    console.error('Failed to load salary history:', err)
    error.value = err.message || 'Không thể tải lịch sử lương'
    historyData.value = null
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

// Format month display
const formatMonth = (month) => {
  return `Tháng ${month}`
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

// Calculate trend percentage
const getTrendPercentage = (current, previous) => {
  if (!previous || previous === 0) return 0
  return ((current - previous) / previous * 100).toFixed(1)
}

// Get trend icon and color
const getTrendIcon = (percentage) => {
  if (percentage > 0) return { icon: 'tabler-trending-up', color: 'success' }
  if (percentage < 0) return { icon: 'tabler-trending-down', color: 'error' }
  return { icon: 'tabler-minus', color: 'warning' }
}
</script>

<template>
  <div>
    <!-- Page Header -->
    <VRow>
      <VCol cols="12">
        <div class="d-flex align-center justify-space-between mb-6">
          <div>
            <h2 class="text-h4 font-weight-bold mb-1">
              📊 Lịch Sử Lương
            </h2>
            <p class="text-body-1 text-medium-emphasis">
              Tra cứu lịch sử lương theo khoảng thời gian với phân tích xu hướng
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
                md="3"
              >
                <VTextField
                  v-model="employeeId"
                  label="Employee ID"
                  placeholder="VD: VNW0014732"
                  variant="outlined"
                  prepend-inner-icon="tabler-id"
                  @keyup.enter="loadSalaryHistory"
                />
              </VCol>
              <VCol
                cols="12"
                md="2"
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
                md="2"
              >
                <VSelect
                  v-model="fromMonth"
                  :items="monthOptions"
                  item-title="label"
                  item-value="value"
                  label="Từ tháng"
                  variant="outlined"
                />
              </VCol>
              <VCol
                cols="12"
                md="2"
              >
                <VSelect
                  v-model="toMonth"
                  :items="monthOptions"
                  item-title="label"
                  item-value="value"
                  label="Đến tháng"
                  variant="outlined"
                />
              </VCol>
              <VCol
                cols="12"
                md="3"
                class="d-flex align-end"
              >
                <VBtn
                  color="primary"
                  block
                  @click="loadSalaryHistory"
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

    <!-- Salary History Data -->
    <VRow v-if="!loading && historyData">
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
                      {{ historyData.employee_name || historyData.employee_id }}
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
                  {{ historyData.employee_id }}
                </VChip>
              </VCol>
              <VCol
                cols="12"
                md="3"
              >
                <p class="text-caption text-medium-emphasis mb-1">
                  Kỳ truy vấn
                </p>
                <VChip
                  color="success"
                  variant="flat"
                >
                  {{ historyData.period.month }} / {{ historyData.period.year }}
                </VChip>
              </VCol>
            </VRow>
          </VCardText>
        </VCard>

        <!-- Trend Analysis -->
        <VCard
          v-if="historyData.trend"
          class="mb-4"
        >
          <VCardTitle class="bg-primary-subtle">
            <VIcon
              icon="tabler-chart-line"
              class="me-2"
            />
            Phân Tích Xu Hướng
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
                      Thu Nhập TB / Tháng
                    </p>
                    <p class="text-h5 font-weight-bold mb-0">
                      {{ formatCurrency(historyData.trend.average_income) }}
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
                      Khấu Trừ TB / Tháng
                    </p>
                    <p class="text-h5 font-weight-bold mb-0">
                      {{ formatCurrency(historyData.trend.average_deductions) }}
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
                      Thực Lĩnh TB / Tháng
                    </p>
                    <p class="text-h5 font-weight-bold mb-0">
                      {{ formatCurrency(historyData.trend.average_net) }}
                    </p>
                  </VCardText>
                </VCard>
              </VCol>
            </VRow>

            <!-- Highest and Lowest Months -->
            <VRow
              v-if="historyData.trend.highest_month && historyData.trend.lowest_month"
              class="mt-4"
            >
              <VCol
                cols="12"
                md="6"
              >
                <VCard
                  variant="outlined"
                  color="success"
                >
                  <VCardText>
                    <div class="d-flex align-center justify-space-between mb-2">
                      <div class="d-flex align-center">
                        <VIcon
                          icon="tabler-arrow-up"
                          color="success"
                          size="24"
                          class="me-2"
                        />
                        <span class="text-body-1 font-weight-medium">Tháng Cao Nhất</span>
                      </div>
                      <VChip
                        color="success"
                        variant="flat"
                        size="small"
                      >
                        {{ formatMonth(historyData.trend.highest_month.month) }}
                      </VChip>
                    </div>
                    <p class="text-h5 font-weight-bold text-success mb-0">
                      {{ formatCurrency(historyData.trend.highest_month.summary.thuc_linh) }}
                    </p>
                  </VCardText>
                </VCard>
              </VCol>
              <VCol
                cols="12"
                md="6"
              >
                <VCard
                  variant="outlined"
                  color="error"
                >
                  <VCardText>
                    <div class="d-flex align-center justify-space-between mb-2">
                      <div class="d-flex align-center">
                        <VIcon
                          icon="tabler-arrow-down"
                          color="error"
                          size="24"
                          class="me-2"
                        />
                        <span class="text-body-1 font-weight-medium">Tháng Thấp Nhất</span>
                      </div>
                      <VChip
                        color="error"
                        variant="flat"
                        size="small"
                      >
                        {{ formatMonth(historyData.trend.lowest_month.month) }}
                      </VChip>
                    </div>
                    <p class="text-h5 font-weight-bold text-error mb-0">
                      {{ formatCurrency(historyData.trend.lowest_month.summary.thuc_linh) }}
                    </p>
                  </VCardText>
                </VCard>
              </VCol>
            </VRow>
          </VCardText>
        </VCard>

        <!-- Monthly History Table -->
        <VCard>
          <VCardTitle>
            <VIcon
              icon="tabler-calendar-stats"
              class="me-2"
            />
            Lịch Sử Theo Tháng
          </VCardTitle>
          <VDivider />
          <VCardText>
            <VTable>
              <thead>
                <tr>
                  <th>Tháng</th>
                  <th class="text-end">
                    Thu Nhập
                  </th>
                  <th class="text-end">
                    Khấu Trừ
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
                  v-for="(monthData, index) in historyData.months"
                  :key="monthData.month"
                >
                  <td>
                    <VChip
                      color="primary"
                      variant="tonal"
                      size="small"
                    >
                      {{ formatMonth(monthData.month) }}
                    </VChip>
                  </td>
                  <td class="text-end text-success">
                    {{ formatCurrency(monthData.summary.tong_tien_cong) }}
                  </td>
                  <td class="text-end text-error">
                    {{ formatCurrency(monthData.summary.tong_tien_tru) }}
                  </td>
                  <td class="text-end">
                    <strong>{{ formatCurrency(monthData.summary.thuc_linh) }}</strong>
                  </td>
                  <td class="text-center">
                    <VChip
                      v-if="index > 0"
                      :color="getTrendIcon(getTrendPercentage(monthData.summary.thuc_linh, historyData.months[index - 1].summary.thuc_linh)).color"
                      variant="tonal"
                      size="small"
                    >
                      <VIcon
                        :icon="getTrendIcon(getTrendPercentage(monthData.summary.thuc_linh, historyData.months[index - 1].summary.thuc_linh)).icon"
                        size="16"
                        start
                      />
                      {{ Math.abs(getTrendPercentage(monthData.summary.thuc_linh, historyData.months[index - 1].summary.thuc_linh)) }}%
                    </VChip>
                    <VChip
                      v-else
                      color="grey"
                      variant="tonal"
                      size="small"
                    >
                      -
                    </VChip>
                  </td>
                </tr>
              </tbody>
              <tfoot v-if="historyData.trend">
                <tr class="font-weight-bold bg-primary-subtle">
                  <td>TRUNG BÌNH</td>
                  <td class="text-end text-success">
                    {{ formatCurrency(historyData.trend.average_income) }}
                  </td>
                  <td class="text-end text-error">
                    {{ formatCurrency(historyData.trend.average_deductions) }}
                  </td>
                  <td class="text-end">
                    {{ formatCurrency(historyData.trend.average_net) }}
                  </td>
                  <td />
                </tr>
              </tfoot>
            </VTable>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <!-- No Data State -->
    <VRow v-if="!loading && !historyData && !error">
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
              Vui lòng nhập Employee ID, chọn năm và khoảng tháng, sau đó nhấn "Tra Cứu"
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
