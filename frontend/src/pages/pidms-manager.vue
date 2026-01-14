<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAdminProtection } from '@/composables/useAdminProtection'
import { $api } from '@/utils/api'

// Protect this page - only admin can access
useAdminProtection()

// State
const loading = ref(false)
const products = ref([])
const searchResults = ref([])
const searchLoading = ref(false)
const importLoading = ref(false)
const syncLoading = ref(false)

// Products table state
const productsSearch = ref('')
const productsPage = ref(1)
const productsPageSize = ref(10)
const productsSortBy = ref([{ key: 'total_remaining', order: 'desc' }])

// Dialogs
const importDialog = ref(false)
const syncDialog = ref(false)
const keyDetailsDialog = ref(false)
const selectedKey = ref(null)
const productKeysDialog = ref(false)
const selectedProduct = ref(null)
const productKeys = ref([])
const productKeysLoading = ref(false)
const productKeysPage = ref(1)
const productKeysPageSize = ref(50)
const productKeysTotalResults = ref(0)
const productKeysPageSizeOptions = [
  { value: 10, title: '10' },
  { value: 25, title: '25' },
  { value: 50, title: '50' },
  { value: 100, title: '100' },
]

// Search filters
const searchProduct = ref('')
const searchMinRemaining = ref(null)
const searchMaxRemaining = ref(null)
const searchBlocked = ref(null)
const currentPage = ref(1)
const pageSize = ref(50)
const totalResults = ref(0)
const pageSizeOptions = [
  { value: 10, title: '10' },
  { value: 25, title: '25' },
  { value: 50, title: '50' },
  { value: 100, title: '100' },
]

// Import form
const importKeys = ref('')

// Sync form
const syncProductFilter = ref('')

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

// Load products summary on mount
onMounted(async () => {
  await loadProducts()
})

// Load products summary
const loadProducts = async () => {
  loading.value = true
  try {
    const response = await $api('/pidms/products')
    products.value = response.products || []
  }
  catch (error) {
    console.error('Failed to load products:', error)
    showToast('Không thể tải danh sách sản phẩm!', 'error')
  }
  finally {
    loading.value = false
  }
}

// Search keys
const searchKeys = async (resetPage = false) => {
  if (resetPage) {
    currentPage.value = 1
  }

  searchLoading.value = true
  try {
    const params = new URLSearchParams()

    if (searchProduct.value?.trim()) {
      params.append('product', searchProduct.value.trim())
    }
    if (searchMinRemaining.value !== null && searchMinRemaining.value !== '') {
      params.append('min_remaining', searchMinRemaining.value)
    }
    if (searchMaxRemaining.value !== null && searchMaxRemaining.value !== '') {
      params.append('max_remaining', searchMaxRemaining.value)
    }
    if (searchBlocked.value !== null && searchBlocked.value !== '') {
      params.append('blocked', searchBlocked.value)
    }
    params.append('page', currentPage.value)
    params.append('page_size', pageSize.value)

    const response = await $api(`/pidms/search?${params.toString()}`)
    searchResults.value = response.results || []
    totalResults.value = response.total || 0
  }
  catch (error) {
    console.error('Failed to search keys:', error)
    showToast('Không thể tìm kiếm keys!', 'error')
    searchResults.value = []
    totalResults.value = 0
  }
  finally {
    searchLoading.value = false
  }
}

// Import keys
const importKeysSubmit = async () => {
  if (!importKeys.value.trim()) {
    showToast('Vui lòng nhập product keys!', 'warning')
    return
  }

  importLoading.value = true
  try {
    const response = await $api('/pidms/check', {
      method: 'POST',
      body: { keys: importKeys.value },
    })

    if (response.success) {
      const { summary } = response
      showToast(
        `Import thành công! ${summary.new_keys} keys mới, ${summary.updated_keys} keys cập nhật`,
        'success'
      )
      importDialog.value = false
      importKeys.value = ''

      // Reload products and search results
      await loadProducts()
      if (searchResults.value.length > 0) {
        await searchKeys()
      }
    }
  }
  catch (error) {
    console.error('Failed to import keys:', error)
    showToast('Import keys thất bại!', 'error')
  }
  finally {
    importLoading.value = false
  }
}

// Sync all keys
const syncKeysSubmit = async () => {
  syncLoading.value = true
  try {
    const response = await $api('/pidms/sync', {
      method: 'POST',
      body: { product_filter: syncProductFilter.value || null },
    })

    if (response.success) {
      const { summary } = response
      showToast(
        `Sync thành công! ${summary.total_synced} keys, ${summary.updated} cập nhật, ${summary.errors} lỗi`,
        summary.errors > 0 ? 'warning' : 'success'
      )
      syncDialog.value = false
      syncProductFilter.value = ''

      // Reload products and search results
      await loadProducts()
      if (searchResults.value.length > 0) {
        await searchKeys()
      }
    }
  }
  catch (error) {
    console.error('Failed to sync keys:', error)
    showToast('Sync keys thất bại!', 'error')
  }
  finally {
    syncLoading.value = false
  }
}

// Show key details
const showKeyDetails = (key) => {
  selectedKey.value = key
  keyDetailsDialog.value = true
}

// Close key details
const closeKeyDetails = () => {
  keyDetailsDialog.value = false
  selectedKey.value = null
}

// Get status color
const getStatusColor = (remaining) => {
  if (remaining === 0) return 'error'
  if (remaining < 100) return 'warning'
  return 'success'
}

// Get blocked color
const getBlockedColor = (blocked) => {
  return blocked === 1 ? 'error' : 'success'
}

// Blocked options
const blockedOptions = [
  { value: null, title: 'Tất cả' },
  { value: -1, title: 'Không bị chặn' },
  { value: 1, title: 'Bị chặn' },
]

// Total pages
const totalPages = computed(() => Math.ceil(totalResults.value / pageSize.value))

// Handle page change
const handlePageChange = (page) => {
  currentPage.value = page
  searchKeys(false)
}

// Handle page size change
const handlePageSizeChange = () => {
  currentPage.value = 1
  if (searchResults.value.length > 0) {
    searchKeys(false)
  }
}

// Filtered products for table
const filteredProducts = computed(() => {
  if (!productsSearch.value) return products.value

  const search = productsSearch.value.toLowerCase()
  return products.value.filter(p =>
    p.prd.toLowerCase().includes(search)
  )
})

// Products table headers
const productsHeaders = [
  { title: 'Product', key: 'prd', align: 'start', sortable: true },
  { title: 'Keys', key: 'key_count', align: 'center', sortable: true },
  { title: 'Total Remaining', key: 'total_remaining', align: 'center', sortable: true },
  { title: 'Avg Remaining', key: 'avg_remaining', align: 'center', sortable: true },
  { title: 'Status', key: 'low_inventory', align: 'center', sortable: true },
  { title: 'Actions', key: 'actions', align: 'center', sortable: false },
]

// Get inventory status
const getInventoryStatus = (product) => {
  if (product.total_remaining === 0) return { text: 'Out of Stock', color: 'error' }
  if (product.low_inventory) return { text: 'Low Stock', color: 'warning' }
  return { text: 'In Stock', color: 'success' }
}

// View product keys
const viewProductKeys = async (product, page = 1) => {
  selectedProduct.value = product
  productKeysDialog.value = true
  productKeysLoading.value = true
  productKeys.value = []

  try {
    const params = new URLSearchParams()
    params.append('product', product.prd)
    params.append('page', page)
    params.append('page_size', productKeysPageSize.value)

    const response = await $api(`/pidms/search?${params.toString()}`)
    productKeys.value = response.results || []
    productKeysTotalResults.value = response.total || 0
    productKeysPage.value = page
  }
  catch (error) {
    console.error('Failed to load product keys:', error)
    showToast('Không thể tải danh sách keys!', 'error')
    productKeys.value = []
    productKeysTotalResults.value = 0
  }
  finally {
    productKeysLoading.value = false
  }
}

// Handle product keys page change
const handleProductKeysPageChange = (page) => {
  if (selectedProduct.value) {
    viewProductKeys(selectedProduct.value, page)
  }
}

// Handle product keys page size change
const handleProductKeysPageSizeChange = () => {
  productKeysPage.value = 1
  if (selectedProduct.value) {
    viewProductKeys(selectedProduct.value, 1)
  }
}

// Total pages for product keys
const productKeysTotalPages = computed(() =>
  Math.ceil(productKeysTotalResults.value / productKeysPageSize.value)
)

// Close product keys dialog
const closeProductKeysDialog = () => {
  productKeysDialog.value = false
  selectedProduct.value = null
  productKeys.value = []
  productKeysPage.value = 1
  productKeysTotalResults.value = 0
}
</script>

<template>
  <div>
    <!-- Header -->
    <VCard class="mb-6">
      <VCardTitle class="d-flex align-center justify-space-between">
        <div class="d-flex align-center gap-2">
          <VIcon
            icon="tabler-key"
            size="28"
          />
          <span>PIDMS - Product Key Management</span>
        </div>
        <VChip
          color="error"
          variant="tonal"
        >
          <VIcon
            icon="tabler-shield-lock"
            start
          />
          Admin Only
        </VChip>
      </VCardTitle>

      <VCardText>
        <VAlert
          type="info"
          variant="tonal"
          class="mb-4"
        >
          <template #prepend>
            <VIcon icon="tabler-info-circle" />
          </template>
          <div>
            <strong>Quản lý Product Keys</strong>
            <p class="mt-2">
              Trang này cho phép quản lý Microsoft product keys từ PIDKey.com. Bạn có thể import keys mới, tìm kiếm, và đồng bộ với API.
            </p>
          </div>
        </VAlert>

        <!-- Action Buttons -->
        <div class="d-flex gap-3">
          <VBtn
            color="primary"
            prepend-icon="tabler-upload"
            @click="importDialog = true"
          >
            Import Keys
          </VBtn>
          <VBtn
            color="success"
            prepend-icon="tabler-refresh"
            @click="syncDialog = true"
          >
            Sync Keys
          </VBtn>
          <VBtn
            color="info"
            prepend-icon="tabler-reload"
            :loading="loading"
            @click="loadProducts"
          >
            Reload Stats
          </VBtn>
        </div>
      </VCardText>
    </VCard>

    <!-- Products Statistics -->
    <VCard class="mb-6">
      <VCardTitle class="d-flex align-center justify-space-between">
        <div class="d-flex align-center gap-2">
          <VIcon
            icon="tabler-chart-bar"
            size="24"
          />
          <span>Thống Kê Sản Phẩm</span>
        </div>
        <VChip
          v-if="products.length > 0"
          color="primary"
          variant="tonal"
        >
          {{ products.length }} products
        </VChip>
      </VCardTitle>
      <VDivider />
      <VCardText>
        <!-- Loading State -->
        <div
          v-if="loading"
          class="text-center py-8"
        >
          <VProgressCircular
            indeterminate
            color="primary"
            size="64"
          />
          <p class="mt-4">
            Đang tải thống kê...
          </p>
        </div>

        <!-- Products Table -->
        <div v-else-if="products.length > 0">
          <!-- Summary Cards -->
          <VRow class="mb-4">
            <VCol
              cols="12"
              sm="6"
              md="3"
            >
              <VCard
                color="primary"
                variant="tonal"
              >
                <VCardText>
                  <div class="d-flex align-center gap-3">
                    <VIcon
                      icon="tabler-key"
                      size="32"
                    />
                    <div>
                      <div class="text-caption text-medium-emphasis">
                        Total Products
                      </div>
                      <div class="text-h5 font-weight-bold">
                        {{ products.length }}
                      </div>
                    </div>
                  </div>
                </VCardText>
              </VCard>
            </VCol>
            <VCol
              cols="12"
              sm="6"
              md="3"
            >
              <VCard
                color="success"
                variant="tonal"
              >
                <VCardText>
                  <div class="d-flex align-center gap-3">
                    <VIcon
                      icon="tabler-checks"
                      size="32"
                    />
                    <div>
                      <div class="text-caption text-medium-emphasis">
                        Total Keys
                      </div>
                      <div class="text-h5 font-weight-bold">
                        {{ products.reduce((sum, p) => sum + p.key_count, 0) }}
                      </div>
                    </div>
                  </div>
                </VCardText>
              </VCard>
            </VCol>
            <VCol
              cols="12"
              sm="6"
              md="3"
            >
              <VCard
                color="info"
                variant="tonal"
              >
                <VCardText>
                  <div class="d-flex align-center gap-3">
                    <VIcon
                      icon="tabler-stack"
                      size="32"
                    />
                    <div>
                      <div class="text-caption text-medium-emphasis">
                        Total Remaining
                      </div>
                      <div class="text-h5 font-weight-bold">
                        {{ products.reduce((sum, p) => sum + p.total_remaining, 0).toLocaleString() }}
                      </div>
                    </div>
                  </div>
                </VCardText>
              </VCard>
            </VCol>
            <VCol
              cols="12"
              sm="6"
              md="3"
            >
              <VCard
                color="warning"
                variant="tonal"
              >
                <VCardText>
                  <div class="d-flex align-center gap-3">
                    <VIcon
                      icon="tabler-alert-triangle"
                      size="32"
                    />
                    <div>
                      <div class="text-caption text-medium-emphasis">
                        Low Stock
                      </div>
                      <div class="text-h5 font-weight-bold">
                        {{ products.filter(p => p.low_inventory).length }}
                      </div>
                    </div>
                  </div>
                </VCardText>
              </VCard>
            </VCol>
          </VRow>

          <!-- Search -->
          <VTextField
            v-model="productsSearch"
            placeholder="Tìm kiếm product..."
            prepend-inner-icon="tabler-search"
            variant="outlined"
            clearable
            hide-details
            class="mb-4"
          />

          <!-- Data Table -->
          <VDataTable
            :headers="productsHeaders"
            :items="filteredProducts"
            :sort-by="productsSortBy"
            :items-per-page="productsPageSize"
            :page="productsPage"
            @update:page="productsPage = $event"
            @update:sort-by="productsSortBy = $event"
          >
            <template #item.prd="{ item }">
              <div class="text-body-2 font-weight-medium">
                {{ item.prd }}
              </div>
            </template>

            <template #item.key_count="{ item }">
              <VChip
                size="small"
                variant="tonal"
                color="primary"
              >
                {{ item.key_count }}
              </VChip>
            </template>

            <template #item.total_remaining="{ item }">
              <VChip
                size="small"
                variant="tonal"
                :color="item.total_remaining === 0 ? 'error' : item.total_remaining < 100 ? 'warning' : 'success'"
              >
                {{ item.total_remaining.toLocaleString() }}
              </VChip>
            </template>

            <template #item.avg_remaining="{ item }">
              <span class="text-body-2">{{ item.avg_remaining.toFixed(1) }}</span>
            </template>

            <template #item.low_inventory="{ item }">
              <VChip
                size="small"
                :color="getInventoryStatus(item).color"
              >
                {{ getInventoryStatus(item).text }}
              </VChip>
            </template>

            <template #item.actions="{ item }">
              <VBtn
                icon
                variant="text"
                size="small"
                color="primary"
                @click="viewProductKeys(item)"
              >
                <VIcon icon="tabler-eye" />
                <VTooltip activator="parent">
                  Xem keys
                </VTooltip>
              </VBtn>
            </template>
          </VDataTable>
        </div>

        <!-- Empty State -->
        <div
          v-else
          class="text-center py-8"
        >
          <VIcon
            icon="tabler-database-off"
            size="64"
            color="disabled"
          />
          <p class="mt-4 text-disabled">
            Chưa có product keys nào
          </p>
        </div>
      </VCardText>
    </VCard>

    <!-- Search Section -->
    <VCard>
      <VCardTitle>
        <VIcon
          icon="tabler-search"
          class="me-2"
        />
        Tìm Kiếm Product Keys
      </VCardTitle>
      <VDivider />
      <VCardText>
        <!-- Search Filters -->
        <VRow class="mb-4">
          <VCol
            cols="12"
            md="3"
          >
            <VTextField
              v-model="searchProduct"
              label="Product Name"
              placeholder="VD: Office, Windows"
              variant="outlined"
              prepend-inner-icon="tabler-package"
              clearable
              hide-details
              @keyup.enter="searchKeys(true)"
            />
          </VCol>
          <VCol
            cols="12"
            md="3"
          >
            <VSelect
              v-model="searchBlocked"
              :items="blockedOptions"
              label="Trạng thái"
              variant="outlined"
              hide-details
            />
          </VCol>
          <VCol
            cols="12"
            md="2"
          >
            <VTextField
              v-model.number="searchMinRemaining"
              label="Min Remaining"
              placeholder="0"
              variant="outlined"
              type="number"
              clearable
              hide-details
              @keyup.enter="searchKeys(true)"
            />
          </VCol>
          <VCol
            cols="12"
            md="2"
          >
            <VTextField
              v-model.number="searchMaxRemaining"
              label="Max Remaining"
              placeholder="9999"
              variant="outlined"
              type="number"
              clearable
              hide-details
              @keyup.enter="searchKeys(true)"
            />
          </VCol>
          <VCol
            cols="12"
            md="2"
            class="d-flex align-end justify-end"
          >
            <VBtn
              color="primary"
              :block="$vuetify.display.smAndDown"
              :width="$vuetify.display.mdAndUp ? 140 : undefined"
              :loading="searchLoading"
              @click="searchKeys(true)"
            >
              <VIcon
                start
                icon="tabler-search"
              />
              Tìm Kiếm
            </VBtn>
          </VCol>
        </VRow>

        <!-- Search Results -->
        <div v-if="searchResults.length > 0">
          <div class="d-flex justify-space-between align-center mb-4">
            <h6 class="text-h6">
              Kết quả tìm kiếm
            </h6>
            <VChip
              color="primary"
              variant="tonal"
            >
              {{ totalResults }} keys
            </VChip>
          </div>

          <VTable>
            <thead>
              <tr>
                <th class="text-left">
                  ID
                </th>
                <th class="text-left">
                  Product Key
                </th>
                <th class="text-left">
                  Product
                </th>
                <th class="text-center">
                  Remaining
                </th>
                <th class="text-center">
                  Status
                </th>
                <th class="text-center">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="key in searchResults"
                :key="key.id"
              >
                <td>{{ key.id }}</td>
                <td>
                  <code class="text-body-2">{{ key.keyname_with_dash }}</code>
                </td>
                <td>{{ key.prd }}</td>
                <td class="text-center">
                  <VChip
                    :color="getStatusColor(key.remaining)"
                    size="small"
                    variant="tonal"
                  >
                    {{ key.remaining.toLocaleString() }}
                  </VChip>
                </td>
                <td class="text-center">
                  <VChip
                    :color="getBlockedColor(key.blocked)"
                    size="small"
                  >
                    {{ key.blocked === 1 ? 'Blocked' : 'Active' }}
                  </VChip>
                </td>
                <td class="text-center">
                  <VBtn
                    icon
                    variant="text"
                    size="small"
                    @click="showKeyDetails(key)"
                  >
                    <VIcon icon="tabler-eye" />
                  </VBtn>
                </td>
              </tr>
            </tbody>
          </VTable>

          <!-- Pagination -->
          <VDivider class="mt-4" />
          <div class="d-flex align-center justify-space-between flex-wrap gap-4 pa-4">
            <div class="d-flex align-center gap-3">
              <div class="text-body-2 text-medium-emphasis">
                Hiển thị {{ totalResults === 0 ? 0 : ((currentPage - 1) * pageSize) + 1 }} - {{ Math.min(((currentPage - 1) * pageSize) + searchResults.length, totalResults) }} trong tổng số {{ totalResults }} kết quả
              </div>
              <VSelect
                v-model="pageSize"
                :items="pageSizeOptions"
                variant="outlined"
                density="compact"
                hide-details
                style="max-width: 100px;"
                @update:model-value="handlePageSizeChange"
              />
            </div>
            <VPagination
              v-model="currentPage"
              :length="totalPages"
              :total-visible="7"
              @update:model-value="handlePageChange"
            />
          </div>
        </div>

        <!-- No Results -->
        <div
          v-else-if="!searchLoading && searchResults.length === 0 && (searchProduct || searchMinRemaining || searchMaxRemaining || searchBlocked !== null)"
          class="text-center py-8"
        >
          <VIcon
            icon="tabler-search-off"
            size="64"
            color="disabled"
          />
          <p class="mt-4 text-disabled">
            Không tìm thấy kết quả nào
          </p>
        </div>
      </VCardText>
    </VCard>

    <!-- Import Dialog -->
    <VDialog
      v-model="importDialog"
      max-width="600"
    >
      <VCard>
        <VCardTitle class="d-flex align-center gap-2">
          <VIcon
            icon="tabler-upload"
            color="primary"
          />
          Import Product Keys
        </VCardTitle>
        <VDivider />
        <VCardText>
          <VAlert
            type="info"
            variant="tonal"
            class="mb-4"
          >
            Nhập các product keys (mỗi key một dòng, có thể có hoặc không có dấu gạch ngang)
          </VAlert>

          <VTextarea
            v-model="importKeys"
            label="Product Keys"
            placeholder="6NRGD-KHFCF-Y4TF7-PRWFD-YBF3H&#10;8NFMQ-FTF43-RQCKR-T473J-JFHB2"
            variant="outlined"
            rows="8"
            :disabled="importLoading"
          />
        </VCardText>
        <VDivider />
        <VCardActions class="px-6 py-4">
          <VSpacer />
          <VBtn
            color="grey"
            variant="text"
            :disabled="importLoading"
            @click="importDialog = false"
          >
            Hủy
          </VBtn>
          <VBtn
            color="primary"
            variant="elevated"
            :loading="importLoading"
            @click="importKeysSubmit"
          >
            <VIcon
              start
              icon="tabler-check"
            />
            Import
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Sync Dialog -->
    <VDialog
      v-model="syncDialog"
      max-width="500"
    >
      <VCard>
        <VCardTitle class="d-flex align-center gap-2">
          <VIcon
            icon="tabler-refresh"
            color="success"
          />
          Sync Product Keys
        </VCardTitle>
        <VDivider />
        <VCardText>
          <VAlert
            type="warning"
            variant="tonal"
            class="mb-4"
          >
            Đồng bộ tất cả keys trong database với PIDKey.com API. Quá trình này có thể mất vài phút.
          </VAlert>

          <VTextField
            v-model="syncProductFilter"
            label="Product Filter (Optional)"
            placeholder="VD: Office"
            variant="outlined"
            prepend-inner-icon="tabler-filter"
            hint="Để trống để sync tất cả keys"
            persistent-hint
            :disabled="syncLoading"
          />
        </VCardText>
        <VDivider />
        <VCardActions class="px-6 py-4">
          <VSpacer />
          <VBtn
            color="grey"
            variant="text"
            :disabled="syncLoading"
            @click="syncDialog = false"
          >
            Hủy
          </VBtn>
          <VBtn
            color="success"
            variant="elevated"
            :loading="syncLoading"
            @click="syncKeysSubmit"
          >
            <VIcon
              start
              icon="tabler-refresh"
            />
            Sync Now
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Key Details Dialog -->
    <VDialog
      v-model="keyDetailsDialog"
      max-width="700"
    >
      <VCard v-if="selectedKey">
        <VCardTitle class="d-flex align-center justify-space-between">
          <div class="d-flex align-center gap-2">
            <VIcon
              icon="tabler-key"
              color="primary"
            />
            Key Details
          </div>
          <VBtn
            icon
            variant="text"
            @click="closeKeyDetails"
          >
            <VIcon icon="tabler-x" />
          </VBtn>
        </VCardTitle>
        <VDivider />
        <VCardText>
          <VRow>
            <VCol cols="12">
              <div class="mb-4">
                <div class="text-caption text-medium-emphasis mb-1">
                  Product Key
                </div>
                <code class="text-h6">{{ selectedKey.keyname_with_dash }}</code>
              </div>
            </VCol>

            <VCol
              cols="12"
              md="6"
            >
              <div class="mb-4">
                <div class="text-caption text-medium-emphasis mb-1">
                  Product
                </div>
                <strong>{{ selectedKey.prd }}</strong>
              </div>
            </VCol>

            <VCol
              cols="12"
              md="6"
            >
              <div class="mb-4">
                <div class="text-caption text-medium-emphasis mb-1">
                  Remaining Activations
                </div>
                <VChip
                  :color="getStatusColor(selectedKey.remaining)"
                  variant="tonal"
                >
                  {{ selectedKey.remaining.toLocaleString() }}
                </VChip>
              </div>
            </VCol>

            <VCol
              cols="12"
              md="6"
            >
              <div class="mb-4">
                <div class="text-caption text-medium-emphasis mb-1">
                  Status
                </div>
                <VChip :color="getBlockedColor(selectedKey.blocked)">
                  {{ selectedKey.blocked === 1 ? 'Blocked' : 'Active' }}
                </VChip>
              </div>
            </VCol>

            <VCol
              cols="12"
              md="6"
            >
              <div class="mb-4">
                <div class="text-caption text-medium-emphasis mb-1">
                  Key Type
                </div>
                <div>{{ selectedKey.is_key_type || 'N/A' }}</div>
              </div>
            </VCol>

            <VCol
              v-if="selectedKey.eid"
              cols="12"
            >
              <div class="mb-4">
                <div class="text-caption text-medium-emphasis mb-1">
                  Enterprise ID
                </div>
                <div>{{ selectedKey.eid }}</div>
              </div>
            </VCol>

            <VCol
              v-if="selectedKey.datetime_checked_done"
              cols="12"
            >
              <div class="mb-4">
                <div class="text-caption text-medium-emphasis mb-1">
                  Last Checked
                </div>
                <div>{{ selectedKey.datetime_checked_done }}</div>
              </div>
            </VCol>
          </VRow>
        </VCardText>
      </VCard>
    </VDialog>

    <!-- Product Keys Dialog -->
    <VDialog
      v-model="productKeysDialog"
      max-width="1200"
      scrollable
    >
      <VCard v-if="selectedProduct">
        <VCardTitle class="d-flex align-center justify-space-between">
          <div class="d-flex align-center gap-2">
            <VIcon
              icon="tabler-list"
              color="primary"
            />
            <div>
              <div class="text-h6">
                Keys - {{ selectedProduct.prd }}
              </div>
              <div class="text-caption text-medium-emphasis">
                {{ selectedProduct.key_count }} keys total
              </div>
            </div>
          </div>
          <VBtn
            icon
            variant="text"
            @click="closeProductKeysDialog"
          >
            <VIcon icon="tabler-x" />
          </VBtn>
        </VCardTitle>
        <VDivider />
        <VCardText style="max-height: 600px;">
          <!-- Loading State -->
          <div
            v-if="productKeysLoading"
            class="text-center py-8"
          >
            <VProgressCircular
              indeterminate
              color="primary"
              size="64"
            />
            <p class="mt-4">
              Đang tải keys...
            </p>
          </div>

          <!-- Keys Table -->
          <VTable
            v-else-if="productKeys.length > 0"
            density="comfortable"
          >
            <thead>
              <tr>
                <th class="text-left">
                  #
                </th>
                <th class="text-left">
                  Product Key
                </th>
                <th class="text-center">
                  Remaining
                </th>
                <th class="text-center">
                  Status
                </th>
                <th class="text-center">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(key, index) in productKeys"
                :key="key.id"
              >
                <td>{{ (productKeysPage - 1) * productKeysPageSize + index + 1 }}</td>
                <td>
                  <code class="text-body-2">{{ key.keyname_with_dash }}</code>
                </td>
                <td class="text-center">
                  <VChip
                    :color="getStatusColor(key.remaining)"
                    size="small"
                    variant="tonal"
                  >
                    {{ key.remaining.toLocaleString() }}
                  </VChip>
                </td>
                <td class="text-center">
                  <VChip
                    :color="getBlockedColor(key.blocked)"
                    size="small"
                  >
                    {{ key.blocked === 1 ? 'Blocked' : 'Active' }}
                  </VChip>
                </td>
                <td class="text-center">
                  <VBtn
                    icon
                    variant="text"
                    size="small"
                    @click="showKeyDetails(key)"
                  >
                    <VIcon icon="tabler-eye" />
                  </VBtn>
                </td>
              </tr>
            </tbody>
          </VTable>

          <!-- Pagination -->
          <VDivider class="mt-4" />
          <div
            v-if="productKeys.length > 0"
            class="d-flex align-center justify-space-between flex-wrap gap-4 pa-4"
          >
            <div class="d-flex align-center gap-3">
              <div class="text-body-2 text-medium-emphasis">
                Hiển thị {{ productKeysTotalResults === 0 ? 0 : ((productKeysPage - 1) * productKeysPageSize) + 1 }} - {{ Math.min(((productKeysPage - 1) * productKeysPageSize) + productKeys.length, productKeysTotalResults) }} trong tổng số {{ productKeysTotalResults }} kết quả
              </div>
              <VSelect
                v-model="productKeysPageSize"
                :items="productKeysPageSizeOptions"
                variant="outlined"
                density="compact"
                hide-details
                style="max-width: 100px;"
                @update:model-value="handleProductKeysPageSizeChange"
              />
            </div>
            <VPagination
              v-model="productKeysPage"
              :length="productKeysTotalPages"
              :total-visible="7"
              @update:model-value="handleProductKeysPageChange"
            />
          </div>

          <!-- Empty State -->
          <div
            v-else
            class="text-center py-8"
          >
            <VIcon
              icon="tabler-inbox-off"
              size="64"
              color="disabled"
            />
            <p class="mt-4 text-disabled">
              Không tìm thấy keys nào
            </p>
          </div>
        </VCardText>
        <VDivider />
        <VCardActions class="px-6 py-4">
          <VChip
            v-if="!productKeysLoading"
            color="primary"
            variant="tonal"
          >
            {{ productKeysTotalResults }} keys total
          </VChip>
          <VChip
            v-if="!productKeysLoading && productKeysTotalPages > 1"
            color="info"
            variant="tonal"
          >
            Page {{ productKeysPage }} / {{ productKeysTotalPages }}
          </VChip>
          <VSpacer />
          <VBtn
            color="primary"
            variant="elevated"
            @click="closeProductKeysDialog"
          >
            Đóng
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

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
