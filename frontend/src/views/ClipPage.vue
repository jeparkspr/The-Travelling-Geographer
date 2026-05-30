<template>
  <div class="clip-page">
    <div class="clip-card">
      <div v-if="loading" class="clip-status">
        <i class="pi pi-spin pi-spinner" style="font-size: 2rem;"></i>
        <h2>Saving to Geographer...</h2>
        <p class="clip-url">{{ clipUrl }}</p>
      </div>

      <div v-else-if="savedDestination" class="clip-status success">
        <i class="pi pi-check-circle" style="font-size: 2.5rem; color: #22c55e;"></i>
        <h2>Saved!</h2>
        <p class="clip-title">{{ savedDestination.name }}</p>
        <p v-if="savedDestination.country" class="clip-detail">{{ savedDestination.country }}</p>
        <div class="clip-actions">
          <router-link :to="`/destinations/${savedDestination.id}`">
            <Button label="View Destination" icon="pi pi-eye" />
          </router-link>
          <router-link :to="`/destinations/${savedDestination.id}/edit`">
            <Button label="Edit Details" icon="pi pi-pencil" severity="secondary" />
          </router-link>
        </div>
      </div>

      <div v-else-if="error" class="clip-status error">
        <i class="pi pi-times-circle" style="font-size: 2.5rem; color: #ef4444;"></i>
        <h2>Failed to Save</h2>
        <p>{{ error }}</p>
        <p class="clip-url">{{ clipUrl }}</p>
        <div class="clip-actions">
          <Button label="Try Again" icon="pi pi-refresh" @click="doClip" />
          <router-link to="/">
            <Button label="Go to Dashboard" severity="secondary" />
          </router-link>
        </div>
      </div>

      <div v-else class="clip-status">
        <i class="pi pi-exclamation-triangle" style="font-size: 2.5rem; color: #f59e0b;"></i>
        <h2>No URL Provided</h2>
        <p>Use the bookmarklet from the Settings page to clip web pages.</p>
        <router-link to="/settings">
          <Button label="Go to Settings" icon="pi pi-cog" />
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useApi } from '@/composables/useApi'

const route = useRoute()
const { clipDestination } = useApi()

const loading = ref(false)
const savedDestination = ref(null)
const error = ref(null)
const clipUrl = ref('')

const doClip = async () => {
  const url = route.query.url
  const title = route.query.title || ''
  const description = route.query.description || ''

  if (!url) return

  clipUrl.value = url
  loading.value = true
  error.value = null
  savedDestination.value = null

  try {
    const response = await clipDestination({ url, title, description })
    savedDestination.value = response.data
  } catch (e) {
    console.error('Clip error:', e)
    error.value = e.response?.data?.detail || 'Failed to save destination. Please try again.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (route.query.url) {
    doClip()
  }
})
</script>

<style scoped>
.clip-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg);
  padding: 2rem;
}

.clip-card {
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: 0.75rem;
  padding: 3rem;
  max-width: 500px;
  width: 100%;
  text-align: center;
}

.clip-status h2 {
  margin: 1rem 0 0.5rem 0;
  color: var(--color-text-bright);
}

.clip-status p {
  color: var(--color-text-muted);
  margin: 0.25rem 0;
}

.clip-url {
  font-size: 0.8rem;
  word-break: break-all;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
}

.clip-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--color-text-bright);
}

.clip-detail {
  font-size: 0.875rem;
}

.clip-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: center;
  margin-top: 1.5rem;
  flex-wrap: wrap;
}

.clip-actions a {
  text-decoration: none;
}
</style>
