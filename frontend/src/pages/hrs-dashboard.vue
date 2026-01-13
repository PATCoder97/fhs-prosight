<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useGuestProtection } from '@/composables/useGuestProtection'

// Protect from guest users
useGuestProtection()

const router = useRouter()

// State
const loading = ref(false)
const dashboardData = ref({
  salary: null,
  achievements: null,
  yearBonus: null,
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

// Get current date and calculate previous month
const now = new Date()
const currentYear = now.getMonth() === 0 ? now.getFullYear() - 1 : now.getFullYear()
const currentMonth = now.getMonth() === 0 ? 12 : now.getMonth() // Previous month

// Format currency
const formatCurrency = (amount) => {
  if (!amount && amount !== 0) return '0 ₫'
  return new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND',
  }).format(amount)
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

    // Wait for all requests
    const [salary, achievements, yearBonus] = await Promise.all([
      salaryPromise,
      achievementsPromise,
      yearBonusPromise,
    ])

    dashboardData.value = {
      salary,
      achievements,
      yearBonus,
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

// Get score color
const getScoreColor = (score) => {
  if (score === '優') return 'success'
  if (score === '良') return 'info'
  if (score === '甲') return 'primary'
  if (score === '乙') return 'warning'
  if (score === '丙') return 'error'
  return 'grey'
}

// Get score label
const getScoreLabel = (score) => {
  const labels = {
    '優': 'Xuất Sắc',
    '良': 'Tốt',
    '甲': 'Khá',
    '乙': 'Trung Bình',
    '丙': 'Yếu',
  }
  return labels[score] || score
}

// Load data on mount
onMounted(() => {
  loadDashboardData()
})
</script>

<template>
  <div>
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
      <VRow class="mb-4">
        <!-- Current Salary Card -->
        <VCol
          cols="12"
          md="4"
        >
          <VCard
            class="dashboard-card"
            :class="{ 'cursor-pointer': dashboardData.salary }"
            @click="dashboardData.salary ? navigateTo('salary') : null"
          >
            <VCardText>
              <div class="d-flex align-center justify-space-between mb-3">
                <VIcon
                  icon="tabler-currency-dong"
                  size="32"
                  color="success"
                />
                <VBtn
                  icon
                  variant="text"
                  size="small"
                  @click.stop="navigateTo('salary')"
                >
                  <VIcon icon="tabler-arrow-right" />
                </VBtn>
              </div>
              <p class="text-caption text-medium-emphasis mb-1">
                Lương Tháng {{ currentMonth }}/{{ currentYear }}
              </p>
              <p
                v-if="dashboardData.salary"
                class="text-h5 font-weight-bold text-success mb-0"
              >
                {{ formatCurrency(dashboardData.salary.summary.thuc_linh) }}
              </p>
              <p
                v-else
                class="text-body-2 text-medium-emphasis mb-0"
              >
                Chưa có dữ liệu
              </p>
            </VCardText>
          </VCard>
        </VCol>

        <!-- Latest Achievement Card -->
        <VCol
          cols="12"
          md="4"
        >
          <VCard
            class="dashboard-card"
            :class="{ 'cursor-pointer': latestAchievement }"
            @click="latestAchievement ? navigateTo('achievements') : null"
          >
            <VCardText>
              <div class="d-flex align-center justify-space-between mb-3">
                <VIcon
                  icon="tabler-trophy"
                  size="32"
                  :color="latestAchievement ? getScoreColor(latestAchievement.score) : 'grey'"
                />
                <VBtn
                  icon
                  variant="text"
                  size="small"
                  @click.stop="navigateTo('achievements')"
                >
                  <VIcon icon="tabler-arrow-right" />
                </VBtn>
              </div>
              <p class="text-caption text-medium-emphasis mb-1">
                Thành Tích Gần Nhất
              </p>
              <div
                v-if="latestAchievement"
                class="d-flex align-center gap-2"
              >
                <VChip
                  :color="getScoreColor(latestAchievement.score)"
                  variant="flat"
                  size="small"
                >
                  {{ latestAchievement.score }}
                </VChip>
                <span class="text-body-2">{{ getScoreLabel(latestAchievement.score) }}</span>
                <span class="text-caption text-medium-emphasis">({{ latestAchievement.year }})</span>
              </div>
              <p
                v-else
                class="text-body-2 text-medium-emphasis mb-0"
              >
                Chưa có dữ liệu
              </p>
            </VCardText>
          </VCard>
        </VCol>

        <!-- Year Bonus Card -->
        <VCol
          cols="12"
          md="4"
        >
          <VCard
            class="dashboard-card"
            :class="{ 'cursor-pointer': dashboardData.yearBonus }"
            @click="dashboardData.yearBonus ? navigateTo('year-bonus') : null"
          >
            <VCardText>
              <div class="d-flex align-center justify-space-between mb-3">
                <VIcon
                  icon="tabler-gift"
                  size="32"
                  color="warning"
                />
                <VBtn
                  icon
                  variant="text"
                  size="small"
                  @click.stop="navigateTo('year-bonus')"
                >
                  <VIcon icon="tabler-arrow-right" />
                </VBtn>
              </div>
              <p class="text-caption text-medium-emphasis mb-1">
                Thưởng Tết {{ currentYear }}
              </p>
              <p
                v-if="dashboardData.yearBonus"
                class="text-h5 font-weight-bold text-warning mb-0"
              >
                {{ formatCurrency(dashboardData.yearBonus.bonus_data.stienthuong) }}
              </p>
              <p
                v-else
                class="text-body-2 text-medium-emphasis mb-0"
              >
                Chưa có dữ liệu
              </p>
            </VCardText>
          </VCard>
        </VCol>
      </VRow>

      <!-- Detailed Cards Row -->
      <VRow>
        <!-- Salary Details -->
        <VCol
          cols="12"
          md="6"
        >
          <VCard>
            <VCardTitle class="d-flex align-center justify-space-between">
              <div>
                <VIcon
                  icon="tabler-wallet"
                  class="me-2"
                />
                Chi Tiết Lương
              </div>
              <VBtn
                size="small"
                variant="tonal"
                @click="navigateTo('salary')"
              >
                Xem Chi Tiết
                <VIcon
                  end
                  icon="tabler-arrow-right"
                />
              </VBtn>
            </VCardTitle>
            <VDivider />
            <VCardText>
              <div v-if="dashboardData.salary">
                <VRow class="mb-3">
                  <VCol cols="6">
                    <p class="text-caption text-medium-emphasis mb-1">
                      Thu Nhập
                    </p>
                    <p class="text-h6 text-success mb-0">
                      {{ formatCurrency(dashboardData.salary.summary.tong_tien_cong) }}
                    </p>
                  </VCol>
                  <VCol cols="6">
                    <p class="text-caption text-medium-emphasis mb-1">
                      Khấu Trừ
                    </p>
                    <p class="text-h6 text-error mb-0">
                      {{ formatCurrency(dashboardData.salary.summary.tong_tien_tru) }}
                    </p>
                  </VCol>
                </VRow>
                <VDivider class="my-3" />
                <div class="d-flex align-center justify-space-between">
                  <span class="text-body-1 font-weight-medium">Thực Lĩnh</span>
                  <span class="text-h5 font-weight-bold text-primary">
                    {{ formatCurrency(dashboardData.salary.summary.thuc_linh) }}
                  </span>
                </div>
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
                <p class="text-body-2 text-medium-emphasis">
                  Không có dữ liệu lương tháng {{ currentMonth }}/{{ currentYear }}
                </p>
              </div>
            </VCardText>
          </VCard>
        </VCol>

        <!-- Achievements Overview -->
        <VCol
          cols="12"
          md="6"
        >
          <VCard>
            <VCardTitle class="d-flex align-center justify-space-between">
              <div>
                <VIcon
                  icon="tabler-trophy"
                  class="me-2"
                />
                Lịch Sử Thành Tích
              </div>
              <VBtn
                size="small"
                variant="tonal"
                @click="navigateTo('achievements')"
              >
                Xem Chi Tiết
                <VIcon
                  end
                  icon="tabler-arrow-right"
                />
              </VBtn>
            </VCardTitle>
            <VDivider />
            <VCardText>
              <div v-if="dashboardData.achievements?.achievements?.length">
                <VRow>
                  <VCol
                    v-for="achievement in dashboardData.achievements.achievements.slice(0, 4)"
                    :key="achievement.year"
                    cols="6"
                    class="mb-2"
                  >
                    <div class="d-flex align-center gap-2">
                      <VChip
                        :color="getScoreColor(achievement.score)"
                        variant="flat"
                        size="small"
                      >
                        {{ achievement.score }}
                      </VChip>
                      <span class="text-caption">Năm {{ achievement.year }}</span>
                    </div>
                  </VCol>
                </VRow>
                <VBtn
                  v-if="dashboardData.achievements.achievements.length > 4"
                  variant="text"
                  size="small"
                  class="mt-2"
                  @click="navigateTo('achievements')"
                >
                  Xem thêm {{ dashboardData.achievements.achievements.length - 4 }} năm
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
                <p class="text-body-2 text-medium-emphasis">
                  Không có dữ liệu thành tích
                </p>
              </div>
            </VCardText>
          </VCard>
        </VCol>
      </VRow>

      <!-- Quick Actions -->
      <VRow class="mt-4">
        <VCol cols="12">
          <VCard>
            <VCardTitle>
              <VIcon
                icon="tabler-bolt"
                class="me-2"
              />
              Tra Cứu Nhanh
            </VCardTitle>
            <VDivider />
            <VCardText>
              <VRow>
                <VCol
                  cols="12"
                  sm="6"
                  md="3"
                >
                  <VBtn
                    block
                    variant="tonal"
                    color="primary"
                    size="large"
                    @click="navigateTo('salary')"
                  >
                    <VIcon
                      start
                      icon="tabler-currency-dong"
                    />
                    Tra Cứu Lương
                  </VBtn>
                </VCol>
                <VCol
                  cols="12"
                  sm="6"
                  md="3"
                >
                  <VBtn
                    block
                    variant="tonal"
                    color="info"
                    size="large"
                    @click="navigateTo('salary-history')"
                  >
                    <VIcon
                      start
                      icon="tabler-chart-line"
                    />
                    Lịch Sử Lương
                  </VBtn>
                </VCol>
                <VCol
                  cols="12"
                  sm="6"
                  md="3"
                >
                  <VBtn
                    block
                    variant="tonal"
                    color="success"
                    size="large"
                    @click="navigateTo('achievements')"
                  >
                    <VIcon
                      start
                      icon="tabler-trophy"
                    />
                    Thành Tích
                  </VBtn>
                </VCol>
                <VCol
                  cols="12"
                  sm="6"
                  md="3"
                >
                  <VBtn
                    block
                    variant="tonal"
                    color="warning"
                    size="large"
                    @click="navigateTo('year-bonus')"
                  >
                    <VIcon
                      start
                      icon="tabler-gift"
                    />
                    Thưởng Tết
                  </VBtn>
                </VCol>
              </VRow>
            </VCardText>
          </VCard>
        </VCol>
      </VRow>
    </div>
  </div>
</template>

<style scoped>
.dashboard-card {
  transition: transform 0.2s, box-shadow 0.2s;
}

.dashboard-card.cursor-pointer:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  cursor: pointer;
}
</style>
