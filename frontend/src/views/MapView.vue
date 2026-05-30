<template>
  <div class="map-view">
    <Toolbar class="search-toolbar">
      <template #start>
        <span class="search-label">
          <i class="pi pi-search"></i>
        </span>
        <InputText
          v-model="searchQuery"
          placeholder="Search destinations..."
          @keyup.enter="applyFilters"
          class="search-input"
        />
      </template>
      <template #end>
        <Button
          icon="pi pi-filter"
          @click="filterOpen = !filterOpen"
          :outlined="!filterOpen"
          :severity="filterOpen ? 'primary' : 'secondary'"
          label="Filters"
        />
      </template>
    </Toolbar>

    <div class="map-view-container">
      <FilterSidebar
        v-if="filterOpen"
        v-model="filters"
        :tags="tags"
        :countries="countries"
        :regions="regions"
        :custom-fields="customFields"
        @apply="applyFilters"
        @clear="clearFilters"
      />

      <div class="map-main">
        <MapComponent
          :destinations="filteredDestinations"
          :zoom="3"
          :show-layer-control="true"
          map-id="map-view"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useDestinationsStore } from '@/stores/destinations'
import { useCustomFieldsStore } from '@/stores/customFields'
import { useSettingsStore } from '@/stores/settings'
import { useApi } from '@/composables/useApi'
import MapComponent from '@/components/MapComponent.vue'
import FilterSidebar from '@/components/FilterSidebar.vue'

const destinationsStore = useDestinationsStore()
const customFieldsStore = useCustomFieldsStore()
const settingsStore = useSettingsStore()
const { getFilterOptions } = useApi()

const countries = ref([])
const regions = ref([])

const filterOpen = ref(false)
const searchQuery = ref('')

const filters = ref({
  status: [],
  country: [],
  region: [],
  tags: [],
  priority: [],
  best_season: [],
  rating: [],
  search: '',
  noCover: settingsStore.filterNoCover
})

const tags = computed(() => destinationsStore.tags)
const customFields = computed(() => customFieldsStore.fields)
const destinations = computed(() => {
  const all = destinationsStore.destinations
  if (settingsStore.showArchived) return all
  return all.filter(d => d.status !== 'archived')
})

const filteredDestinations = computed(() => {
  return destinations.value.filter(dest => {
    // Status filter
    if (filters.value.status.length > 0 && !filters.value.status.includes(dest.status)) {
      return false
    }

    // Country filter
    if (filters.value.country?.length > 0 && !filters.value.country.includes(dest.country)) {
      return false
    }

    // Region filter
    if (filters.value.region?.length > 0 && !filters.value.region.includes(dest.region)) {
      return false
    }

    // Tags filter
    if (filters.value.tags.length > 0) {
      const destTags = dest.tags || []
      const hasTag = filters.value.tags.some(tag => destTags.includes(tag))
      if (!hasTag) return false
    }

    // Priority filter
    if (filters.value.priority.length > 0 && !filters.value.priority.includes(dest.priority)) {
      return false
    }

    // Season filter
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

    // No cover photo filter
    if (filters.value.noCover && dest.cover_media_id) {
      return false
    }

    // Search filter
    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase()
      const matches =
        dest.name?.toLowerCase().includes(query) ||
        dest.country?.toLowerCase().includes(query) ||
        dest.city?.toLowerCase().includes(query) ||
        dest.description?.toLowerCase().includes(query)
      if (!matches) return false
    }

    return true
  })
})

const applyFilters = () => {
  filters.value.search = searchQuery.value
}

const clearFilters = () => {
  filters.value = {
    status: [],
    country: [],
    region: [],
    tags: [],
    priority: [],
    best_season: [],
    rating: [],
    search: ''
  }
  searchQuery.value = ''
}

onMounted(async () => {
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
})
</script>

<style scoped>
.map-view {
  height: calc(100vh - 64px);
  display: flex;
  flex-direction: column;
}

.search-toolbar {
  background: var(--color-bg-elevated);
  border-bottom: 1px solid var(--color-border);
  padding: 0.75rem 1rem;
  display: flex;
  gap: 1rem;
  align-items: center;
}

.search-label {
  color: var(--color-text-muted);
  font-size: 1rem;
}

.search-input {
  flex: 1;
  max-width: 400px;
}

.search-input :deep(.p-inputtext) {
  width: 100%;
}

.map-view-container {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.map-main {
  flex: 1;
  position: relative;
}

@media (max-width: 768px) {
  .search-toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .search-input {
    max-width: none;
  }
}
</style>
