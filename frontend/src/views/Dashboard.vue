<template>
  <div class="dashboard">
    <div class="container py-4">
      <!-- Stats Row -->
      <div class="stats-grid mb-4">
        <router-link to="/destinations?status=suggested" class="stat-card-link">
          <div class="stat-card">
            <div class="stat-icon suggested">
              <i class="pi pi-bookmark"></i>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.suggested }}</div>
              <div class="stat-label">Suggested</div>
            </div>
          </div>
        </router-link>

        <router-link to="/destinations?status=want_to_visit" class="stat-card-link">
          <div class="stat-card">
            <div class="stat-icon want-to-visit">
              <i class="pi pi-heart"></i>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.want_to_visit }}</div>
              <div class="stat-label">Want to Visit</div>
            </div>
          </div>
        </router-link>

        <router-link to="/destinations?status=researching" class="stat-card-link">
          <div class="stat-card">
            <div class="stat-icon researching">
              <i class="pi pi-search"></i>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.researching }}</div>
              <div class="stat-label">Researching</div>
            </div>
          </div>
        </router-link>

        <router-link to="/destinations?status=planned" class="stat-card-link">
          <div class="stat-card">
            <div class="stat-icon planned">
              <i class="pi pi-calendar"></i>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.planned }}</div>
              <div class="stat-label">Planned</div>
            </div>
          </div>
        </router-link>

        <router-link to="/destinations?status=visited" class="stat-card-link">
          <div class="stat-card">
            <div class="stat-icon visited">
              <i class="pi pi-check-circle"></i>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.visited }}</div>
              <div class="stat-label">Visited</div>
            </div>
          </div>
        </router-link>

        <router-link v-if="settingsStore.showArchived" to="/destinations?status=archived" class="stat-card-link">
          <div class="stat-card">
            <div class="stat-icon archived">
              <i class="pi pi-box"></i>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ archivedCount }}</div>
              <div class="stat-label">Archived</div>
            </div>
          </div>
        </router-link>
      </div>

      <!-- Map Section -->
      <div class="section mb-4">
        <h2>Map View</h2>
        <div class="map-container small">
          <MapComponent
            :destinations="destinations"
            :zoom="3"
            :show-layer-control="true"
            map-id="dashboard"
          />
        </div>
      </div>

      <!-- Recent & Upcoming -->
      <div class="two-column">
        <!-- Recent Destinations -->
        <div class="section">
          <h2>Recent Destinations</h2>
          <div v-if="recentDestinations.length" class="destinations-list">
            <router-link
              v-for="dest in recentDestinations"
              :key="dest.id"
              :to="`/destinations/${dest.id}`"
              class="destination-item"
            >
              <div class="item-image" v-if="dest.thumbnail_url">
                <img :src="dest.thumbnail_url" :alt="dest.name" @error="e => e.target.style.display='none'" />
              </div>
              <div class="item-image placeholder" v-else>
                <i class="pi pi-image"></i>
              </div>
              <div class="item-content">
                <h4>{{ dest.name }}</h4>
                <p>{{ dest.country }}</p>
                <StatusBadge :status="dest.status" />
              </div>
            </router-link>
          </div>
          <div v-else class="empty-state">
            <p>No destinations yet</p>
            <router-link to="/destinations/new" class="btn-link">
              Add your first destination
            </router-link>
          </div>
        </div>

        <!-- Upcoming Trips -->
        <div class="section">
          <h2>Upcoming Trips</h2>
          <div v-if="upcomingTrips.length" class="destinations-list">
            <router-link
              v-for="trip in upcomingTrips"
              :key="trip.id"
              :to="`/destinations/${trip.id}`"
              class="destination-item"
            >
              <div class="item-image" v-if="trip.thumbnail_url">
                <img :src="trip.thumbnail_url" :alt="trip.name" @error="e => e.target.style.display='none'" />
              </div>
              <div class="item-image placeholder" v-else>
                <i class="pi pi-image"></i>
              </div>
              <div class="item-content">
                <h4>{{ trip.name }}</h4>
                <p>{{ trip.country }}</p>
                <span class="travel-dates">
                  <i class="pi pi-calendar"></i>
                  {{ formatDate(trip.planned_start_date) }}
                  <template v-if="trip.planned_end_date"> – {{ formatDate(trip.planned_end_date) }}</template>
                </span>
              </div>
            </router-link>
          </div>
          <div v-else class="empty-state">
            <p>No upcoming trips planned</p>
            <router-link to="/destinations/new" class="btn-link">
              Plan a trip
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { formatDistanceToNow, format } from 'date-fns'
import { useDestinationsStore } from '@/stores/destinations'
import { useSettingsStore } from '@/stores/settings'
import MapComponent from '@/components/MapComponent.vue'
import StatusBadge from '@/components/StatusBadge.vue'

const router = useRouter()

const destinationsStore = useDestinationsStore()
const settingsStore = useSettingsStore()
const destinations = computed(() => {
  const all = destinationsStore.destinations
  if (settingsStore.showArchived) return all
  return all.filter(d => d.status !== 'archived')
})

const archivedCount = computed(() => {
  return destinationsStore.destinations.filter(d => d.status === 'archived').length
})

const stats = computed(() => {
  const counts = { suggested: 0, researching: 0, want_to_visit: 0, planned: 0, visited: 0 }
  destinations.value.forEach(d => {
    if (counts[d.status] !== undefined) counts[d.status]++
  })
  return counts
})

const recentDestinations = computed(() => {
  return destinations.value.slice(0, 3)
})

const upcomingTrips = computed(() => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return destinations.value
    .filter(d => {
      if (d.status !== 'planned' || !d.planned_start_date) return false
      const endDate = d.planned_end_date ? new Date(d.planned_end_date) : new Date(d.planned_start_date)
      endDate.setHours(23, 59, 59, 999)
      return endDate >= today
    })
    .sort((a, b) => new Date(a.planned_start_date) - new Date(b.planned_start_date))
    .slice(0, 4)
})

const formatDate = (date) => {
  try {
    return format(new Date(date), 'MMM d, yyyy')
  } catch {
    return 'TBD'
  }
}

onMounted(async () => {
  try {
    await destinationsStore.fetchDestinations({ page_size: 9999 })
  } catch (error) {
    console.error('Error loading destinations:', error)
  }
})
</script>

<style scoped>
.dashboard {
  padding-top: 2rem;
  padding-bottom: 2rem;
}

.stats-grid {
  display: flex;
  gap: 0;
}

.stat-card-link {
  flex: 1;
  text-decoration: none;
  color: inherit;
  min-width: 0;
}

.stat-card {
  background: var(--color-bg-elevated);
  padding: 1rem 1rem 1rem 1.25rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  transition: filter 0.2s;
  cursor: pointer;
  height: 72px;
  clip-path: polygon(0 0, calc(100% - 14px) 0, 100% 50%, calc(100% - 14px) 100%, 0 100%, 14px 50%);
}

.stat-card-link:first-child .stat-card {
  clip-path: polygon(0 0, calc(100% - 14px) 0, 100% 50%, calc(100% - 14px) 100%, 0 100%);
  border-radius: 0.5rem 0 0 0.5rem;
}

.stat-card-link:last-child .stat-card {
  clip-path: polygon(0 0, 100% 0, 100% 100%, 0 100%, 14px 50%);
  border-radius: 0 0.5rem 0.5rem 0;
}

.stat-card:hover {
  filter: brightness(1.15);
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.5rem;
  flex-shrink: 0;
}

.stat-icon.suggested {
  background: #93c5fd;
}

.stat-icon.researching {
  background: #f59e0b;
}

.stat-icon.want-to-visit {
  background: #22c55e;
}

.stat-icon.planned {
  background: #f87171;
}

.stat-icon.visited {
  background: #c084fc;
}

.stat-icon.archived {
  background: #9ca3af;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--color-text-bright);
}

.stat-label {
  font-size: 0.875rem;
  color: var(--color-text-muted);
}

.section {
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  padding: 1.5rem;
}

.section h2 {
  margin-top: 0;
  margin-bottom: 1.5rem;
}

.two-column {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

.destinations-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.destination-item {
  display: flex;
  gap: 1rem;
  padding: 0.75rem;
  border-radius: 0.375rem;
  text-decoration: none;
  color: inherit;
  transition: all 0.2s;
  border: 1px solid var(--color-border);
}

.destination-item:hover {
  background: var(--color-bg-hover);
  border-color: var(--color-border);
}

.item-image {
  width: 80px;
  height: 80px;
  flex-shrink: 0;
  border-radius: 0.375rem;
  overflow: hidden;
  background: var(--color-bg-hover);
}

.item-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.item-image.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);
  font-size: 1.5rem;
}

.item-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.item-content h4 {
  margin: 0 0 0.25rem 0;
}

.item-content p {
  margin: 0 0 0.5rem 0;
  font-size: 0.875rem;
  color: var(--color-text-muted);
}

.travel-dates {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-accent-hover);
}

.travel-dates .pi {
  font-size: 0.75rem;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: var(--color-text-muted);
}

.btn-link {
  display: inline-block;
  margin-top: 0.75rem;
  color: var(--color-accent-hover);
  text-decoration: none;
  font-weight: 500;
}

.btn-link:hover {
  text-decoration: underline;
}

.py-4 {
  padding-top: 1.5rem;
  padding-bottom: 1.5rem;
}

.mb-4 {
  margin-bottom: 2rem;
}

@media (max-width: 768px) {
  .stats-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 0.75rem;
  }

  .stat-card,
  .stat-card-link:first-child .stat-card,
  .stat-card-link:last-child .stat-card {
    clip-path: none;
    border-radius: 0.5rem;
    height: auto;
    padding: 1rem;
    border: 1px solid var(--color-border);
  }

  .stat-value {
    font-size: 1.5rem;
  }

  .two-column {
    grid-template-columns: 1fr;
  }
}
</style>
