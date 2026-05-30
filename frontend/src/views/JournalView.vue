<template>
  <div class="journal-view">
    <div class="container py-4">
      <h1 class="page-title">Journal</h1>

      <!-- Filters -->
      <div class="filter-bar">
        <div class="filter-group">
          <InputText
            v-model="filters.search"
            placeholder="Search entries..."
            class="filter-input"
          />
        </div>
        <div class="filter-group">
          <Dropdown
            v-model="filters.destination"
            :options="destinationOptions"
            option-label="name"
            option-value="id"
            placeholder="All destinations"
            class="filter-select"
            :show-clear="true"
          />
        </div>
        <div class="filter-group">
          <Calendar
            v-model="filters.startDate"
            placeholder="From date"
            date-format="yy-mm-dd"
            show-icon
            class="filter-input"
          />
        </div>
        <div class="filter-group">
          <Calendar
            ref="endDateRef"
            v-model="filters.endDate"
            placeholder="To date"
            date-format="yy-mm-dd"
            show-icon
            class="filter-input"
          />
        </div>
        <div class="filter-group filter-sort">
          <Button
            :icon="sortAsc ? 'pi pi-sort-amount-up' : 'pi pi-sort-amount-down'"
            :label="sortAsc ? 'Oldest First' : 'Newest First'"
            text
            size="small"
            @click="sortAsc = !sortAsc"
            v-tooltip.bottom="sortAsc ? 'Switch to newest first' : 'Switch to oldest first'"
          />
        </div>
      </div>

      <!-- Timeline -->
      <div v-if="filteredEntries.length" class="timeline">
        <div v-for="entry in filteredEntries" :key="entry.id" class="timeline-item">
          <div class="timeline-marker">
            <div class="marker-dot"></div>
          </div>
          <div class="timeline-content">
            <div class="entry-header">
              <div class="entry-title-group">
                <div class="entry-date-line">
                  <span class="entry-date">{{ formatDate(entry.entry_date) }}</span>
                  <span class="entry-date-sep">—</span>
                  <router-link
                    :to="`/destinations/${entry.destination_id}`"
                    class="destination-link"
                  >
                    {{ entry.destination_name || getDestinationName(entry.destination_id) }}
                  </router-link>
                </div>
                <h3 class="entry-title">{{ entry.title }}</h3>
              </div>
              <div class="entry-meta">
                <Rating
                  v-if="entry.rating"
                  v-model="entry.rating"
                  :cancel="false"
                  readonly
                />
              </div>
            </div>
            <div class="entry-body" v-html="entry.body_html || entry.body"></div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="empty-state">
        <i class="pi pi-book"></i>
        <p>No journal entries found</p>
        <router-link to="/destinations" class="btn-link">
          Add destinations and write in your journal
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useApi } from '@/composables/useApi'
import { format } from 'date-fns'

const { getAllJournalEntries } = useApi()

const allEntries = ref([])
const loading = ref(false)
const sortAsc = ref(false)
const endDateRef = ref(null)

const filters = ref({
  search: '',
  destination: null,
  startDate: null,
  endDate: null
})

// When start date is picked, pre-stage next day as end date and focus it
watch(() => filters.value.startDate, (newVal, oldVal) => {
  if (newVal && !oldVal) {
    const nextDay = new Date(newVal)
    nextDay.setDate(nextDay.getDate() + 1)
    filters.value.endDate = nextDay
    nextTick(() => {
      const el = endDateRef.value?.$el || endDateRef.value
      const input = el?.querySelector?.('input')
      if (input) input.focus()
    })
  }
})

const destinationOptions = computed(() => {
  const seen = new Map()
  for (const entry of allEntries.value) {
    if (!seen.has(entry.destination_id)) {
      seen.set(entry.destination_id, {
        id: entry.destination_id,
        name: entry.destination_name || 'Unknown'
      })
    }
  }
  return Array.from(seen.values()).sort((a, b) => a.name.localeCompare(b.name))
})

const filteredEntries = computed(() => {
  const filtered = allEntries.value.filter(entry => {
    // Search filter
    if (filters.value.search) {
      const query = filters.value.search.toLowerCase()
      const matches =
        entry.title?.toLowerCase().includes(query) ||
        entry.body?.toLowerCase().includes(query)
      if (!matches) return false
    }

    // Destination filter
    if (filters.value.destination && entry.destination_id !== filters.value.destination) {
      return false
    }

    // Date range filter
    if (filters.value.startDate) {
      const entryDate = new Date(entry.entry_date)
      if (entryDate < filters.value.startDate) return false
    }

    if (filters.value.endDate) {
      const entryDate = new Date(entry.entry_date)
      if (entryDate > filters.value.endDate) return false
    }

    return true
  })

  // Sort by date
  const direction = sortAsc.value ? 1 : -1
  return filtered.sort((a, b) => direction * (new Date(a.entry_date) - new Date(b.entry_date)))
})

const getDestinationName = (destinationId) => {
  const entry = allEntries.value.find(e => e.destination_id === destinationId)
  return entry?.destination_name || 'Unknown'
}

const formatDate = (date) => {
  try {
    return format(new Date(date), 'MMM d, yyyy')
  } catch {
    return 'Invalid date'
  }
}

onMounted(async () => {
  try {
    loading.value = true
    const response = await getAllJournalEntries()
    allEntries.value = response.data || []
  } catch (error) {
    console.error('Error loading journal entries:', error)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.journal-view {
  min-height: 100vh;
  background: var(--color-bg);
  padding-bottom: 4rem;
}

.page-title {
  margin: 0 0 2rem 0;
  font-size: 2.25rem;
  color: var(--color-text-bright);
}

.filter-bar {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
  background: var(--color-bg-elevated);
  padding: 1.5rem;
  border-radius: 0.5rem;
  border: 1px solid var(--color-border);
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.filter-input,
.filter-select {
  width: 100%;
}

.filter-input :deep(.p-inputtext),
.filter-select :deep(.p-dropdown) {
  width: 100%;
  font-size: 0.875rem;
}

.timeline {
  position: relative;
  padding: 0;
}

.timeline::before {
  content: '';
  position: absolute;
  left: 30px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: var(--color-border);
}

.timeline-item {
  display: flex;
  gap: 2rem;
  margin-bottom: 2rem;
  position: relative;
}

.timeline-marker {
  flex-shrink: 0;
  width: 60px;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 0.5rem;
}

.marker-dot {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--color-bg);
  border: 3px solid var(--color-accent-hover);
  position: relative;
  z-index: 1;
}

.timeline-content {
  flex: 1;
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  padding: 1.5rem;
  transition: all 0.2s;
}

.timeline-content:hover {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.4);
}

.entry-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}

.entry-title-group {
  flex: 1;
}

.entry-title {
  margin: 0 0 0.5rem 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text-bright);
}

.destination-link {
  color: var(--color-accent-hover);
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
}

.destination-link:hover {
  text-decoration: underline;
}

.entry-meta {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-shrink: 0;
}

.entry-date-line {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}

.entry-date {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--color-accent-hover);
  white-space: nowrap;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.entry-date-sep {
  color: var(--color-text-muted);
  font-size: 0.8rem;
}

.filter-sort {
  display: flex;
  align-items: flex-end;
}

.entry-body {
  color: var(--color-text);
  line-height: 1.6;
}

.entry-body :deep(h1),
.entry-body :deep(h2),
.entry-body :deep(h3) {
  margin: 1rem 0 0.5rem 0;
}

.entry-body :deep(p) {
  margin: 0.5rem 0;
}

.entry-body :deep(ul),
.entry-body :deep(ol) {
  margin: 0.5rem 0 0.5rem 1.5rem;
}

.entry-body :deep(li) {
  margin: 0.25rem 0;
}

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  background: var(--color-bg-elevated);
  border-radius: 0.5rem;
  border: 1px solid var(--color-border);
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

.py-4 {
  padding-top: 1.5rem;
  padding-bottom: 1.5rem;
}

@media (max-width: 768px) {
  .container {
    padding-left: 0.5rem;
    padding-right: 0.5rem;
  }

  .timeline::before {
    left: 16px;
  }

  .timeline-marker {
    width: 40px;
  }

  .timeline-item {
    gap: 1rem;
  }

  .entry-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .entry-meta {
    width: 100%;
    justify-content: space-between;
  }

  .entry-date {
    white-space: normal;
  }

  .filter-bar {
    grid-template-columns: 1fr;
  }
}
</style>
