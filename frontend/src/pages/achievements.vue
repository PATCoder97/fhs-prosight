<script setup>
import { ref } from 'vue'
import { useGuestProtection } from '@/composables/useGuestProtection'
import { $api } from '@/utils/api'
import { formatEmployeeId, getScoreColor, getScoreLabel, getScoreIcon } from '@/utils/formatters'
import { silentRequiredValidator } from '@/@core/utils/validators'

// Protect from guest users
useGuestProtection()

// State
const loading = ref(false)
const achievementData = ref(null)

// Toast notification
const toast = ref({
  show: false,
  message: '',
  color: 'error',
})

const showToast = (message, color = 'error') => {
  toast.value = {
    show: true,
    message,
    color,
  }
}

// Form ref
const formRef = ref()

// Form input
const employeeId = ref('')

// Load achievement data
const loadAchievements = async () => {
  // Validate form
  const { valid } = await formRef.value.validate()
  if (!valid) return

  // Auto-format employee ID
  const formattedId = formatEmployeeId(employeeId.value)
  employeeId.value = formattedId

  loading.value = true
  achievementData.value = null

  try {
    const response = await $api(`/hrs-data/achievements/${formattedId}`)
    achievementData.value = response
  }
  catch (err) {
    console.error('Failed to load achievements:', err)
    showToast(err.message || 'Không thể tải thông tin thành tích')
    achievementData.value = null
  }
  finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <!-- Search Form -->
    <VRow>
      <VCol cols="12">
        <VCard>
          <VCardTitle>
            <VIcon
              icon="tabler-trophy"
              class="me-2"
            />
            Tra Cứu Thành Tích
          </VCardTitle>
          <VDivider />
          <VCardText>
            <VForm
              ref="formRef"
              @submit.prevent="loadAchievements"
            >
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
                    :rules="[silentRequiredValidator]"
                    hide-details
                    @keyup.enter="loadAchievements"
                  />
                </VCol>
                <VCol
                  cols="12"
                  md="9"
                  class="d-flex align-end justify-end"
                >
                  <VBtn
                    color="primary"
                    :block="$vuetify.display.smAndDown"
                    :width="$vuetify.display.mdAndUp ? 140 : undefined"
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
            </VForm>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

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
                    color="info"
                    variant="flat"
                    class="mb-2"
                  >
                    良
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
                    color="primary"
                    variant="flat"
                    class="mb-2"
                  >
                    甲
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
                    color="warning"
                    variant="flat"
                    class="mb-2"
                  >
                    乙
                  </VChip>
                  <p class="text-caption mb-0">
                    Yếu
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
                    Kém
                  </p>
                </div>
              </VCol>
            </VRow>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <!-- No Data State -->
    <VRow v-if="!loading && !achievementData">
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

    <!-- Toast Notification -->
    <VSnackbar
      v-model="toast.show"
      :color="toast.color"
      :timeout="3000"
      location="top end"
      transition="slide-x-reverse-transition"
      rounded="lg"
      elevation="8"
      min-width="300"
      max-width="400"
    >
      <div class="d-flex align-center gap-3">
        <VIcon
          :icon="toast.color === 'success' ? 'tabler-circle-check' : toast.color === 'warning' ? 'tabler-alert-triangle' : 'tabler-circle-x'"
          size="24"
        />
        <span>{{ toast.message }}</span>
      </div>
      <template #actions>
        <VBtn
          variant="text"
          icon="tabler-x"
          size="small"
          @click="toast.show = false"
        />
      </template>
    </VSnackbar>
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
