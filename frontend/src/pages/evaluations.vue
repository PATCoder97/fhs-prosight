<script setup>
import { ref, computed, onMounted } from 'vue'
import { $api } from '@/utils/api'

// State
const loading = ref(false)
const evaluations = ref([])
const total = ref(0)

// Search filters
const searchEmployeeId = ref('')
const searchTermCode = ref('')
const searchDeptCode = ref('')

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

// Pagination
const page = ref(1)
const pageSize = ref(10)
const pageSizeOptions = [
  { value: 10, title: '10' },
  { value: 25, title: '25' },
  { value: 50, title: '50' },
]

// Toast notification
const toast = ref({
  show: false,
  message: '',
  color: 'success',
})

const showToast = (message, color = 'success') => {
  toast.value = {
    show: true,
    message,
    color,
  }
}

// Search evaluations
const searchEvaluations = async (resetPage = false) => {
  if (resetPage) {
    page.value = 1
  }

  loading.value = true

  try {
    const params = new URLSearchParams()

    if (searchEmployeeId.value.trim()) {
      // Format employee ID before sending to API
      const formattedId = formatEmployeeId(searchEmployeeId.value.trim())
      // Update input with formatted value
      searchEmployeeId.value = formattedId
      params.append('employee_id', formattedId)
    }
    if (searchTermCode.value.trim()) {
      params.append('term_code', searchTermCode.value.trim())
    }
    if (searchDeptCode.value.trim()) {
      params.append('dept_code', searchDeptCode.value.trim())
    }

    params.append('page', page.value.toString())
    params.append('page_size', pageSize.value.toString())

    const queryString = params.toString()
    const response = await $api(`/evaluations/search?${queryString}`)

    evaluations.value = response.results || []
    total.value = response.total || 0
  }
  catch (err) {
    console.error('Failed to search evaluations:', err)
    showToast('Không thể tìm kiếm đánh giá!', 'error')
    evaluations.value = []
    total.value = 0
  }
  finally {
    loading.value = false
  }
}

// Handle page change
const onPageChange = (newPage) => {
  page.value = newPage
  searchEvaluations()
}

// Handle page size change
const onPageSizeChange = () => {
  page.value = 1
  if (evaluations.value.length > 0) {
    searchEvaluations()
  }
}

// Total pages
const totalPages = computed(() => {
  if (total.value === 0) return 1
  return Math.ceil(total.value / pageSize.value)
})

// Get score color
const getScoreColor = (score) => {
  if (!score) return 'default'
  switch (score) {
    case '優': return 'success'    // Tốt - Xanh lá
    case '良': return 'info'       // Khá - Xanh dương
    case '甲':                     // Trung Bình - Primary
    case '甲上':                   // Trung Bình Trên - Primary
    case '甲下':                   // Trung Bình Dưới - Primary
      return 'primary'
    case '乙': return 'warning'    // Yếu - Vàng
    case '丙': return 'error'      // Kém - Đỏ
    default: return 'default'
  }
}

// Evaluation detail dialog
const detailDialog = ref(false)
const selectedEvaluation = ref(null)

const viewDetail = (evaluation) => {
  selectedEvaluation.value = evaluation
  detailDialog.value = true
}

const closeDetail = () => {
  detailDialog.value = false
  selectedEvaluation.value = null
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
              icon="tabler-chart-bar"
              class="me-2"
            />
            Tìm Kiếm Đánh Giá
          </VCardTitle>
          <VDivider />
          <VCardText>
            <VRow>
              <VCol
                cols="12"
                md="3"
              >
                <VTextField
                  v-model="searchEmployeeId"
                  label="Mã nhân viên"
                  placeholder="VD: 14732 hoặc VNW0014732"
                  variant="outlined"
                  prepend-inner-icon="tabler-id"
                  clearable
                  @keyup.enter="searchEvaluations(true)"
                />
              </VCol>
              <VCol
                cols="12"
                md="3"
              >
                <VTextField
                  v-model="searchTermCode"
                  label="Kỳ đánh giá"
                  placeholder="VD: 25B"
                  variant="outlined"
                  prepend-inner-icon="tabler-calendar"
                  clearable
                  @keyup.enter="searchEvaluations(true)"
                />
              </VCol>
              <VCol
                cols="12"
                md="3"
              >
                <VTextField
                  v-model="searchDeptCode"
                  label="Mã phòng ban"
                  placeholder="VD: 78"
                  variant="outlined"
                  prepend-inner-icon="tabler-building"
                  clearable
                  @keyup.enter="searchEvaluations(true)"
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
                  :loading="loading"
                  @click="searchEvaluations(true)"
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
      v-if="!loading && evaluations.length > 0"
      class="mt-4"
    >
      <VCol cols="12">
        <VCard>
          <VCardTitle class="d-flex align-center justify-space-between">
            <div>
              <VIcon
                icon="tabler-list"
                class="me-2"
              />
              Kết Quả
            </div>
            <VChip
              color="primary"
              variant="tonal"
            >
              {{ total }} kết quả
            </VChip>
          </VCardTitle>
          <VDivider />
          <VCardText class="pa-0">
            <VTable>
              <thead>
                <tr>
                  <th class="text-left">
                    Kỳ đánh giá
                  </th>
                  <th class="text-left">
                    Mã NV
                  </th>
                  <th class="text-left">
                    Tên nhân viên
                  </th>
                  <th class="text-left">
                    Phòng ban
                  </th>
                  <th class="text-left">
                    Chức vụ
                  </th>
                  <th class="text-center">
                    Đánh giá PB
                  </th>
                  <th class="text-center">
                    Đánh giá QL
                  </th>
                  <th class="text-center">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="evaluation in evaluations"
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
                    {{ evaluation.employee_id }}
                  </td>
                  <td>
                    <span class="font-weight-medium">{{ evaluation.employee_name }}</span>
                  </td>
                  <td>
                    <div
                      class="text-truncate"
                      style="max-width: 250px;"
                      :title="evaluation.dept_name"
                    >
                      <span class="text-caption text-medium-emphasis">{{ evaluation.dept_code }}</span>
                      <br>
                      {{ evaluation.dept_name }}
                    </div>
                  </td>
                  <td>
                    <div
                      class="text-truncate"
                      style="max-width: 200px;"
                      :title="evaluation.grade_name"
                    >
                      {{ evaluation.grade_name || 'N/A' }}
                    </div>
                  </td>
                  <td class="text-center">
                    <span
                      class="score-badge"
                      :style="{ color: `rgb(var(--v-theme-${getScoreColor(evaluation.dept_evaluation?.final?.score)}))` }"
                    >
                      {{ evaluation.dept_evaluation?.final?.score || 'N/A' }}
                    </span>
                  </td>
                  <td class="text-center">
                    <span
                      class="score-badge"
                      :style="{ color: `rgb(var(--v-theme-${getScoreColor(evaluation.mgr_evaluation?.final?.score)}))` }"
                    >
                      {{ evaluation.mgr_evaluation?.final?.score || 'N/A' }}
                    </span>
                  </td>
                  <td class="text-center">
                    <VBtn
                      icon
                      variant="text"
                      size="small"
                      @click="viewDetail(evaluation)"
                    >
                      <VIcon icon="tabler-eye" />
                    </VBtn>
                  </td>
                </tr>
              </tbody>
            </VTable>
          </VCardText>

          <!-- Pagination -->
          <VDivider />
          <VCardText class="d-flex align-center justify-space-between flex-wrap gap-4">
            <div class="d-flex align-center gap-3">
              <div class="text-body-2 text-medium-emphasis">
                Hiển thị {{ total === 0 ? 0 : ((page - 1) * pageSize) + 1 }} - {{ Math.min(((page - 1) * pageSize) + evaluations.length, total) }} trong tổng số {{ total }} kết quả
              </div>
              <VSelect
                v-model="pageSize"
                :items="pageSizeOptions"
                variant="outlined"
                density="compact"
                hide-details
                style="max-width: 100px;"
                @update:model-value="onPageSizeChange"
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
      v-if="!loading && evaluations.length === 0 && (searchEmployeeId || searchTermCode || searchDeptCode)"
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
              Thử thay đổi các tiêu chí tìm kiếm
            </p>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <!-- Initial State -->
    <VRow
      v-if="!loading && evaluations.length === 0 && !searchEmployeeId && !searchTermCode && !searchDeptCode"
      class="mt-4"
    >
      <VCol cols="12">
        <VCard>
          <VCardText class="text-center py-16">
            <VIcon
              icon="tabler-chart-bar"
              size="64"
              color="grey-lighten-1"
              class="mb-4"
            />
            <p class="text-h6 text-medium-emphasis mb-2">
              Tìm kiếm đánh giá
            </p>
            <p class="text-body-2 text-medium-emphasis">
              Nhập điều kiện tìm kiếm để xem kết quả đánh giá
            </p>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <!-- Detail Dialog -->
    <VDialog
      v-model="detailDialog"
      max-width="800"
    >
      <VCard v-if="selectedEvaluation">
        <VCardTitle class="d-flex align-center justify-space-between">
          <div>
            <VIcon
              icon="tabler-file-text"
              class="me-2"
            />
            Chi Tiết Đánh Giá
          </div>
          <VBtn
            icon
            variant="text"
            @click="closeDetail"
          >
            <VIcon icon="tabler-x" />
          </VBtn>
        </VCardTitle>
        <VDivider />
        <VCardText>
          <!-- Basic Info -->
          <div class="mb-6">
            <h6 class="text-h6 mb-4">
              Thông tin chung
            </h6>
            <VRow>
              <VCol
                cols="6"
                md="4"
              >
                <div class="text-caption text-medium-emphasis">
                  Kỳ đánh giá
                </div>
                <div class="font-weight-medium">
                  {{ selectedEvaluation.term_code }}
                </div>
              </VCol>
              <VCol
                cols="6"
                md="4"
              >
                <div class="text-caption text-medium-emphasis">
                  Mã nhân viên
                </div>
                <div class="font-weight-medium">
                  {{ selectedEvaluation.employee_id }}
                </div>
              </VCol>
              <VCol
                cols="12"
                md="4"
              >
                <div class="text-caption text-medium-emphasis">
                  Tên nhân viên
                </div>
                <div class="font-weight-medium">
                  {{ selectedEvaluation.employee_name }}
                </div>
              </VCol>
              <VCol
                cols="12"
                md="6"
              >
                <div class="text-caption text-medium-emphasis">
                  Phòng ban
                </div>
                <div class="font-weight-medium">
                  {{ selectedEvaluation.dept_name }}
                </div>
              </VCol>
              <VCol
                cols="12"
                md="6"
              >
                <div class="text-caption text-medium-emphasis">
                  Chức vụ
                </div>
                <div class="font-weight-medium">
                  {{ selectedEvaluation.grade_name || 'N/A' }}
                </div>
              </VCol>
              <VCol cols="12">
                <div class="text-caption text-medium-emphasis">
                  Cấp bậc
                </div>
                <div class="font-weight-medium">
                  {{ selectedEvaluation.job_level || 'N/A' }}
                </div>
              </VCol>
            </VRow>
          </div>

          <VDivider class="my-6" />

          <!-- Department Evaluation -->
          <div class="mb-6">
            <h6 class="text-h6 mb-4">
              Đánh giá phòng ban
            </h6>
            <VRow>
              <VCol
                cols="12"
                md="4"
              >
                <VCard
                  variant="tonal"
                  class="evaluation-card"
                >
                  <VCardText>
                    <div class="text-caption text-medium-emphasis mb-2">
                      Đánh giá ban đầu
                    </div>
                    <VChip
                      :color="getScoreColor(selectedEvaluation.dept_evaluation?.init?.score)"
                      class="mb-2"
                    >
                      {{ selectedEvaluation.dept_evaluation?.init?.score || 'N/A' }}
                    </VChip>
                    <div class="text-caption reviewer-info">
                      {{ selectedEvaluation.dept_evaluation?.init?.reviewer ? `Người đánh giá: ${selectedEvaluation.dept_evaluation.init.reviewer}` : '\u00A0' }}
                    </div>
                  </VCardText>
                </VCard>
              </VCol>
              <VCol
                cols="12"
                md="4"
              >
                <VCard
                  variant="tonal"
                  class="evaluation-card"
                >
                  <VCardText>
                    <div class="text-caption text-medium-emphasis mb-2">
                      Đánh giá xét duyệt
                    </div>
                    <VChip
                      :color="getScoreColor(selectedEvaluation.dept_evaluation?.review?.score)"
                      class="mb-2"
                    >
                      {{ selectedEvaluation.dept_evaluation?.review?.score || 'N/A' }}
                    </VChip>
                    <div class="text-caption reviewer-info">
                      {{ selectedEvaluation.dept_evaluation?.review?.reviewer ? `Người xét duyệt: ${selectedEvaluation.dept_evaluation.review.reviewer}` : '\u00A0' }}
                    </div>
                  </VCardText>
                </VCard>
              </VCol>
              <VCol
                cols="12"
                md="4"
              >
                <VCard
                  variant="tonal"
                  class="evaluation-card"
                >
                  <VCardText>
                    <div class="text-caption text-medium-emphasis mb-2">
                      Đánh giá cuối cùng
                    </div>
                    <VChip
                      :color="getScoreColor(selectedEvaluation.dept_evaluation?.final?.score)"
                      class="mb-2"
                    >
                      {{ selectedEvaluation.dept_evaluation?.final?.score || 'N/A' }}
                    </VChip>
                    <div class="text-caption reviewer-info">
                      {{ selectedEvaluation.dept_evaluation?.final?.reviewer ? `Người phê duyệt: ${selectedEvaluation.dept_evaluation.final.reviewer}` : '\u00A0' }}
                    </div>
                  </VCardText>
                </VCard>
              </VCol>
            </VRow>
          </div>

          <VDivider class="my-6" />

          <!-- Manager Evaluation -->
          <div class="mb-6">
            <h6 class="text-h6 mb-4">
              Đánh giá quản lý
            </h6>
            <VRow>
              <VCol
                cols="12"
                md="4"
              >
                <VCard
                  variant="tonal"
                  class="evaluation-card"
                >
                  <VCardText>
                    <div class="text-caption text-medium-emphasis mb-2">
                      Đánh giá ban đầu
                    </div>
                    <VChip
                      :color="getScoreColor(selectedEvaluation.mgr_evaluation?.init?.score)"
                      class="mb-2"
                    >
                      {{ selectedEvaluation.mgr_evaluation?.init?.score || 'N/A' }}
                    </VChip>
                    <div class="text-caption reviewer-info">
                      {{ selectedEvaluation.mgr_evaluation?.init?.reviewer ? `Người đánh giá: ${selectedEvaluation.mgr_evaluation.init.reviewer}` : '\u00A0' }}
                    </div>
                  </VCardText>
                </VCard>
              </VCol>
              <VCol
                cols="12"
                md="4"
              >
                <VCard
                  variant="tonal"
                  class="evaluation-card"
                >
                  <VCardText>
                    <div class="text-caption text-medium-emphasis mb-2">
                      Đánh giá xét duyệt
                    </div>
                    <VChip
                      :color="getScoreColor(selectedEvaluation.mgr_evaluation?.review?.score)"
                      class="mb-2"
                    >
                      {{ selectedEvaluation.mgr_evaluation?.review?.score || 'N/A' }}
                    </VChip>
                    <div class="text-caption reviewer-info">
                      {{ selectedEvaluation.mgr_evaluation?.review?.reviewer ? `Người xét duyệt: ${selectedEvaluation.mgr_evaluation.review.reviewer}` : '\u00A0' }}
                    </div>
                  </VCardText>
                </VCard>
              </VCol>
              <VCol
                cols="12"
                md="4"
              >
                <VCard
                  variant="tonal"
                  class="evaluation-card"
                >
                  <VCardText>
                    <div class="text-caption text-medium-emphasis mb-2">
                      Đánh giá cuối cùng
                    </div>
                    <VChip
                      :color="getScoreColor(selectedEvaluation.mgr_evaluation?.final?.score)"
                      class="mb-2"
                    >
                      {{ selectedEvaluation.mgr_evaluation?.final?.score || 'N/A' }}
                    </VChip>
                    <div class="text-caption reviewer-info">
                      {{ selectedEvaluation.mgr_evaluation?.final?.reviewer ? `Người phê duyệt: ${selectedEvaluation.mgr_evaluation.final.reviewer}` : '\u00A0' }}
                    </div>
                  </VCardText>
                </VCard>
              </VCol>
            </VRow>
          </div>

          <!-- Additional Info -->
          <VDivider class="my-6" />
          <VRow>
            <VCol cols="6">
              <div class="text-caption text-medium-emphasis">
                Số ngày nghỉ
              </div>
              <div class="font-weight-medium">
                {{ selectedEvaluation.leave_days || 0 }} ngày
              </div>
            </VCol>
            <VCol cols="6">
              <div class="text-caption text-medium-emphasis">
                Quốc tịch
              </div>
              <div class="font-weight-medium">
                {{ selectedEvaluation.nation || 'N/A' }}
              </div>
            </VCol>
          </VRow>
        </VCardText>
      </VCard>
    </VDialog>

    <!-- Toast Notification -->
    <VSnackbar
      v-model="toast.show"
      :color="toast.color"
      :timeout="3000"
      location="top"
    >
      {{ toast.message }}
      <template #actions>
        <VBtn
          variant="text"
          @click="toast.show = false"
        >
          Đóng
        </VBtn>
      </template>
    </VSnackbar>
  </div>
</template>

<style scoped>
.evaluation-card {
  height: 100%;
}

.reviewer-info {
  min-height: 1.5em;
}

.score-badge {
  font-weight: 600;
  font-size: 1.1rem;
}
</style>
