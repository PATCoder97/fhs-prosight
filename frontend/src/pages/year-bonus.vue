<script setup>
import { ref, computed } from 'vue'
import { useGuestProtection } from '@/composables/useGuestProtection'

// Protect from guest users
useGuestProtection()

// State
const loading = ref(false)
const bonusData = ref(null)
const error = ref(null)

// Form inputs
const employeeId = ref('')
const selectedYear = ref(new Date().getFullYear())

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

// Load year bonus data
const loadYearBonus = async () => {
  // Auto-format employee ID before validation
  const formattedId = formatEmployeeId(employeeId.value)

  // Validate employee ID
  if (!formattedId || !formattedId.trim()) {
    error.value = 'Vui lòng nhập Employee ID'
    return
  }

  // Update employeeId with formatted value
  employeeId.value = formattedId

  loading.value = true
  error.value = null
  bonusData.value = null

  try {
    const response = await $api(
      `/hrs-data/year-bonus/${formattedId}/${selectedYear.value}`
    )
    bonusData.value = response
  }
  catch (err) {
    console.error('Failed to load year bonus:', err)
    error.value = err.message || 'Không thể tải thông tin thưởng'
    bonusData.value = null
  }
  finally {
    loading.value = false
  }
}

// Parse number from string (remove commas)
const parseNumber = (value) => {
  if (!value || value === null) return 0
  if (typeof value === 'number') return value
  // Remove commas and parse: "7,205,600" → 7205600
  const cleaned = value.toString().replace(/,/g, '')
  return parseFloat(cleaned) || 0
}

// Format currency
const formatCurrency = (amount) => {
  const numAmount = parseNumber(amount)
  return new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND',
  }).format(numAmount)
}

// Calculate total bonus (tpnttt + tpntst)
const totalBonus = computed(() => {
  if (!bonusData.value) return 0
  const preTet = parseNumber(bonusData.value.bonus_data.tpnttt)
  const postTet = parseNumber(bonusData.value.bonus_data.tpntst)
  return preTet + postTet
})

// Year options (last 10 years)
const yearOptions = computed(() => {
  const currentYear = new Date().getFullYear()
  return Array.from({ length: 10 }, (_, i) => ({
    value: currentYear - i,
    label: `Năm ${currentYear - i}`,
  }))
})

// Auto-format Employee ID: "14732" → "VNW0014732"
const formatEmployeeId = (input) => {
  if (!input) return ''

  // Remove whitespace
  const cleaned = input.toString().trim()

  // If already starts with VNW, return as-is
  if (cleaned.toUpperCase().startsWith('VNW')) {
    return cleaned.toUpperCase()
  }

  // If just numbers, format as VNW + padded numbers
  if (/^\d+$/.test(cleaned)) {
    const paddedNumber = cleaned.padStart(7, '0')
    return `VNW${paddedNumber}`
  }

  // Otherwise return as-is
  return cleaned
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
              🎁 Tra Cứu Thưởng Tết
            </h2>
            <p class="text-body-1 text-medium-emphasis">
              Tra cứu thông tin thưởng cuối năm theo Employee ID
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
                md="8"
              >
                <VTextField
                  v-model="employeeId"
                  label="Employee ID"
                  placeholder="VD: 14732 hoặc VNW0014732"
                  variant="outlined"
                  prepend-inner-icon="tabler-id"
                  @keyup.enter="loadYearBonus"
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
                class="d-flex align-end"
              >
                <VBtn
                  color="primary"
                  block
                  @click="loadYearBonus"
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

    <!-- Bonus Data -->
    <VRow v-if="!loading && bonusData">
      <VCol cols="12">
        <!-- Employee Info -->
        <VCard class="mb-4">
          <VCardText>
            <VRow>
              <VCol
                cols="12"
                md="4"
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
                      {{ bonusData.employee_name || bonusData.employee_id }}
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
                  {{ bonusData.employee_id }}
                </VChip>
              </VCol>
              <VCol
                cols="12"
                md="2"
              >
                <p class="text-caption text-medium-emphasis mb-1">
                  Năm thưởng
                </p>
                <VChip
                  color="success"
                  variant="flat"
                >
                  {{ bonusData.year }}
                </VChip>
              </VCol>
              <VCol
                cols="12"
                md="3"
              >
                <p class="text-caption text-medium-emphasis mb-1">
                  Cấp bậc
                </p>
                <VChip
                  color="warning"
                  variant="flat"
                >
                  {{ bonusData.bonus_data.capbac || 'N/A' }}
                </VChip>
              </VCol>
            </VRow>
          </VCardText>
        </VCard>

        <!-- Summary Cards -->
        <VRow class="mb-4">
          <VCol
            cols="12"
            md="3"
          >
            <VCard
              variant="tonal"
              color="info"
            >
              <VCardText class="text-center">
                <VIcon
                  icon="tabler-wallet"
                  size="32"
                  class="mb-2"
                />
                <p class="text-caption mb-1">
                  Tổng Lương Cơ Bản
                </p>
                <p class="text-h6 font-weight-bold mb-0">
                  {{ formatCurrency(bonusData.bonus_data.tlcb) }}
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
              color="primary"
            >
              <VCardText class="text-center">
                <VIcon
                  icon="tabler-percentage"
                  size="32"
                  class="mb-2"
                />
                <p class="text-caption mb-1">
                  Tỷ Lệ Thưởng
                </p>
                <p class="text-h6 font-weight-bold mb-0">
                  {{ bonusData.bonus_data.tile || '0%' }}
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
                <VIcon
                  icon="tabler-calendar"
                  size="32"
                  class="mb-2"
                />
                <p class="text-caption mb-1">
                  Tỷ Lệ BHTN
                </p>
                <p class="text-h6 font-weight-bold mb-0">
                  {{ bonusData.bonus_data.stdltbtn || '0%' }}
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
                <VIcon
                  icon="tabler-gift"
                  size="32"
                  class="mb-2"
                />
                <p class="text-caption mb-1">
                  Tổng Thưởng
                </p>
                <p class="text-h6 font-weight-bold mb-0">
                  {{ formatCurrency(totalBonus) }}
                </p>
              </VCardText>
            </VCard>
          </VCol>
        </VRow>

        <!-- Bonus Breakdown -->
        <VCard class="mb-4">
          <VCardTitle class="bg-success-subtle">
            <VIcon
              icon="tabler-gift-card"
              class="me-2"
            />
            Chi Tiết Thưởng Tết
          </VCardTitle>
          <VDivider />
          <VCardText>
            <VRow>
              <VCol
                cols="12"
                md="6"
              >
                <VCard
                  variant="outlined"
                  color="success"
                >
                  <VCardText>
                    <div class="d-flex align-center justify-space-between mb-3">
                      <div class="d-flex align-center">
                        <VIcon
                          icon="tabler-calendar-event"
                          color="success"
                          size="24"
                          class="me-2"
                        />
                        <span class="text-body-1 font-weight-medium">Thưởng Trước Tết</span>
                      </div>
                      <VChip
                        color="success"
                        variant="flat"
                      >
                        Phần 1
                      </VChip>
                    </div>
                    <p class="text-h4 font-weight-bold text-success mb-0">
                      {{ formatCurrency(bonusData.bonus_data.tpnttt) }}
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
                  color="info"
                >
                  <VCardText>
                    <div class="d-flex align-center justify-space-between mb-3">
                      <div class="d-flex align-center">
                        <VIcon
                          icon="tabler-calendar-check"
                          color="info"
                          size="24"
                          class="me-2"
                        />
                        <span class="text-body-1 font-weight-medium">Thưởng Sau Tết</span>
                      </div>
                      <VChip
                        color="info"
                        variant="flat"
                      >
                        Phần 2
                      </VChip>
                    </div>
                    <p class="text-h4 font-weight-bold text-info mb-0">
                      {{ formatCurrency(bonusData.bonus_data.tpntst) }}
                    </p>
                  </VCardText>
                </VCard>
              </VCol>
            </VRow>
          </VCardText>
        </VCard>

        <!-- Detailed Information Table -->
        <VCard>
          <VCardTitle>
            <VIcon
              icon="tabler-info-circle"
              class="me-2"
            />
            Thông Tin Chi Tiết
          </VCardTitle>
          <VDivider />
          <VCardText>
            <VTable density="comfortable">
              <tbody>
                <tr>
                  <td class="font-weight-medium">
                    Tổng Lương Cơ Bản
                  </td>
                  <td class="text-end">
                    {{ formatCurrency(bonusData.bonus_data.tlcb) }}
                  </td>
                </tr>
                <tr>
                  <td class="font-weight-medium">
                    Số Tháng Đóng BHTN
                  </td>
                  <td class="text-end">
                    {{ bonusData.bonus_data.stdltbtn || '0' }} tháng
                  </td>
                </tr>
                <tr>
                  <td class="font-weight-medium">
                    Cấp Bậc
                  </td>
                  <td class="text-end">
                    {{ bonusData.bonus_data.capbac || 'N/A' }}
                  </td>
                </tr>
                <tr>
                  <td class="font-weight-medium">
                    Tỷ Lệ Thưởng
                  </td>
                  <td class="text-end">
                    {{ bonusData.bonus_data.tile || '0' }}%
                  </td>
                </tr>
                <tr class="bg-success-subtle">
                  <td class="font-weight-bold">
                    Tổng Số Tiền Thưởng
                  </td>
                  <td class="text-end font-weight-bold text-success">
                    {{ formatCurrency(totalBonus) }}
                  </td>
                </tr>
                <tr>
                  <td class="font-weight-medium ps-8">
                    • Thưởng Phần NT Trước Tết
                  </td>
                  <td class="text-end text-success">
                    {{ formatCurrency(bonusData.bonus_data.tpnttt) }}
                  </td>
                </tr>
                <tr>
                  <td class="font-weight-medium ps-8">
                    • Thưởng Phần NT Sau Tết
                  </td>
                  <td class="text-end text-info">
                    {{ formatCurrency(bonusData.bonus_data.tpntst) }}
                  </td>
                </tr>
              </tbody>
            </VTable>
          </VCardText>
        </VCard>

        <!-- Total Bonus Summary -->
        <VCard class="mt-4">
          <VCardText>
            <div class="d-flex align-center justify-space-between pa-4 bg-success-subtle rounded">
              <div>
                <p class="text-caption text-medium-emphasis mb-1">
                  TỔNG THƯỞNG TẾT NĂM {{ bonusData.year }}
                </p>
                <p class="text-h3 font-weight-bold text-success mb-0">
                  {{ formatCurrency(totalBonus) }}
                </p>
              </div>
              <VIcon
                icon="tabler-gift"
                size="64"
                color="success"
                class="opacity-50"
              />
            </div>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <!-- No Data State -->
    <VRow v-if="!loading && !bonusData && !error">
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
              Vui lòng nhập Employee ID, chọn năm và nhấn "Tra Cứu"
            </p>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>
  </div>
</template>

<style scoped>
.bg-success-subtle {
  background-color: rgba(var(--v-theme-success), 0.08);
}
</style>
