<script setup>
import { ref } from 'vue'
import { useGuestProtection } from '@/composables/useGuestProtection'
import { $api } from '@/utils/api'
import { formatEmployeeId, formatCurrency } from '@/utils/formatters'
import { silentRequiredValidator } from '@/@core/utils/validators'

// Protect from guest users
useGuestProtection()

// State
const loading = ref(false)
const billsData = ref(null)
const error = ref(null)

// Form ref
const formRef = ref()

// Pagination
const currentPage = ref(1)
const pageSize = ref(50)
const totalRecords = ref(0)

// Form inputs
const searchEmployeeId = ref('')
const searchTermCode = ref('')
const searchDormCode = ref('')

// Search dormitory bills
const searchBills = async (resetPage = false) => {
  if (resetPage) {
    currentPage.value = 1
  }

  loading.value = true
  error.value = null
  billsData.value = null

  try {
    // Build query params
    const params = new URLSearchParams()

    if (searchEmployeeId.value?.trim()) {
      const formattedId = formatEmployeeId(searchEmployeeId.value)
      // Extract numeric ID from formatted ID (VNW0014732 → 14732)
      const numericId = formattedId.replace(/^VNW0*/i, '')
      params.append('employee_id', numericId)
    }

    if (searchTermCode.value?.trim()) {
      params.append('term_code', searchTermCode.value.trim())
    }

    if (searchDormCode.value?.trim()) {
      params.append('dorm_code', searchDormCode.value.trim())
    }

    params.append('page', currentPage.value)
    params.append('page_size', pageSize.value)

    const response = await $api(`/dormitory-bills/search?${params.toString()}`)

    billsData.value = response.results || []
    totalRecords.value = response.total || 0
  }
  catch (err) {
    console.error('Failed to search dormitory bills:', err)
    error.value = err.message || 'Không thể tìm kiếm hóa đơn KTX'
    billsData.value = null
  }
  finally {
    loading.value = false
  }
}

// Pagination handlers
const handlePageChange = (page) => {
  currentPage.value = page
  searchBills(false)
}
</script>

<template>
  <!-- Search Form -->
  <VRow>
      <VCol cols="12">
        <VCard>
          <VCardTitle>
            <VIcon
              icon="tabler-home-dollar"
              class="me-2"
            />
            Tra Cứu Hóa Đơn KTX
          </VCardTitle>
          <VDivider />
          <VCardText>
            <VForm
              ref="formRef"
              @submit.prevent="searchBills(true)"
            >
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
                    @keyup.enter="searchBills(true)"
                  />
                </VCol>
                <VCol
                  cols="12"
                  md="3"
                >
                  <VTextField
                    v-model="searchTermCode"
                    label="Kỳ hóa đơn"
                    placeholder="VD: 25A, 251"
                    variant="outlined"
                    prepend-inner-icon="tabler-calendar"
                    clearable
                    hide-details
                    @keyup.enter="searchBills(true)"
                  />
                </VCol>
                <VCol
                  cols="12"
                  md="3"
                >
                  <VTextField
                    v-model="searchDormCode"
                    label="Mã phòng KTX"
                    placeholder="VD: P157, A01"
                    variant="outlined"
                    prepend-inner-icon="tabler-home"
                    clearable
                    hide-details
                    @keyup.enter="searchBills(true)"
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
                    @click="searchBills(true)"
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
      v-if="error && !loading"
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

    <!-- Results -->
    <VRow v-if="billsData && billsData.length > 0 && !loading">
      <VCol cols="12">
        <VCard>
          <VCardTitle class="d-flex justify-space-between align-center">
            <span>Kết Quả Tìm Kiếm</span>
            <VChip
              color="primary"
              variant="tonal"
            >
              {{ totalRecords }} kết quả
            </VChip>
          </VCardTitle>
          <VDivider />

          <VCardText>
            <VDataTable
              :items="billsData"
              :items-per-page="pageSize"
              hide-default-footer
            >
              <template #headers>
                <tr>
                  <th>Mã NV</th>
                  <th>Kỳ</th>
                  <th>Phòng</th>
                  <th>Khu vực</th>
                  <th class="text-end">Điện (kWh)</th>
                  <th class="text-end">Tiền điện</th>
                  <th class="text-end">Nước (m³)</th>
                  <th class="text-end">Tiền nước</th>
                  <th class="text-end">Phí khác</th>
                  <th class="text-end">Tổng cộng</th>
                </tr>
              </template>

              <template #item="{ item }">
                <tr>
                  <td>{{ item.employee_id }}</td>
                  <td>
                    <VChip
                      size="small"
                      color="info"
                      variant="tonal"
                    >
                      {{ item.term_code }}
                    </VChip>
                  </td>
                  <td>{{ item.dorm_code }}</td>
                  <td>{{ item.factory_location }}</td>
                  <td class="text-end">
                    {{ item.elec_usage?.toFixed(1) }}
                    <span class="text-caption text-medium-emphasis">
                      ({{ item.elec_last_index }} → {{ item.elec_curr_index }})
                    </span>
                  </td>
                  <td class="text-end font-weight-medium">
                    {{ formatCurrency(item.elec_amount) }}
                  </td>
                  <td class="text-end">
                    {{ item.water_usage?.toFixed(1) }}
                    <span class="text-caption text-medium-emphasis">
                      ({{ item.water_last_index }} → {{ item.water_curr_index }})
                    </span>
                  </td>
                  <td class="text-end font-weight-medium">
                    {{ formatCurrency(item.water_amount) }}
                  </td>
                  <td class="text-end">
                    <div class="text-caption">
                      Chung: {{ formatCurrency(item.shared_fee) }}
                    </div>
                    <div class="text-caption">
                      Quản lý: {{ formatCurrency(item.management_fee) }}
                    </div>
                  </td>
                  <td class="text-end">
                    <VChip
                      color="success"
                      variant="tonal"
                    >
                      {{ formatCurrency(item.total_amount) }}
                    </VChip>
                  </td>
                </tr>
              </template>
            </VDataTable>
          </VCardText>

          <!-- Pagination -->
          <VDivider />
          <VCardText class="d-flex justify-center">
            <VPagination
              v-model="currentPage"
              :length="Math.ceil(totalRecords / pageSize)"
              @update:model-value="handlePageChange"
            />
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <!-- No Data State -->
    <VRow v-if="!billsData && !loading && !error">
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
</template>
