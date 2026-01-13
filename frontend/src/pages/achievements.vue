<script setup>
import { ref, computed } from 'vue'
import { useGuestProtection } from '@/composables/useGuestProtection'

// Protect from guest users
useGuestProtection()

// State
const loading = ref(false)
const achievementData = ref(null)
const error = ref(null)

// Form input
const employeeId = ref('')

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

// Load achievement data
const loadAchievements = async () => {
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
  achievementData.value = null

  try {
    const response = await $api(`/hrs-data/achievements/${formattedId}`)
    achievementData.value = response
  }
  catch (err) {
    console.error('Failed to load achievements:', err)
    error.value = err.message || 'Không thể tải thông tin thành tích'
    achievementData.value = null
  }
  finally {
    loading.value = false
  }
}

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

// Get score icon
const getScoreIcon = (score) => {
  if (score === '優') return 'tabler-trophy'
  if (score === '良') return 'tabler-medal'
  if (score === '甲') return 'tabler-award'
  if (score === '乙') return 'tabler-star'
  return 'tabler-circle'
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
              🏆 Tra Cứu Thành Tích
            </h2>
            <p class="text-body-1 text-medium-emphasis">
              Tra cứu lịch sử đánh giá thành tích theo Employee ID
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
                md="10"
              >
                <VTextField
                  v-model="employeeId"
                  label="Employee ID"
                  placeholder="VD: 14732 hoặc VNW0014732"
                  variant="outlined"
                  prepend-inner-icon="tabler-id"
                  @keyup.enter="loadAchievements"
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
                  @click="loadAchievements"
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

    <!-- Achievement Data -->
    <VRow v-if="!loading && achievementData">
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
                      {{ achievementData.employee_name || achievementData.employee_id }}
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
                  {{ achievementData.employee_id }}
                </VChip>
              </VCol>
              <VCol
                cols="12"
                md="3"
              >
                <p class="text-caption text-medium-emphasis mb-1">
                  Tổng số năm
                </p>
                <VChip
                  color="success"
                  variant="flat"
                >
                  {{ achievementData.achievements.length }} năm
                </VChip>
              </VCol>
            </VRow>
          </VCardText>
        </VCard>

        <!-- Achievements Timeline -->
        <VCard>
          <VCardTitle>
            <VIcon
              icon="tabler-timeline"
              class="me-2"
            />
            Lịch Sử Đánh Giá Thành Tích
          </VCardTitle>
          <VDivider />
          <VCardText>
            <!-- Achievement Cards Grid -->
            <VRow>
              <VCol
                v-for="achievement in achievementData.achievements"
                :key="achievement.year"
                cols="12"
                sm="6"
                md="4"
                lg="3"
              >
                <VCard
                  :color="getScoreColor(achievement.score)"
                  variant="tonal"
                  class="achievement-card"
                >
                  <VCardText class="text-center pa-6">
                    <VIcon
                      :icon="getScoreIcon(achievement.score)"
                      size="48"
                      class="mb-3"
                    />
                    <p class="text-h6 font-weight-bold mb-1">
                      Năm {{ achievement.year }}
                    </p>
                    <div class="d-flex align-center justify-center gap-2">
                      <VChip
                        :color="getScoreColor(achievement.score)"
                        variant="flat"
                        size="large"
                      >
                        {{ achievement.score }}
                      </VChip>
                      <p class="text-body-2 mb-0">
                        {{ getScoreLabel(achievement.score) }}
                      </p>
                    </div>
                  </VCardText>
                </VCard>
              </VCol>
            </VRow>

            <!-- Achievement Table -->
            <VDivider class="my-6" />

            <VTable>
              <thead>
                <tr>
                  <th class="text-center">
                    STT
                  </th>
                  <th>Năm</th>
                  <th class="text-center">
                    Điểm
                  </th>
                  <th>Đánh Giá</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(achievement, index) in achievementData.achievements"
                  :key="achievement.year"
                >
                  <td class="text-center">
                    {{ index + 1 }}
                  </td>
                  <td>
                    <strong>{{ achievement.year }}</strong>
                  </td>
                  <td class="text-center">
                    <VChip
                      :color="getScoreColor(achievement.score)"
                      variant="flat"
                      size="small"
                    >
                      {{ achievement.score }}
                    </VChip>
                  </td>
                  <td>
                    <div class="d-flex align-center gap-2">
                      <VIcon
                        :icon="getScoreIcon(achievement.score)"
                        :color="getScoreColor(achievement.score)"
                        size="20"
                      />
                      <span class="font-weight-medium">
                        {{ getScoreLabel(achievement.score) }}
                      </span>
                    </div>
                  </td>
                </tr>
              </tbody>
            </VTable>
          </VCardText>
        </VCard>

        <!-- Score Legend -->
        <VCard class="mt-4">
          <VCardTitle>
            <VIcon
              icon="tabler-info-circle"
              class="me-2"
            />
            Thang Điểm Đánh Giá
          </VCardTitle>
          <VDivider />
          <VCardText>
            <VRow>
              <VCol
                cols="6"
                sm="4"
                md="2"
              >
                <div class="text-center">
                  <VChip
                    color="success"
                    variant="flat"
                    class="mb-2"
                  >
                    優
                  </VChip>
                  <p class="text-caption mb-0">
                    Xuất Sắc
                  </p>
                </div>
              </VCol>
              <VCol
                cols="6"
                sm="4"
                md="2"
              >
                <div class="text-center">
                  <VChip
                    color="info"
                    variant="flat"
                    class="mb-2"
                  >
                    良
                  </VChip>
                  <p class="text-caption mb-0">
                    Tốt
                  </p>
                </div>
              </VCol>
              <VCol
                cols="6"
                sm="4"
                md="2"
              >
                <div class="text-center">
                  <VChip
                    color="primary"
                    variant="flat"
                    class="mb-2"
                  >
                    甲
                  </VChip>
                  <p class="text-caption mb-0">
                    Khá
                  </p>
                </div>
              </VCol>
              <VCol
                cols="6"
                sm="4"
                md="2"
              >
                <div class="text-center">
                  <VChip
                    color="warning"
                    variant="flat"
                    class="mb-2"
                  >
                    乙
                  </VChip>
                  <p class="text-caption mb-0">
                    Trung Bình
                  </p>
                </div>
              </VCol>
              <VCol
                cols="6"
                sm="4"
                md="2"
              >
                <div class="text-center">
                  <VChip
                    color="error"
                    variant="flat"
                    class="mb-2"
                  >
                    丙
                  </VChip>
                  <p class="text-caption mb-0">
                    Yếu
                  </p>
                </div>
              </VCol>
            </VRow>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <!-- No Data State -->
    <VRow v-if="!loading && !achievementData && !error">
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
              Vui lòng nhập Employee ID và nhấn "Tra Cứu"
            </p>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>
  </div>
</template>

<style scoped>
.achievement-card {
  transition: transform 0.2s, box-shadow 0.2s;
}

.achievement-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
</style>
