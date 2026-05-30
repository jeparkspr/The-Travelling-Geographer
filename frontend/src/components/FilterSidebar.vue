<template>
  <div class="filter-sidebar" :class="{ 'mobile-open': mobileOpen }">
    <div class="filter-header">
      <h3>Filters</h3>
      <Button
        icon="pi pi-times"
        text
        @click="emit('close')"
        class="close-btn"
      />
    </div>

    <div class="filter-content">
      <!-- Search -->
      <div class="filter-group">
        <label>Search</label>
        <InputText
          v-model="localFilters.search"
          placeholder="Search destinations..."
          class="w-full"
        />
      </div>

      <!-- Ownership -->
      <div class="filter-group">
        <label>Ownership</label>
        <Select
          v-model="localFilters.ownership"
          :options="ownershipOptions"
          option-label="label"
          option-value="value"
          class="w-full"
        />
      </div>

      <!-- Status -->
      <div class="filter-group">
        <label>Status</label>
        <MultiSelect
          v-model="localFilters.status"
          :options="statusOptions"
          option-label="label"
          option-value="value"
          placeholder="All statuses"
          class="w-full"
          display="chip"
        />
      </div>

      <!-- Country -->
      <div v-if="countries.length" class="filter-group">
        <label>Country</label>
        <MultiSelect
          v-model="localFilters.country"
          :options="countries"
          placeholder="All countries"
          class="w-full"
          display="chip"
        />
      </div>

      <!-- Region -->
      <div v-if="regions.length" class="filter-group">
        <label>Region</label>
        <MultiSelect
          v-model="localFilters.region"
          :options="regions"
          placeholder="All regions"
          class="w-full"
          display="chip"
        />
      </div>

      <!-- Tags -->
      <div class="filter-group">
        <label>Tags</label>
        <MultiSelect
          v-model="localFilters.tags"
          :options="tags"
          placeholder="Select tags"
          class="w-full"
          display="chip"
        />
      </div>

      <!-- Priority -->
      <div class="filter-group">
        <label>Priority</label>
        <MultiSelect
          v-model="localFilters.priority"
          :options="priorityOptions"
          option-label="label"
          option-value="value"
          placeholder="All priorities"
          class="w-full"
          display="chip"
        />
      </div>

      <!-- Best Season -->
      <div class="filter-group">
        <label>Best Season</label>
        <MultiSelect
          v-model="localFilters.best_season"
          :options="seasonOptions"
          option-label="label"
          option-value="value"
          placeholder="All seasons"
          class="w-full"
          display="chip"
        />
      </div>

      <!-- Rating -->
      <div class="filter-group">
        <label>Rating</label>
        <MultiSelect
          v-model="localFilters.rating"
          :options="ratingOptions"
          option-label="label"
          option-value="value"
          placeholder="Any rating"
          class="w-full"
          display="chip"
        />
      </div>

      <!-- No Cover Photo -->
      <div class="filter-group">
        <div class="checkbox-filter">
          <Checkbox
            v-model="localFilters.noCover"
            :binary="true"
            inputId="noCover"
          />
          <label for="noCover">No cover photo</label>
        </div>
      </div>

      <!-- Custom Fields -->
      <div v-for="field in customFields" :key="field.id" class="filter-group">
        <label>{{ field.name }}</label>
        <InputText
          v-if="field.field_type === 'text'"
          :model-value="localFilters[`custom_${field.id}`]"
          @update:model-value="updateCustomFilter(field.id, $event)"
          class="w-full"
        />
        <Dropdown
          v-else-if="field.field_type === 'select'"
          :model-value="localFilters[`custom_${field.id}`]"
          @update:model-value="updateCustomFilter(field.id, $event)"
          :options="field.options"
          class="w-full"
        />
      </div>

      <!-- Buttons -->
      <div class="filter-actions">
        <Button
          label="Clear Filters"
          severity="secondary"
          @click="clearAllFilters"
          class="w-full"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useSettingsStore } from '@/stores/settings'

const settingsStore = useSettingsStore()

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  },
  tags: {
    type: Array,
    default: () => []
  },
  countries: {
    type: Array,
    default: () => []
  },
  regions: {
    type: Array,
    default: () => []
  },
  customFields: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'apply', 'clear', 'close'])

const mobileOpen = ref(false)

const ownershipOptions = [
  { label: 'All Destinations', value: 'all' },
  { label: 'My Destinations', value: 'mine' },
  { label: 'Shared with Me', value: 'shared' },
  { label: 'Shared by Me', value: 'shared_by_me' }
]

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

const seasonOptions = [
  { label: 'Spring', value: 'Spring' },
  { label: 'Summer', value: 'Summer' },
  { label: 'Fall', value: 'Fall' },
  { label: 'Winter', value: 'Winter' }
]

const ratingOptions = [
  { label: 'No Rating', value: 0 },
  { label: '1 Star', value: 1 },
  { label: '2 Stars', value: 2 },
  { label: '3 Stars', value: 3 },
  { label: '4 Stars', value: 4 },
  { label: '5 Stars', value: 5 }
]

const localFilters = ref({
  ownership: props.modelValue?.ownership || 'all',
  status: props.modelValue?.status || [],
  country: props.modelValue?.country || [],
  region: props.modelValue?.region || [],
  tags: props.modelValue?.tags || [],
  priority: props.modelValue?.priority || [],
  best_season: props.modelValue?.best_season || [],
  rating: props.modelValue?.rating || [],
  search: props.modelValue?.search || '',
  noCover: settingsStore.filterNoCover
})

watch(() => localFilters.value.noCover, (val) => {
  settingsStore.setFilterNoCover(val)
})

const updateCustomFilter = (fieldId, value) => {
  localFilters.value[`custom_${fieldId}`] = value
}

const applyFilters = () => {
  emit('update:modelValue', localFilters.value)
  emit('apply')
  mobileOpen.value = false
}

const clearAllFilters = () => {
  localFilters.value = {
    ownership: 'all',
    status: [],
    country: [],
    region: [],
    tags: [],
    priority: [],
    best_season: [],
    rating: [],
    search: '',
    noCover: false
  }
  emit('update:modelValue', localFilters.value)
  emit('clear')
  mobileOpen.value = false
}

let debounceTimer = null

watch(
  localFilters,
  () => {
    clearTimeout(debounceTimer)
    debounceTimer = setTimeout(() => {
      emit('update:modelValue', { ...localFilters.value })
      emit('apply')
    }, 300)
  },
  { deep: true }
)

watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal) {
      localFilters.value = { ...newVal }
    }
  }
)
</script>

<style scoped>
.filter-sidebar {
  background: var(--color-bg-elevated);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  width: 280px;
  height: 100%;
  overflow-y: auto;
}

.filter-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  border-bottom: 1px solid var(--color-border);
}

.filter-header h3 {
  margin: 0;
  font-size: 1.125rem;
}

.close-btn {
  display: none;
}

.filter-content {
  flex: 1;
  padding: 1rem;
  overflow-y: auto;
}

.filter-group {
  margin-bottom: 1rem;
}

.filter-group label {
  display: block;
  font-weight: 600;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
  color: var(--color-text-bright);
}

.filter-group :deep(.p-inputtext),
.filter-group :deep(.p-dropdown),
.filter-group :deep(.p-multiselect) {
  width: 100%;
  font-size: 0.875rem;
}

.checkbox-filter {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.checkbox-filter label {
  font-weight: normal;
  font-size: 0.875rem;
  cursor: pointer;
}

.filter-actions {
  border-top: 1px solid var(--color-border);
  padding-top: 1rem;
  margin-top: 1rem;
}

.w-full {
  width: 100%;
}

.mb-2 {
  margin-bottom: 0.5rem;
}

@media (max-width: 768px) {
  .close-btn {
    display: block;
  }

  .filter-header {
    padding: 1.5rem 1rem;
  }
}
</style>
