<script setup>
import { ref, computed, onMounted } from 'vue'
import { $api } from '@/utils/api'
import { formatEmployeeId, getScoreColor } from '@/utils/formatters'

// State
const loading = ref(false)
const evaluations = ref([])
const total = ref(0)

// Search filters
const searchEmployeeId = ref('')
const searchTermCode = ref('')
const searchDeptCode = ref('')

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

    // Sort evaluations by term_code
    const results = response.results || []
    results.sort((a, b) => sortTermCodes(a.term_code, b.term_code))

    evaluations.value = results
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
            <VForm @submit.prevent="searchEvaluations(true)">
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
                    hide-details
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
                    hide-details
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
                    hide-details
                    @keyup.enter="searchEvaluations(true)"
                  />
                </VCol>
                <VCol
                  cols="12"
                  md="3"
                  class="d-flex align-end justify-end"
                >
                  <VBtn
                    color="primary"
                    :block="$vuetify.display.smAndDown"
                    :width="$vuetify.display.mdAndUp ? 140 : undefined"
                    :loading="loading"
                    @click="searchEvaluations(true)"
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
              Đang tìm kiếm...
            </p>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <!-- Results Table -->
    <VRow v-if="!loading && evaluations.length > 0">
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

    <!-- No Data State -->
    <VRow v-if="!loading && evaluations.length === 0 && !error">
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
              Vui lòng nhập điều kiện tìm kiếm và nhấn "Tra Cứu"
            </p>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <!-- Detail Dialog -->
    <VDialog
      v-model="detailDialog"
      max-width="1200"
      scrollable
    >
      <VCard v-if="selectedEvaluation">
        <VCardTitle class="d-flex align-center justify-space-between">
          <div class="d-flex align-center gap-3">
            <VIcon
              icon="tabler-file-text"
              size="24"
            />
            <div>
              <div class="text-h6">
                {{ selectedEvaluation.employee_name }}
              </div>
              <div class="text-caption text-medium-emphasis">
                {{ selectedEvaluation.employee_id }} - Kỳ {{ selectedEvaluation.term_code }}
              </div>
            </div>
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
          <!-- Department Evaluations -->
          <div class="mb-6">
            <h6 class="text-h6 font-weight-bold mb-4">
              <VIcon
                icon="tabler-building"
                class="me-2"
              />
              Đánh giá phòng ban
            </h6>
            <VRow>
              <!-- Dept Init -->
              <VCol
                cols="12"
                md="4"
              >
                <VCard variant="outlined">
                  <VCardText>
                    <div class="d-flex align-center justify-space-between mb-3">
                      <span class="text-body-2 font-weight-medium">Đánh giá ban đầu</span>
                      <VChip
                        :color="getScoreColor(selectedEvaluation.dept_evaluation?.init?.score)"
                        size="small"
                      >
                        {{ selectedEvaluation.dept_evaluation?.init?.score || 'N/A' }}
                      </VChip>
                    </div>
                    <div class="text-caption mb-2">
                      <strong>Người đánh giá:</strong> {{ selectedEvaluation.dept_evaluation?.init?.reviewer || 'N/A' }}
                    </div>
                    <div
                      v-if="selectedEvaluation.dept_evaluation?.init?.comment"
                      class="comment-box"
                    >
                      <div class="text-caption mb-1">
                        <strong>Nhận xét:</strong>
                      </div>
                      {{ selectedEvaluation.dept_evaluation.init.comment }}
                    </div>
                  </VCardText>
                </VCard>
              </VCol>

              <!-- Dept Review -->
              <VCol
                cols="12"
                md="4"
              >
                <VCard variant="outlined">
                  <VCardText>
                    <div class="d-flex align-center justify-space-between mb-3">
                      <span class="text-body-2 font-weight-medium">Đánh giá xét duyệt</span>
                      <VChip
                        :color="getScoreColor(selectedEvaluation.dept_evaluation?.review?.score)"
                        size="small"
                      >
                        {{ selectedEvaluation.dept_evaluation?.review?.score || 'N/A' }}
                      </VChip>
                    </div>
                    <div class="text-caption mb-2">
                      <strong>Người đánh giá:</strong> {{ selectedEvaluation.dept_evaluation?.review?.reviewer || 'N/A' }}
                    </div>
                    <div
                      v-if="selectedEvaluation.dept_evaluation?.review?.comment"
                      class="comment-box"
                    >
                      <div class="text-caption mb-1">
                        <strong>Nhận xét:</strong>
                      </div>
                      {{ selectedEvaluation.dept_evaluation.review.comment }}
                    </div>
                  </VCardText>
                </VCard>
              </VCol>

              <!-- Dept Final -->
              <VCol
                cols="12"
                md="4"
              >
                <VCard variant="outlined">
                  <VCardText>
                    <div class="d-flex align-center justify-space-between mb-3">
                      <span class="text-body-2 font-weight-medium">Đánh giá cuối cùng</span>
                      <VChip
                        :color="getScoreColor(selectedEvaluation.dept_evaluation?.final?.score)"
                        size="small"
                      >
                        {{ selectedEvaluation.dept_evaluation?.final?.score || 'N/A' }}
                      </VChip>
                    </div>
                    <div class="text-caption mb-2">
                      <strong>Người đánh giá:</strong> {{ selectedEvaluation.dept_evaluation?.final?.reviewer || 'N/A' }}
                    </div>
                    <div
                      v-if="selectedEvaluation.dept_evaluation?.final?.comment"
                      class="comment-box"
                    >
                      <div class="text-caption mb-1">
                        <strong>Nhận xét:</strong>
                      </div>
                      {{ selectedEvaluation.dept_evaluation.final.comment }}
                    </div>
                  </VCardText>
                </VCard>
              </VCol>
            </VRow>
          </div>

          <VDivider class="my-6" />

          <!-- Manager Evaluations -->
          <div>
            <h6 class="text-h6 font-weight-bold mb-4">
              <VIcon
                icon="tabler-user-star"
                class="me-2"
              />
              Đánh giá quản lý
            </h6>
            <VRow>
              <!-- Mgr Init -->
              <VCol
                cols="12"
                md="4"
              >
                <VCard variant="outlined">
                  <VCardText>
                    <div class="d-flex align-center justify-space-between mb-3">
                      <span class="text-body-2 font-weight-medium">Đánh giá ban đầu</span>
                      <VChip
                        :color="getScoreColor(selectedEvaluation.mgr_evaluation?.init?.score)"
                        size="small"
                      >
                        {{ selectedEvaluation.mgr_evaluation?.init?.score || 'N/A' }}
                      </VChip>
                    </div>
                    <div class="text-caption mb-2">
                      <strong>Người đánh giá:</strong> {{ selectedEvaluation.mgr_evaluation?.init?.reviewer || 'N/A' }}
                    </div>
                    <div
                      v-if="selectedEvaluation.mgr_evaluation?.init?.comment"
                      class="comment-box"
                    >
                      <div class="text-caption mb-1">
                        <strong>Nhận xét:</strong>
                      </div>
                      {{ selectedEvaluation.mgr_evaluation.init.comment }}
                    </div>
                  </VCardText>
                </VCard>
              </VCol>

              <!-- Mgr Review -->
              <VCol
                cols="12"
                md="4"
              >
                <VCard variant="outlined">
                  <VCardText>
                    <div class="d-flex align-center justify-space-between mb-3">
                      <span class="text-body-2 font-weight-medium">Đánh giá xét duyệt</span>
                      <VChip
                        :color="getScoreColor(selectedEvaluation.mgr_evaluation?.review?.score)"
                        size="small"
                      >
                        {{ selectedEvaluation.mgr_evaluation?.review?.score || 'N/A' }}
                      </VChip>
                    </div>
                    <div class="text-caption mb-2">
                      <strong>Người đánh giá:</strong> {{ selectedEvaluation.mgr_evaluation?.review?.reviewer || 'N/A' }}
                    </div>
                    <div
                      v-if="selectedEvaluation.mgr_evaluation?.review?.comment"
                      class="comment-box"
                    >
                      <div class="text-caption mb-1">
                        <strong>Nhận xét:</strong>
                      </div>
                      {{ selectedEvaluation.mgr_evaluation.review.comment }}
                    </div>
                  </VCardText>
                </VCard>
              </VCol>

              <!-- Mgr Final -->
              <VCol
                cols="12"
                md="4"
              >
                <VCard variant="outlined">
                  <VCardText>
                    <div class="d-flex align-center justify-space-between mb-3">
                      <span class="text-body-2 font-weight-medium">Đánh giá cuối cùng</span>
                      <VChip
                        :color="getScoreColor(selectedEvaluation.mgr_evaluation?.final?.score)"
                        size="small"
                      >
                        {{ selectedEvaluation.mgr_evaluation?.final?.score || 'N/A' }}
                      </VChip>
                    </div>
                    <div class="text-caption mb-2">
                      <strong>Người đánh giá:</strong> {{ selectedEvaluation.mgr_evaluation?.final?.reviewer || 'N/A' }}
                    </div>
                    <div
                      v-if="selectedEvaluation.mgr_evaluation?.final?.comment"
                      class="comment-box"
                    >
                      <div class="text-caption mb-1">
                        <strong>Nhận xét:</strong>
                      </div>
                      {{ selectedEvaluation.mgr_evaluation.final.comment }}
                    </div>
                  </VCardText>
                </VCard>
              </VCol>
            </VRow>
          </div>
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

.evaluation-box {
  padding: 1rem;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: 8px;
  background-color: rgba(var(--v-theme-on-surface), 0.02);
}

.comment-box {
  font-size: 0.875rem;
  line-height: 1.5;
  max-height: 300px;
  overflow-y: auto;
  color: rgba(var(--v-theme-on-surface), 0.87);
  margin-top: 0.5rem;
  padding: 0.75rem;
  background-color: rgba(var(--v-theme-on-surface), 0.05);
  border-radius: 6px;
  border-left: 3px solid rgba(var(--v-theme-primary), 0.4);
  word-wrap: break-word;
  white-space: pre-wrap;
}

.comment-box::-webkit-scrollbar {
  width: 6px;
}

.comment-box::-webkit-scrollbar-track {
  background: rgba(var(--v-theme-on-surface), 0.05);
  border-radius: 3px;
}

.comment-box::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-on-surface), 0.2);
  border-radius: 3px;
}

.comment-box::-webkit-scrollbar-thumb:hover {
  background: rgba(var(--v-theme-on-surface), 0.3);
}
</style>
