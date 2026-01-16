<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import { useGuestProtection } from '@/composables/useGuestProtection'
import { $api } from '@/utils/api'
import { formatCurrency, getScoreColor, getScoreLabel } from '@/utils/formatters'

// Check authentication first
// Route guard now handles authentication at router level
// const { isAuthenticated, isLoading: authLoading } = useAuth()

// Protect from guest users
useGuestProtection()

const router = useRouter()

// State
const loading = ref(false)
const dashboardData = ref({
  salary: null,
  achievements: null,
  yearBonus: null,
  evaluations: null,
  dormitoryBills: null,
})
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

// Get current date and calculate previous month for salary
const now = new Date()
const currentYear = now.getMonth() === 0 ? now.getFullYear() - 1 : now.getFullYear()
const currentMonth = now.getMonth() === 0 ? 12 : now.getMonth() // now.getMonth() is 0-indexed, so it's already -1

// Get current term code (261 for January 2026)
const currentTermCode = computed(() => {
  const year = new Date().getFullYear()
  const month = new Date().getMonth() + 1
  const shortYear = year.toString().slice(-2)

  // Months 1-9: use number (261, 262, ..., 259)
  // Months 10-12: use letter (26A, 26B, 26C)
  if (month >= 10) {
    const endOfYearTerms = ['A', 'B', 'C']
    return `${shortYear}${endOfYearTerms[month - 10]}`
  }

  return `${shortYear}${month}`
})

// Sort term codes: 25 > 25C > 25B > 25A > 259 > 258 > ... > 251 > 24 > 24C > ...
const sortTermCodes = (a, b) => {
  // Extract year (first 2 digits)
  const extractYear = (term) => {
    const match = term.match(/^(\d{2})/)
    return match ? parseInt(match[1]) : 0
  }

  // Extract suffix (everything after year)
  // "25" -> "", "25A" -> "A", "251" -> "1"
  const extractSuffix = (term) => {
    const match = term.match(/^\d{2}(.*)/)
    return match ? match[1] : ''
  }

  const yearA = extractYear(a)
  const yearB = extractYear(b)

  // Different years: sort by year descending (newer first)
  if (yearA !== yearB) {
    return yearB - yearA
  }

  // Same year: sort by suffix
  const suffixA = extractSuffix(a)
  const suffixB = extractSuffix(b)

  // No suffix (e.g., "25") means year-end summary - comes first
  if (!suffixA && !suffixB) return 0
  if (!suffixA) return -1 // "25" comes before everything
  if (!suffixB) return 1

  // Both have suffixes - check if they are letters (A/B/C) or numbers (1-9)
  const isLetterA = /^[A-Z]$/.test(suffixA)
  const isLetterB = /^[A-Z]$/.test(suffixB)

  // Letters (A/B/C for Oct/Nov/Dec) come before numbers (1-9 for Jan-Sep)
  if (isLetterA && !isLetterB) return -1
  if (!isLetterA && isLetterB) return 1

  if (isLetterA && isLetterB) {
    // Both letters: C > B > A
    return suffixB.localeCompare(suffixA)
  }

  // Both numbers: 9 > 8 > ... > 1
  return parseInt(suffixB) - parseInt(suffixA)
}

// Load dashboard data
const loadDashboardData = async () => {
  if (!currentUser.value || !currentUser.value.localId) {
    error.value = 'Không tìm thấy Employee ID của bạn'
    return
  }

  loading.value = true
  error.value = null

  try {
    // Load current month salary
    const salaryPromise = $api(
      `/hrs-data/salary/${currentUser.value.localId}?year=${currentYear}&month=${currentMonth}`
    ).catch(() => null)

    // Load achievements
    const achievementsPromise = $api(
      `/hrs-data/achievements/${currentUser.value.localId}`
    ).catch(() => null)

    // Load current year bonus
    const yearBonusPromise = $api(
      `/hrs-data/year-bonus/${currentUser.value.localId}/${currentYear}`
    ).catch(() => null)

    // Load evaluations for current employee
    const evaluationsPromise = $api(
      `/evaluations/search?employee_id=${currentUser.value.localId}&page=1&page_size=5`
    ).catch(() => null)

    // Load dormitory bills for current employee (latest term)
    const dormitoryBillsPromise = $api(
      `/dormitory-bills/search?employee_id=${currentUser.value.localId}&page=1&page_size=5`
    ).catch(() => null)

    // Wait for all requests
    const [salary, achievements, yearBonus, evaluations, dormitoryBills] = await Promise.all([
      salaryPromise,
      achievementsPromise,
      yearBonusPromise,
      evaluationsPromise,
      dormitoryBillsPromise,
    ])

    // Sort evaluations by term_code
    if (evaluations?.results) {
      evaluations.results.sort((a, b) => sortTermCodes(a.term_code, b.term_code))
    }

    dashboardData.value = {
      salary,
      achievements,
      yearBonus,
      evaluations,
      dormitoryBills,
    }
  }
  catch (err) {
    console.error('Failed to load dashboard data:', err)
    error.value = 'Không thể tải dữ liệu dashboard'
  }
  finally {
    loading.value = false
  }
}

// Navigate to detail page
const navigateTo = (pageName) => {
  router.push({ name: pageName })
}

// Get latest achievement
const latestAchievement = computed(() => {
  if (!dashboardData.value.achievements?.achievements?.length) return null
  return dashboardData.value.achievements.achievements[0]
})

// Get latest evaluation
const latestEvaluation = computed(() => {
  if (!dashboardData.value.evaluations?.results?.length) return null
  return dashboardData.value.evaluations.results[0]
})

// Get latest dormitory bill
const latestDormitoryBill = computed(() => {
  if (!dashboardData.value.dormitoryBills?.results?.length) return null
  return dashboardData.value.dormitoryBills.results[0]
})

// Load data on mount
onMounted(() => {
  loadDashboardData()
})
</script>

<template>
  <div>
    <!-- Welcome Header -->
    <VCard class="mb-6 welcome-card">
      <VCardText>
        <VRow align="center">
          <VCol
            cols="12"
            md="8"
          >
            <div class="d-flex align-center gap-3">
              <VAvatar
                color="primary"
                size="64"
              >
                <VIcon
                  icon="tabler-user"
                  size="32"
                />
              </VAvatar>
              <div>
                <h4 class="text-h4 font-weight-bold mb-1">
                  Xin chào, {{ currentUser?.full_name || 'User' }}! 👋
                </h4>
                <p class="text-body-1 text-medium-emphasis mb-0">
                  {{ currentUser?.localId }} - {{ currentUser?.email }}
                </p>
              </div>
            </div>
          </VCol>
          <VCol
            cols="12"
            md="4"
            class="text-md-end"
          >
            <VChip
              color="primary"
              variant="tonal"
              size="large"
            >
              <VIcon
                start
                icon="tabler-calendar"
              />
              Kỳ {{ currentTermCode }}
            </VChip>
          </VCol>
        </VRow>
      </VCardText>
    </VCard>

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

    <!-- Dashboard Content -->
    <div v-if="!loading">
      <!-- Quick Stats Row -->
      <VRow class="mb-6">
        <!-- Current Salary Card -->
        <VCol
          cols="12"
          sm="6"
          md="4"
          lg="2-4"
        >
          <VCard
            class="stat-card"
            color="success"
            variant="tonal"
          >
            <VCardText>
              <div class="d-flex align-center justify-space-between mb-3">
                <VAvatar
                  color="success"
                  size="48"
                  variant="tonal"
                >
                  <VIcon
                    icon="tabler-currency-dong"
                    size="24"
                  />
                </VAvatar>
                <VBtn
                  icon
                  variant="text"
                  size="small"
                  @click="navigateTo('salary')"
                >
                  <VIcon icon="tabler-arrow-right" />
                </VBtn>
              </div>
              <p class="text-caption mb-1">
                Lương Tháng {{ currentMonth }}/{{ currentYear }}
              </p>
              <p
                v-if="dashboardData.salary"
                class="text-h5 font-weight-bold mb-0"
              >
                {{ formatCurrency(dashboardData.salary.summary.thuc_linh) }}
              </p>
              <p
                v-else
                class="text-body-2 mb-0"
              >
                Chưa có dữ liệu
              </p>
            </VCardText>
          </VCard>
        </VCol>

        <!-- Latest Achievement Card -->
        <VCol
          cols="12"
          sm="6"
          md="4"
          lg="2-4"
        >
          <VCard
            class="stat-card"
            color="info"
            variant="tonal"
          >
            <VCardText>
              <div class="d-flex align-center justify-space-between mb-3">
                <VAvatar
                  :color="latestAchievement ? getScoreColor(latestAchievement.score) : 'grey'"
                  size="48"
                  variant="tonal"
                >
                  <VIcon
                    icon="tabler-trophy"
                    size="24"
                  />
                </VAvatar>
                <VBtn
                  icon
                  variant="text"
                  size="small"
                  @click="navigateTo('achievements')"
                >
                  <VIcon icon="tabler-arrow-right" />
                </VBtn>
              </div>
              <p class="text-caption mb-1">
                Thành Tích Gần Nhất
              </p>
              <div
                v-if="latestAchievement"
                class="d-flex align-center gap-2"
              >
                <VChip
                  :color="getScoreColor(latestAchievement.score)"
                  size="small"
                >
                  {{ latestAchievement.score }}
                </VChip>
                <span class="text-body-2 font-weight-medium">{{ getScoreLabel(latestAchievement.score) }}</span>
              </div>
              <p
                v-else
                class="text-body-2 mb-0"
              >
                Chưa có dữ liệu
              </p>
            </VCardText>
          </VCard>
        </VCol>

        <!-- Year Bonus Card -->
        <VCol
          cols="12"
          sm="6"
          md="4"
          lg="2-4"
        >
          <VCard
            class="stat-card"
            color="warning"
            variant="tonal"
          >
            <VCardText>
              <div class="d-flex align-center justify-space-between mb-3">
                <VAvatar
                  color="warning"
                  size="48"
                  variant="tonal"
                >
                  <VIcon
                    icon="tabler-gift"
                    size="24"
                  />
                </VAvatar>
                <VBtn
                  icon
                  variant="text"
                  size="small"
                  @click="navigateTo('year-bonus')"
                >
                  <VIcon icon="tabler-arrow-right" />
                </VBtn>
              </div>
              <p class="text-caption mb-1">
                Thưởng Tết {{ currentYear }}
              </p>
              <p
                v-if="dashboardData.yearBonus"
                class="text-h5 font-weight-bold mb-0"
              >
                {{ formatCurrency(dashboardData.yearBonus.bonus_data.stienthuong) }}
              </p>
              <p
                v-else
                class="text-body-2 mb-0"
              >
                Chưa có dữ liệu
              </p>
            </VCardText>
          </VCard>
        </VCol>

        <!-- Latest Evaluation Card -->
        <VCol
          cols="12"
          sm="6"
          md="4"
          lg="2-4"
        >
          <VCard
            class="stat-card"
            color="primary"
            variant="tonal"
          >
            <VCardText>
              <div class="d-flex align-center justify-space-between mb-3">
                <VAvatar
                  :color="latestEvaluation ? getScoreColor(latestEvaluation.mgr_evaluation?.final?.score) : 'grey'"
                  size="48"
                  variant="tonal"
                >
                  <VIcon
                    icon="tabler-chart-bar"
                    size="24"
                  />
                </VAvatar>
                <VBtn
                  icon
                  variant="text"
                  size="small"
                  @click="navigateTo('evaluations')"
                >
                  <VIcon icon="tabler-arrow-right" />
                </VBtn>
              </div>
              <p class="text-caption mb-1">
                Đánh Giá Gần Nhất
              </p>
              <div
                v-if="latestEvaluation"
                class="d-flex align-center gap-2"
              >
                <VChip
                  :color="getScoreColor(latestEvaluation.mgr_evaluation?.final?.score)"
                  size="small"
                >
                  {{ latestEvaluation.mgr_evaluation?.final?.score || 'N/A' }}
                </VChip>
                <span class="text-caption">Kỳ {{ latestEvaluation.term_code }}</span>
              </div>
              <p
                v-else
                class="text-body-2 mb-0"
              >
                Chưa có dữ liệu
              </p>
            </VCardText>
          </VCard>
        </VCol>

        <!-- Latest Dormitory Bill Card -->
        <VCol
          cols="12"
          sm="6"
          md="4"
          lg="2-4"
        >
          <VCard
            class="stat-card"
            color="secondary"
            variant="tonal"
          >
            <VCardText>
              <div class="d-flex align-center justify-space-between mb-3">
                <VAvatar
                  color="secondary"
                  size="48"
                  variant="tonal"
                >
                  <VIcon
                    icon="tabler-home-dollar"
                    size="24"
                  />
                </VAvatar>
                <VBtn
                  icon
                  variant="text"
                  size="small"
                  @click="navigateTo('dormitory-bills')"
                >
                  <VIcon icon="tabler-arrow-right" />
                </VBtn>
              </div>
              <p class="text-caption mb-1">
                Hóa Đơn KTX Gần Nhất
              </p>
              <div
                v-if="latestDormitoryBill"
                class="d-flex align-center gap-2"
              >
                <VChip
                  color="success"
                  size="small"
                  variant="tonal"
                >
                  {{ formatCurrency(latestDormitoryBill.total_amount) }}
                </VChip>
                <span class="text-caption">{{ latestDormitoryBill.term_code }}</span>
              </div>
              <p
                v-else
                class="text-body-2 mb-0"
              >
                Chưa có dữ liệu
              </p>
            </VCardText>
          </VCard>
        </VCol>
      </VRow>

      <!-- Main Content Row -->
      <VRow>
        <!-- Evaluations Card -->
        <VCol cols="12">
          <VCard>
            <VCardTitle class="d-flex align-center justify-space-between">
              <div class="d-flex align-center gap-2">
                <VIcon
                  icon="tabler-chart-bar"
                  size="24"
                />
                <span>Lịch Sử Đánh Giá</span>
              </div>
              <VBtn
                size="small"
                variant="tonal"
                color="primary"
                @click="navigateTo('evaluations')"
              >
                Xem Tất Cả
                <VIcon
                  end
                  icon="tabler-arrow-right"
                />
              </VBtn>
            </VCardTitle>
            <VDivider />
            <VCardText>
              <div v-if="dashboardData.evaluations?.results?.length">
                <VTable>
                  <thead>
                    <tr>
                      <th>Kỳ</th>
                      <th>Phòng Ban</th>
                      <th class="text-center">
                        Đánh Giá PB
                      </th>
                      <th class="text-center">
                        Đánh Giá QL
                      </th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="evaluation in dashboardData.evaluations.results"
                      :key="evaluation.id"
                    >
                      <td>
                        <VChip
                          color="primary"
                          variant="tonal"
                          size="small"
                        >
                          {{ evaluation.term_code }}
                        </VChip>
                      </td>
                      <td>
                        <div class="text-caption text-medium-emphasis">
                          {{ evaluation.dept_code }}
                        </div>
                        <div
                          class="text-body-2"
                          style="max-width: 250px;"
                        >
                          {{ evaluation.dept_name }}
                        </div>
                      </td>
                      <td class="text-center">
                        <VChip
                          :color="getScoreColor(evaluation.dept_evaluation?.final?.score)"
                          size="small"
                        >
                          {{ evaluation.dept_evaluation?.final?.score || 'N/A' }}
                        </VChip>
                      </td>
                      <td class="text-center">
                        <VChip
                          :color="getScoreColor(evaluation.mgr_evaluation?.final?.score)"
                          size="small"
                        >
                          {{ evaluation.mgr_evaluation?.final?.score || 'N/A' }}
                        </VChip>
                      </td>
                      <td class="text-center">
                        <VBtn
                          icon
                          variant="text"
                          size="small"
                          @click="navigateTo('evaluations')"
                        >
                          <VIcon icon="tabler-eye" />
                        </VBtn>
                      </td>
                    </tr>
                  </tbody>
                </VTable>
              </div>
              <div
                v-else
                class="text-center py-12"
              >
                <VIcon
                  icon="tabler-chart-bar-off"
                  size="64"
                  color="grey-lighten-1"
                  class="mb-3"
                />
                <p class="text-body-1 text-medium-emphasis">
                  Chưa có dữ liệu đánh giá
                </p>
                <VBtn
                  variant="tonal"
                  color="primary"
                  class="mt-2"
                  @click="navigateTo('evaluations')"
                >
                  <VIcon
                    start
                    icon="tabler-search"
                  />
                  Tìm Kiếm Đánh Giá
                </VBtn>
              </div>
            </VCardText>
          </VCard>
        </VCol>
      </VRow>

      <!-- Dormitory Bills Row -->
      <VRow>
        <VCol cols="12">
          <VCard>
            <VCardTitle class="d-flex align-center justify-space-between">
              <div class="d-flex align-center gap-2">
                <VIcon
                  icon="tabler-home-dollar"
                  size="24"
                />
                <span>Hóa Đơn KTX</span>
              </div>
              <VBtn
                size="small"
                variant="tonal"
                color="primary"
                @click="navigateTo('dormitory-bills')"
              >
                Xem Tất Cả
                <VIcon
                  end
                  icon="tabler-arrow-right"
                />
              </VBtn>
            </VCardTitle>
            <VDivider />
            <VCardText>
              <div v-if="dashboardData.dormitoryBills?.results?.length">
                <VTable>
                  <thead>
                    <tr>
                      <th>Kỳ</th>
                      <th>Phòng</th>
                      <th class="text-end">
                        Điện
                      </th>
                      <th class="text-end">
                        Nước
                      </th>
                      <th class="text-end">
                        Tổng
                      </th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="bill in dashboardData.dormitoryBills.results"
                      :key="bill.bill_id"
                    >
                      <td>
                        <VChip
                          color="info"
                          variant="tonal"
                          size="small"
                        >
                          {{ bill.term_code }}
                        </VChip>
                      </td>
                      <td>
                        <div class="text-body-2">
                          {{ bill.dorm_code }}
                        </div>
                        <div class="text-caption text-medium-emphasis">
                          {{ bill.factory_location }}
                        </div>
                      </td>
                      <td class="text-end">
                        <div class="text-body-2">
                          {{ formatCurrency(bill.elec_amount) }}
                        </div>
                        <div class="text-caption text-medium-emphasis">
                          {{ bill.elec_usage?.toFixed(1) }} kWh
                        </div>
                      </td>
                      <td class="text-end">
                        <div class="text-body-2">
                          {{ formatCurrency(bill.water_amount) }}
                        </div>
                        <div class="text-caption text-medium-emphasis">
                          {{ bill.water_usage?.toFixed(1) }} m³
                        </div>
                      </td>
                      <td class="text-end">
                        <VChip
                          color="success"
                          variant="tonal"
                          size="small"
                        >
                          {{ formatCurrency(bill.total_amount) }}
                        </VChip>
                      </td>
                      <td class="text-center">
                        <VBtn
                          icon
                          variant="text"
                          size="small"
                          @click="navigateTo('dormitory-bills')"
                        >
                          <VIcon icon="tabler-eye" />
                        </VBtn>
                      </td>
                    </tr>
                  </tbody>
                </VTable>
              </div>
              <div
                v-else
                class="text-center py-12"
              >
                <VIcon
                  icon="tabler-home-off"
                  size="64"
                  color="grey-lighten-1"
                  class="mb-3"
                />
                <p class="text-body-1 text-medium-emphasis">
                  Chưa có dữ liệu hóa đơn KTX
                </p>
                <VBtn
                  variant="tonal"
                  color="primary"
                  class="mt-2"
                  @click="navigateTo('dormitory-bills')"
                >
                  <VIcon
                    start
                    icon="tabler-search"
                  />
                  Tra Cứu Hóa Đơn
                </VBtn>
              </div>
            </VCardText>
          </VCard>
        </VCol>
      </VRow>

      <!-- Sidebar Row -->
      <VRow>
        <!-- Salary Details -->
        <VCol
          cols="12"
          md="6"
        >
          <VCard class="h-100">
            <VCardTitle class="d-flex align-center justify-space-between">
              <div class="d-flex align-center gap-2">
                <VIcon
                  icon="tabler-wallet"
                  size="20"
                />
                <span>Chi Tiết Lương</span>
              </div>
            </VCardTitle>
            <VDivider />
            <VCardText>
              <div v-if="dashboardData.salary">
                <div class="mb-4">
                  <div class="d-flex align-center justify-space-between mb-2">
                    <span class="text-caption text-medium-emphasis">Thu Nhập</span>
                    <span class="text-body-1 font-weight-medium text-success">
                      {{ formatCurrency(dashboardData.salary.summary.tong_tien_cong) }}
                    </span>
                  </div>
                  <div class="d-flex align-center justify-space-between">
                    <span class="text-caption text-medium-emphasis">Khấu Trừ</span>
                    <span class="text-body-1 font-weight-medium text-error">
                      {{ formatCurrency(dashboardData.salary.summary.tong_tien_tru) }}
                    </span>
                  </div>
                </div>
                <VDivider class="my-3" />
                <div class="d-flex align-center justify-space-between">
                  <span class="text-body-1 font-weight-bold">Thực Lĩnh</span>
                  <span class="text-h6 font-weight-bold text-primary">
                    {{ formatCurrency(dashboardData.salary.summary.thuc_linh) }}
                  </span>
                </div>
                <VBtn
                  block
                  variant="tonal"
                  color="success"
                  class="mt-4"
                  @click="navigateTo('salary')"
                >
                  Xem Chi Tiết
                  <VIcon
                    end
                    icon="tabler-arrow-right"
                  />
                </VBtn>
              </div>
              <div
                v-else
                class="text-center py-8"
              >
                <VIcon
                  icon="tabler-alert-circle"
                  size="48"
                  color="grey-lighten-1"
                  class="mb-2"
                />
                <p class="text-body-2 text-medium-emphasis mb-3">
                  Không có dữ liệu lương<br>tháng {{ currentMonth }}/{{ currentYear }}
                </p>
                <VBtn
                  variant="tonal"
                  size="small"
                  @click="navigateTo('salary')"
                >
                  Tra Cứu Lương
                </VBtn>
              </div>
            </VCardText>
          </VCard>
        </VCol>

        <!-- Achievements Overview -->
        <VCol
          cols="12"
          md="6"
        >
          <VCard class="h-100">
            <VCardTitle class="d-flex align-center justify-space-between">
              <div class="d-flex align-center gap-2">
                <VIcon
                  icon="tabler-trophy"
                  size="20"
                />
                <span>Thành Tích</span>
              </div>
            </VCardTitle>
            <VDivider />
            <VCardText>
              <div v-if="dashboardData.achievements?.achievements?.length">
                <div
                  v-for="achievement in dashboardData.achievements.achievements.slice(0, 5)"
                  :key="achievement.year"
                  class="d-flex align-center justify-space-between mb-3"
                >
                  <span class="text-body-2">Năm {{ achievement.year }}</span>
                  <VChip
                    :color="getScoreColor(achievement.score)"
                    size="small"
                  >
                    {{ achievement.score }}
                  </VChip>
                </div>
                <VBtn
                  block
                  variant="tonal"
                  color="info"
                  class="mt-2"
                  @click="navigateTo('achievements')"
                >
                  Xem Tất Cả
                  <VIcon
                    end
                    icon="tabler-arrow-right"
                  />
                </VBtn>
              </div>
              <div
                v-else
                class="text-center py-8"
              >
                <VIcon
                  icon="tabler-trophy-off"
                  size="48"
                  color="grey-lighten-1"
                  class="mb-2"
                />
                <p class="text-body-2 text-medium-emphasis mb-3">
                  Không có dữ liệu thành tích
                </p>
                <VBtn
                  variant="tonal"
                  size="small"
                  @click="navigateTo('achievements')"
                >
                  Xem Thành Tích
                </VBtn>
              </div>
            </VCardText>
          </VCard>
        </VCol>
      </VRow>
    </div>
  </div>
</template>

<style scoped>
.welcome-card {
  background: linear-gradient(135deg, rgb(var(--v-theme-primary)) 0%, rgb(var(--v-theme-primary-darken-1)) 100%);
  color: white;
}

.welcome-card :deep(*) {
  color: white !important;
}

.stat-card {
  transition: transform 0.2s, box-shadow 0.2s;
  height: 100%;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

/* Custom 5-column layout for large screens */
@media (min-width: 1280px) {
  .v-col-lg-2-4 {
    flex: 0 0 20%;
    max-width: 20%;
  }
}
</style>
