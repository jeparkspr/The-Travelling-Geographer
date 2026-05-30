<template>
  <div class="destination-list">
    <div class="toolbar-section">
      <Toolbar>
        <template #start>
          <h1 class="page-title">Destinations</h1>
        </template>
        <template #end>
          <div class="toolbar-actions">
            <Select
              v-if="viewMode === 'grid'"
              v-model="sortBy"
              :options="sortOptions"
              optionLabel="label"
              optionValue="value"
              class="sort-select"
            />
            <SelectButton
              v-model="viewMode"
              :options="viewOptions"
              optionLabel="icon"
              optionValue="value"
              dataKey="value"
              class="view-toggle"
            >
              <template #option="slotProps">
                <i :class="slotProps.option.icon" v-tooltip.bottom="slotProps.option.title"></i>
              </template>
            </SelectButton>
            <Button
              v-if="isMobile"
              icon="pi pi-filter"
              @click="filterOpen = !filterOpen"
              :severity="filterOpen ? 'primary' : 'secondary'"
              text
            />
            <Button
              v-if="viewMode === 'grid'"
              :icon="selectMode ? 'pi pi-times' : 'pi pi-check-square'"
              :label="isMobile ? '' : (selectMode ? 'Cancel' : 'Select')"
              :severity="selectMode ? 'danger' : 'secondary'"
              text
              @click="toggleSelectMode"
            />
            <router-link to="/destinations/new">
              <Button
                icon="pi pi-plus"
                :label="isMobile ? '' : 'Add Destination'"
                severity="success"
              />
            </router-link>
          </div>
        </template>
      </Toolbar>
    </div>

    <div class="content-container">

      <div v-if="isMobile && filterOpen" class="filter-overlay" @click="filterOpen = false"></div>
      <FilterSidebar
        v-if="!isMobile || filterOpen"
        v-model="filters"
        :tags="tags"
        :countries="countries"
        :regions="regions"
        :custom-fields="customFields"
        @apply="applyFilters"
        @clear="clearFilters"
        @close="filterOpen = false"
        class="sidebar"
        :class="{ 'sidebar-mobile-open': isMobile && filterOpen }"
      />

      <div class="main-content">
        <!-- Grid View -->
        <div v-if="viewMode === 'grid'" class="grid-container">
          <div v-if="filteredDestinations.length" class="destinations-grid">
            <DestinationCard
              v-for="destination in visibleDestinations"
              :key="destination.id"
              :destination="destination"
              :selectable="selectMode"
              :selected="selectedIds.has(destination.id)"
              @toggle-select="toggleSelection"
            />
          </div>
          <div v-if="hasMore" ref="scrollSentinel" class="scroll-sentinel">
            <i class="pi pi-spin pi-spinner"></i> Loading more...
          </div>
          <div v-if="!filteredDestinations.length" class="empty-state">
            <i class="pi pi-inbox"></i>
            <p>No destinations found</p>
            <router-link to="/destinations/new" class="btn-link">
              Create your first destination
            </router-link>
          </div>
        </div>

        <!-- Table View -->
        <div v-else class="table-container">
          <DataTable
            v-if="filteredDestinations.length"
            :value="sortedDestinations"
            :rows="100"
            :paginator="true"
            :rowsPerPageOptions="[20, 50, 100]"
            responsive-layout="scroll"
            striped-rows
            editMode="cell"
            @cell-edit-complete="onCellEditComplete"
            :global-filter-fields="['name', 'country', 'city']"
            class="destinations-table"
          >
            <Column field="name" header="Name" sortable>
              <template #body="{ data }">
                <router-link :to="`/destinations/${data.id}`" class="name-link">
                  {{ data.name }}
                </router-link>
              </template>
              <template #editor="{ data, field }">
                <InputText v-model="data[field]" autofocus class="cell-editor-input" />
              </template>
            </Column>
            <Column field="owner_name" header="Owner" sortable>
              <template #body="{ data }">
                <span v-if="data.owner_id !== currentUserId" class="owner-tag">
                  <i class="pi pi-user"></i> {{ data.owner_name }}
                </span>
                <span v-else class="owner-tag owner-me">Me</span>
              </template>
            </Column>
            <Column field="country" header="Country" sortable>
              <template #editor="{ data, field }">
                <InputText v-model="data[field]" autofocus class="cell-editor-input" />
              </template>
            </Column>
            <Column field="city" header="City" sortable>
              <template #editor="{ data, field }">
                <InputText v-model="data[field]" autofocus class="cell-editor-input" />
              </template>
            </Column>
            <Column field="status" header="Status" sortable>
              <template #body="{ data }">
                <StatusBadge :status="data.status" />
              </template>
              <template #editor="{ data, field }">
                <Select
                  v-model="data[field]"
                  :options="statusOptions"
                  optionLabel="label"
                  optionValue="value"
                  class="cell-editor-select"
                />
              </template>
            </Column>
            <Column field="priority" header="Priority" sortable>
              <template #body="{ data }">
                <span v-if="data.priority" class="priority-badge" :class="`priority-${data.priority}`">
                  {{ getPriorityLabel(data.priority) }}
                </span>
              </template>
              <template #editor="{ data, field }">
                <Select
                  v-model="data[field]"
                  :options="priorityOptions"
                  optionLabel="label"
                  optionValue="value"
                  :showClear="true"
                  placeholder="None"
                  class="cell-editor-select"
                />
              </template>
            </Column>
            <Column field="rating" header="Rating" sortable>
              <template #body="{ data }">
                <Rating v-if="data.rating" v-model="data.rating" :cancel="false" readonly />
              </template>
              <template #editor="{ data, field }">
                <Rating v-model="data[field]" :cancel="true" />
              </template>
            </Column>
            <Column header="Actions">
              <template #body="{ data }">
                <router-link :to="`/destinations/${data.id}/edit`" class="action-link">
                  <i class="pi pi-pencil"></i>
                </router-link>
              </template>
            </Column>
          </DataTable>

          <div v-else class="empty-state">
            <i class="pi pi-inbox"></i>
            <p>No destinations found</p>
            <router-link to="/destinations/new" class="btn-link">
              Create your first destination
            </router-link>
          </div>
        </div>
      </div>
    </div>
    <!-- Selection Action Bar -->
    <div v-if="selectMode && selectedIds.size > 0" class="bulk-action-bar">
      <div class="action-bar-left">
        <span class="action-bar-count">{{ selectedIds.size }} selected</span>
        <a class="action-bar-link" @click.prevent="selectAll">Select all</a>
        <a class="action-bar-link" @click.prevent="deselectAll">Deselect all</a>
      </div>
      <div class="action-bar-right">
        <Button icon="pi pi-pencil" label="Edit" severity="info" size="small" @click="openBulkEditDialog" />
        <Button icon="pi pi-share-alt" label="Share" severity="info" size="small" @click="openBulkShareDialog" />
        <Button icon="pi pi-trash" label="Delete" severity="danger" size="small" @click="openBulkDeleteDialog" />
      </div>
    </div>

    <!-- Bulk Edit Dialog -->
    <Dialog
      v-model:visible="bulkEditDialogVisible"
      header="Edit Selected Destinations"
      :modal="true"
      :style="{ width: '90vw', maxWidth: '480px' }"
    >
      <div class="bulk-edit-form">
        <p class="bulk-edit-hint">Only enabled fields will be updated. Leave a field disabled to keep existing values.</p>

        <div class="bulk-field">
          <div class="bulk-field-header">
            <Checkbox v-model="bulkEdit.statusEnabled" :binary="true" inputId="be-status" />
            <label for="be-status">Status</label>
          </div>
          <Select
            v-model="bulkEdit.status"
            :options="statusOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Select status..."
            class="w-full"
            :disabled="!bulkEdit.statusEnabled"
          />
        </div>

        <div class="bulk-field">
          <div class="bulk-field-header">
            <Checkbox v-model="bulkEdit.priorityEnabled" :binary="true" inputId="be-priority" />
            <label for="be-priority">Priority</label>
          </div>
          <Select
            v-model="bulkEdit.priority"
            :options="priorityOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Select priority..."
            class="w-full"
            :disabled="!bulkEdit.priorityEnabled"
          />
        </div>

        <div class="bulk-field">
          <div class="bulk-field-header">
            <Checkbox v-model="bulkEdit.tagsEnabled" :binary="true" inputId="be-tags" />
            <label for="be-tags">Tags</label>
            <div v-if="bulkEdit.tagsEnabled" class="tag-mode-toggle">
              <SelectButton
                v-model="bulkEdit.tagMode"
                :options="[
                  { label: 'Add', value: 'add' },
                  { label: 'Replace', value: 'replace' }
                ]"
                optionLabel="label"
                optionValue="value"
                :allowEmpty="false"
                class="tag-mode-btn"
              />
              <i
                class="pi pi-info-circle tag-mode-info"
                v-tooltip.top="bulkEdit.tagMode === 'add'
                  ? 'Add: appends these tags to each destination\'s existing tags'
                  : 'Replace: removes all existing tags from selected destinations and sets only these tags'"
              ></i>
            </div>
          </div>
          <InputText
            v-model="bulkEdit.tagsText"
            placeholder="Enter tags separated by commas..."
            class="w-full"
            :disabled="!bulkEdit.tagsEnabled"
          />
        </div>
      </div>
      <template #footer>
        <Button label="Cancel" severity="secondary" text @click="bulkEditDialogVisible = false" />
        <Button label="Apply" icon="pi pi-check" @click="submitBulkEdit" :loading="bulkActionLoading"
          :disabled="!bulkEdit.statusEnabled && !bulkEdit.priorityEnabled && !bulkEdit.tagsEnabled" />
      </template>
    </Dialog>

    <!-- Bulk Share Dialog -->
    <Dialog
      v-model:visible="bulkShareDialogVisible"
      header="Share Selected Destinations"
      :modal="true"
      :style="{ width: '90vw', maxWidth: '480px' }"
    >
      <div class="bulk-share-form">
        <p class="bulk-edit-hint">Share {{ selectedIds.size }} destination(s) with a user.</p>
        <div class="field">
          <label>User</label>
          <Select
            v-model="bulkShare.userId"
            :options="shareableUsers"
            optionLabel="display_name"
            optionValue="id"
            placeholder="Select user..."
            class="w-full"
            :loading="shareableUsersLoading"
          >
            <template #option="{ option }">
              <div>{{ option.display_name }} <span class="share-email-hint">{{ option.email }}</span></div>
            </template>
          </Select>
        </div>
        <div class="field">
          <label>Permission</label>
          <Select
            v-model="bulkShare.tier"
            :options="tierOptions"
            optionLabel="label"
            optionValue="value"
            class="w-full"
          />
        </div>
      </div>
      <template #footer>
        <Button label="Cancel" severity="secondary" text @click="bulkShareDialogVisible = false" />
        <Button label="Share" icon="pi pi-share-alt" @click="submitBulkShare" :loading="bulkActionLoading"
          :disabled="!bulkShare.userId" />
      </template>
    </Dialog>

    <!-- Bulk Delete Confirmation Dialog -->
    <Dialog
      v-model:visible="bulkDeleteDialogVisible"
      header="Delete Selected Destinations"
      :modal="true"
      :style="{ width: '90vw', maxWidth: '450px' }"
    >
      <div class="bulk-delete-form">
        <p class="delete-warning">
          <i class="pi pi-exclamation-triangle"></i>
          You are about to permanently delete <strong>{{ selectedIds.size }}</strong> destination(s) and all their associated media, journal entries, and links. This cannot be undone.
        </p>
      </div>
      <template #footer>
        <Button label="Cancel" severity="secondary" text @click="bulkDeleteDialogVisible = false" />
        <Button label="Delete" icon="pi pi-trash" severity="danger" @click="submitBulkDelete" :loading="bulkActionLoading" />
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import { useDestinationsStore } from '@/stores/destinations'
import { useCustomFieldsStore } from '@/stores/customFields'
import { useSettingsStore } from '@/stores/settings'
import { useApi } from '@/composables/useApi'
import DestinationCard from '@/components/DestinationCard.vue'
import FilterSidebar from '@/components/FilterSidebar.vue'
import StatusBadge from '@/components/StatusBadge.vue'

const route = useRoute()
const toast = useToast()
const destinationsStore = useDestinationsStore()
const customFieldsStore = useCustomFieldsStore()
const settingsStore = useSettingsStore()
const { getFilterOptions, getShareableUsers, bulkEditDestinations, bulkShareDestinations, bulkDeleteDestinations } = useApi()

const countries = ref([])
const regions = ref([])

const viewMode = ref('grid')
const viewOptions = [
  { icon: 'pi pi-bars', value: 'table', title: 'List View' },
  { icon: 'pi pi-th-large', value: 'grid', title: 'Grid View' }
]
const filterOpen = ref(!!(route.query.status || route.query.tag))
const isMobile = ref(false)
const savedSort = (() => { try { return localStorage.getItem('tg-grid-sort') } catch { return null } })()
const sortBy = ref(savedSort || 'status')

const sortOptions = [
  { label: 'Status', value: 'status' },
  { label: 'Priority', value: 'priority_desc' },
  { label: 'Star Rating', value: 'rating_desc' },
  { label: 'Destination Name', value: 'name' },
  { label: 'Country', value: 'country' },
  { label: 'City', value: 'city' }
]

watch(sortBy, (val) => {
  try { localStorage.setItem('tg-grid-sort', val) } catch { /* ignore */ }
})

const statusOrder = { suggested: 0, want_to_visit: 1, researching: 2, planned: 3, visited: 4, archived: 5 }
const priorityOrder = { high: 0, medium: 1, low: 2 }

// Infinite scroll
const PAGE_SIZE = 20
const visibleCount = ref(PAGE_SIZE)
const scrollSentinel = ref(null)
let observer = null

// Use store filters so they survive navigation
const filters = computed({
  get: () => destinationsStore.filters,
  set: (val) => { destinationsStore.filters = val }
})

// Override with query params when arriving via a direct link (e.g. Overview status click)
if (route.query.status) {
  filters.value = { ...filters.value, status: [route.query.status] }
}
if (route.query.tag) {
  filters.value = { ...filters.value, tags: [route.query.tag] }
}

// Current user for ownership filtering
const currentUserId = (() => {
  try { return JSON.parse(localStorage.getItem('user') || '{}').id || null }
  catch { return null }
})()

const tags = computed(() => destinationsStore.tags)
const customFields = computed(() => customFieldsStore.fields)
const destinations = computed(() => {
  const all = destinationsStore.destinations
  if (settingsStore.showArchived) return all
  return all.filter(d => d.status !== 'archived')
})

const filteredDestinations = computed(() => {
  return destinations.value.filter(dest => {
    // Ownership filter
    if (filters.value.ownership === 'mine' && dest.owner_id !== currentUserId) {
      return false
    }
    if (filters.value.ownership === 'shared' && dest.owner_id === currentUserId) {
      return false
    }
    if (filters.value.ownership === 'shared_by_me' && (dest.owner_id !== currentUserId || !dest.shared_with_count)) {
      return false
    }

    if (filters.value.status.length > 0 && !filters.value.status.includes(dest.status)) {
      return false
    }

    if (filters.value.country?.length > 0 && !filters.value.country.includes(dest.country)) {
      return false
    }

    if (filters.value.region?.length > 0 && !filters.value.region.includes(dest.region)) {
      return false
    }

    if (filters.value.tags.length > 0) {
      const destTags = dest.tags || []
      const hasTag = filters.value.tags.some(tag => destTags.includes(tag))
      if (!hasTag) return false
    }

    if (filters.value.priority.length > 0 && !filters.value.priority.includes(dest.priority)) {
      return false
    }

    if (filters.value.best_season.length > 0) {
      const destSeasons = dest.best_season || []
      const hasSeason = filters.value.best_season.some(season => destSeasons.includes(season))
      if (!hasSeason) return false
    }

    // Rating filter (multiselect: 0 = no rating, 1–5 = star values)
    if (filters.value.rating?.length > 0) {
      const hasNoRating = filters.value.rating.includes(0)
      const starValues = filters.value.rating.filter(v => v > 0)
      const matchesNoRating = hasNoRating && dest.rating == null
      const matchesStar = starValues.length > 0 && starValues.includes(dest.rating)
      if (!matchesNoRating && !matchesStar) return false
    }

    if (filters.value.noCover && dest.cover_media_id) {
      return false
    }

    if (filters.value.search) {
      const query = filters.value.search.toLowerCase()
      const matches =
        dest.name?.toLowerCase().includes(query) ||
        dest.country?.toLowerCase().includes(query) ||
        dest.city?.toLowerCase().includes(query) ||
        dest.tags?.some(t => t.toLowerCase().includes(query))
      if (!matches) return false
    }

    return true
  })
})

const sortedDestinations = computed(() => {
  const list = [...filteredDestinations.value]
  const key = sortBy.value
  list.sort((a, b) => {
    switch (key) {
      case 'status':
        return (statusOrder[a.status] ?? 99) - (statusOrder[b.status] ?? 99)
      case 'priority_desc':
        return (priorityOrder[a.priority] ?? 99) - (priorityOrder[b.priority] ?? 99)
      case 'rating_desc':
        return (b.rating || 0) - (a.rating || 0)
      case 'name':
        return (a.name || '').localeCompare(b.name || '')
      case 'country':
        return (a.country || '').localeCompare(b.country || '')
      case 'city':
        return (a.city || '').localeCompare(b.city || '')
      default:
        return 0
    }
  })
  return list
})

const visibleDestinations = computed(() => {
  return sortedDestinations.value.slice(0, visibleCount.value)
})

const hasMore = computed(() => visibleCount.value < sortedDestinations.value.length)

// Reset visible count when filters change
watch(filters, () => {
  visibleCount.value = PAGE_SIZE
}, { deep: true })

const loadMore = () => {
  if (hasMore.value) {
    visibleCount.value += PAGE_SIZE
  }
}

const loadUntilOffscreen = () => {
  nextTick(() => {
    if (!scrollSentinel.value || !hasMore.value) return
    const rect = scrollSentinel.value.getBoundingClientRect()
    if (rect.top < window.innerHeight + 200) {
      loadMore()
      loadUntilOffscreen()
    }
  })
}

const setupObserver = () => {
  if (observer) observer.disconnect()
  observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting && hasMore.value) {
      loadMore()
      loadUntilOffscreen()
    }
  }, { rootMargin: '200px' })

  nextTick(() => {
    if (scrollSentinel.value) {
      observer.observe(scrollSentinel.value)
    }
  })
}

const getPriorityLabel = (priority) => {
  const labels = { low: 'Low', medium: 'Medium', high: 'High' }
  return labels[priority] || priority
}

const statusOptions = [
  { label: 'Suggested', value: 'suggested' },
  { label: 'Want to Visit', value: 'want_to_visit' },
  { label: 'Researching', value: 'researching' },
  { label: 'Planned', value: 'planned' },
  { label: 'Visited', value: 'visited' },
  { label: 'Archived', value: 'archived' }
]

const priorityOptions = [
  { label: 'Low', value: 'low' },
  { label: 'Medium', value: 'medium' },
  { label: 'High', value: 'high' }
]

const onCellEditComplete = async (event) => {
  const { data, newValue, field } = event
  const oldValue = data[field]

  // For name, don't allow empty
  if (field === 'name' && (!newValue || !newValue.trim())) {
    event.preventDefault()
    return
  }

  // No change — skip the API call
  if (newValue === oldValue) return

  // Optimistically update the local data
  data[field] = newValue

  try {
    await destinationsStore.updateCurrentDestination(data.id, { [field]: newValue })
    toast.add({
      severity: 'success',
      summary: 'Updated',
      detail: `${field.charAt(0).toUpperCase() + field.slice(1)} saved`,
      life: 2000
    })
  } catch (error) {
    // Revert on failure
    data[field] = oldValue
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to save change',
      life: 4000
    })
  }
}

const applyFilters = () => {
  if (isMobile.value) {
    filterOpen.value = false
  }
}

const clearFilters = () => {
  destinationsStore.clearFilters()
  if (isMobile.value) {
    filterOpen.value = false
  }
}

const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
  if (window.innerWidth >= 768) {
    filterOpen.value = false
  }
}

// Selection mode
const selectMode = ref(false)
const selectedIds = ref(new Set())

const toggleSelectMode = () => {
  selectMode.value = !selectMode.value
  if (!selectMode.value) selectedIds.value = new Set()
}

const toggleSelection = (id) => {
  const next = new Set(selectedIds.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  selectedIds.value = next
}

const selectAll = () => {
  selectedIds.value = new Set(sortedDestinations.value.map(d => d.id))
}

const deselectAll = () => {
  selectedIds.value = new Set()
}

// Exit selection mode when switching views
watch(viewMode, () => {
  selectMode.value = false
  selectedIds.value = new Set()
})

// Bulk action shared state
const bulkActionLoading = ref(false)
const shareableUsers = ref([])
const shareableUsersLoading = ref(false)

const tierOptions = [
  { label: 'View', value: 'view' },
  { label: 'Contribute', value: 'contribute' },
  { label: 'Edit', value: 'edit' },
  { label: 'Manage', value: 'manage' }
]

const loadShareableUsers = async () => {
  if (shareableUsers.value.length) return
  shareableUsersLoading.value = true
  try {
    const res = await getShareableUsers()
    shareableUsers.value = res.data || []
  } catch { /* ignore */ }
  finally { shareableUsersLoading.value = false }
}

// Bulk Edit
const bulkEditDialogVisible = ref(false)
const bulkEdit = ref({
  statusEnabled: false, status: null,
  priorityEnabled: false, priority: null,
  tagsEnabled: false, tagMode: 'add', tagsText: ''
})

const openBulkEditDialog = () => {
  bulkEdit.value = {
    statusEnabled: false, status: null,
    priorityEnabled: false, priority: null,
    tagsEnabled: false, tagMode: 'add', tagsText: ''
  }
  bulkEditDialogVisible.value = true
}

const submitBulkEdit = async () => {
  const payload = { destination_ids: [...selectedIds.value] }
  if (bulkEdit.value.statusEnabled && bulkEdit.value.status) payload.status = bulkEdit.value.status
  if (bulkEdit.value.priorityEnabled && bulkEdit.value.priority) payload.priority = bulkEdit.value.priority
  if (bulkEdit.value.tagsEnabled) {
    const tags = bulkEdit.value.tagsText.split(',').map(t => t.trim()).filter(Boolean)
    if (tags.length) {
      payload.tags = tags
      payload.tag_mode = bulkEdit.value.tagMode
    }
  }

  bulkActionLoading.value = true
  try {
    const res = await bulkEditDestinations(payload)
    toast.add({ severity: 'success', summary: 'Updated', detail: `${res.data.updated} destination(s) updated`, life: 3000 })
    bulkEditDialogVisible.value = false
    selectedIds.value = new Set()
    selectMode.value = false
    await destinationsStore.fetchDestinations({ page_size: 9999 })
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.response?.data?.detail || 'Bulk edit failed', life: 4000 })
  } finally {
    bulkActionLoading.value = false
  }
}

// Bulk Share
const bulkShareDialogVisible = ref(false)
const bulkShare = ref({ userId: null, tier: 'view' })

const openBulkShareDialog = async () => {
  bulkShare.value = { userId: null, tier: 'view' }
  bulkShareDialogVisible.value = true
  await loadShareableUsers()
}

const submitBulkShare = async () => {
  bulkActionLoading.value = true
  try {
    const res = await bulkShareDestinations({
      destination_ids: [...selectedIds.value],
      user_id: bulkShare.value.userId,
      permission_tier: bulkShare.value.tier
    })
    toast.add({ severity: 'success', summary: 'Shared', detail: `${res.data.shared} destination(s) shared`, life: 3000 })
    bulkShareDialogVisible.value = false
    selectedIds.value = new Set()
    selectMode.value = false
    await destinationsStore.fetchDestinations({ page_size: 9999 })
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.response?.data?.detail || 'Bulk share failed', life: 4000 })
  } finally {
    bulkActionLoading.value = false
  }
}

// Bulk Delete
const bulkDeleteDialogVisible = ref(false)

const openBulkDeleteDialog = () => {
  bulkDeleteDialogVisible.value = true
}

const submitBulkDelete = async () => {
  bulkActionLoading.value = true
  try {
    const res = await bulkDeleteDestinations({ destination_ids: [...selectedIds.value] })
    toast.add({ severity: 'success', summary: 'Deleted', detail: `${res.data.deleted} destination(s) deleted`, life: 3000 })
    bulkDeleteDialogVisible.value = false
    selectedIds.value = new Set()
    selectMode.value = false
    await destinationsStore.fetchDestinations({ page_size: 9999 })
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.response?.data?.detail || 'Bulk delete failed', life: 4000 })
  } finally {
    bulkActionLoading.value = false
  }
}

onMounted(async () => {
  checkMobile()
  window.addEventListener('resize', checkMobile)

  try {
    const [, , , filterOpts] = await Promise.all([
      destinationsStore.fetchDestinations({ page_size: 9999 }),
      destinationsStore.fetchTags(),
      customFieldsStore.fetchFields(),
      getFilterOptions()
    ])
    countries.value = filterOpts.data?.countries || []
    regions.value = filterOpts.data?.regions || []
  } catch (error) {
    console.error('Error loading data:', error)
  }

  setupObserver()
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
  if (observer) observer.disconnect()
})
</script>

<style scoped>
.destination-list {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.toolbar-section {
  background: var(--color-bg-elevated);
  border-bottom: 1px solid var(--color-border);
}

.toolbar-section :deep(.p-toolbar) {
  background: transparent;
  border: none;
  padding: 1rem;
  align-items: center;
  gap: 1rem;
}

.page-title {
  margin: 0;
  font-size: 1.875rem;
}

.view-toggle :deep(.p-button) {
  padding: 0.5rem 0.65rem;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  flex-wrap: wrap;
}

.sort-select {
  min-width: 200px;
  margin-right: 0.5rem;
}

.content-container {
  flex: 1;
  display: flex;
  position: relative;
}

.filter-overlay {
  display: none;
}

.sidebar {
  flex-shrink: 0;
}

.main-content {
  flex: 1;
  padding: 2rem;
  background: var(--color-bg);
  overflow-y: auto;
}

.grid-container {
  width: 100%;
}

.destinations-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1.5rem;
}

.table-container {
  width: 100%;
}

.destinations-table {
  background: var(--color-bg-elevated);
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.destinations-table :deep(.p-datatable-thead > tr > th) {
  background: var(--color-bg-light);
  border-bottom: 2px solid var(--color-border);
  font-weight: 600;
  color: var(--color-text-bright);
}

.destinations-table :deep(.p-datatable-tbody > tr) {
  border-bottom: 1px solid var(--color-border);
}

.destinations-table :deep(.p-datatable-tbody > tr:hover) {
  background: var(--color-bg-hover);
}

.name-link {
  color: var(--color-accent-hover);
  text-decoration: none;
  font-weight: 500;
}

.name-link:hover {
  text-decoration: underline;
}

.priority-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
}

.priority-low {
  background: rgba(147, 197, 253, 0.15);
  color: #93c5fd;
}

.priority-medium {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}

.priority-high {
  background: rgba(248, 113, 113, 0.15);
  color: #f87171;
}

/* Editable cell styles */
.cell-editor-input {
  width: 100%;
}

.cell-editor-select {
  width: 100%;
  min-width: 140px;
}

.destinations-table :deep(.p-datatable-tbody > tr > td.p-cell-editing) {
  padding: 0.25rem 0.5rem;
}

.destinations-table :deep(.p-datatable-tbody > tr > td) {
  cursor: pointer;
}

.destinations-table :deep(.p-datatable-tbody > tr > td:last-child) {
  cursor: default;
}

.action-link {
  color: var(--color-accent-hover);
  text-decoration: none;
  padding: 0.25rem;
}

.action-link:hover {
  color: var(--color-accent-hover);
}

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  color: var(--color-text-muted);
}

.empty-state i {
  font-size: 3rem;
  color: var(--color-text-muted);
  margin-bottom: 1rem;
  display: block;
}

.btn-link {
  display: inline-block;
  margin-top: 1rem;
  color: var(--color-accent-hover);
  text-decoration: none;
  font-weight: 500;
  padding: 0.5rem 1rem;
  border: 1px solid var(--color-accent-hover);
  border-radius: 0.375rem;
  transition: all 0.2s;
}

.btn-link:hover {
  background: var(--color-bg-hover);
}

.scroll-sentinel {
  text-align: center;
  padding: 2rem;
  color: var(--color-text-muted);
  font-size: 0.875rem;
}

/* Bulk Action Bar */
.bulk-action-bar {
  position: sticky;
  bottom: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1.5rem;
  margin: 0;
  background: var(--color-bg-elevated);
  border-top: 1px solid var(--color-border);
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.3);
}

.action-bar-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.action-bar-count {
  font-weight: 600;
  font-size: 0.9rem;
}

.action-bar-link {
  font-size: 0.8rem;
  color: var(--color-accent-hover);
  cursor: pointer;
  text-decoration: none;
}

.action-bar-link:hover {
  text-decoration: underline;
}

.action-bar-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* Bulk Edit Dialog */
.bulk-edit-hint {
  margin: 0 0 1.25rem 0;
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

.bulk-edit-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.bulk-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.bulk-field-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.bulk-field-header label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text);
}

.tag-mode-toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-left: auto;
}

.tag-mode-btn :deep(.p-button) {
  padding: 0.25rem 0.6rem;
  font-size: 0.75rem;
}

.tag-mode-info {
  color: var(--color-text-muted);
  font-size: 0.9rem;
  cursor: help;
}

/* Bulk Share Dialog */
.bulk-share-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.bulk-share-form .field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.bulk-share-form label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text);
}

.share-email-hint {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  margin-left: 0.25rem;
}

/* Bulk Delete Dialog */
.delete-warning {
  color: var(--color-text);
  line-height: 1.6;
}

.delete-warning i {
  color: #f59e0b;
  margin-right: 0.5rem;
}

.w-full {
  width: 100%;
}

.owner-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

.owner-tag.owner-me {
  color: var(--color-text-muted);
  font-style: italic;
}

@media (max-width: 768px) {
  .toolbar-section :deep(.p-toolbar) {
    flex-wrap: wrap;
    gap: 0.5rem;
    padding: 0.75rem;
  }

  .page-title {
    font-size: 1.25rem;
  }

  .toolbar-actions {
    gap: 0.15rem;
  }

  .sort-select {
    min-width: 140px;
    margin-right: 0;
  }

  .filter-overlay {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 998;
  }

  .sidebar-mobile-open {
    position: fixed;
    top: 0;
    left: 0;
    height: 100vh;
    z-index: 999;
    box-shadow: 4px 0 12px rgba(0, 0, 0, 0.4);
  }

  .destinations-grid {
    grid-template-columns: 1fr;
    gap: 1rem;
  }

  .main-content {
    padding: 1rem;
  }

  .destinations-table {
    font-size: 0.875rem;
  }
}
</style>
