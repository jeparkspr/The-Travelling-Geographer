<template>
  <component
    :is="selectable ? 'div' : 'router-link'"
    :to="selectable ? undefined : `/destinations/${destination.id}`"
    class="card-link"
    @dragover.prevent="onDragOver"
    @dragleave="onDragLeave"
    @drop.prevent="onDrop"
    @click="onClick"
  >
    <div class="destination-card" :class="{ 'drag-over': dragOver, 'card-selectable': selectable, 'card-selected': selected }">
      <div class="card-image">
        <div v-if="selectable" class="select-circle" :class="{ checked: selected }">
          <i v-if="selected" class="pi pi-check"></i>
        </div>
        <div v-if="uploading" class="placeholder uploading">
          <i class="pi pi-spin pi-spinner"></i>
        </div>
        <img
          v-else-if="(localThumbnail || destination.thumbnail_url) && !thumbError"
          :src="localThumbnail || destination.thumbnail_url"
          :alt="destination.name"
          @error="thumbError = true"
        />
        <div v-else class="placeholder">
          <i class="pi pi-image"></i>
        </div>
      </div>

      <div class="card-body">
        <div class="card-header">
          <h3 class="card-title">{{ destination.name }}</h3>
          <StatusBadge :status="destination.status" />
        </div>

        <div v-if="isShared" class="card-owner">
          <i class="pi pi-user"></i>
          <span>{{ destination.owner_name }}</span>
        </div>

        <div class="card-location">
          <i class="pi pi-map-marker"></i>
          <span>{{ destination.city ? `${destination.city}, ${destination.country}` : destination.country }}</span>
        </div>

        <div class="card-tags">
          <Chip
            v-for="tag in destination.tags"
            :key="tag"
            :label="tag"
            class="tag-chip"
          />
        </div>

        <div class="card-footer">
          <div v-if="destination.priority" class="priority" :class="`priority-${destination.priority}`">
            <i class="pi pi-flag"></i>
            <span>{{ destination.priority }}</span>
          </div>
          <div v-if="destination.rating" class="rating">
            <Rating v-model="destination.rating" :cancel="false" readonly />
          </div>
        </div>
      </div>
    </div>
  </component>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useToast } from 'primevue/usetoast'
import { useApi } from '@/composables/useApi'
import { useDestinationsStore } from '@/stores/destinations'
import StatusBadge from './StatusBadge.vue'

const props = defineProps({
  destination: {
    type: Object,
    required: true
  },
  selectable: {
    type: Boolean,
    default: false
  },
  selected: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['toggle-select'])

const toast = useToast()
const { uploadMedia, uploadMediaFromUrl } = useApi()
const destinationsStore = useDestinationsStore()

const currentUserId = (() => {
  try { return JSON.parse(localStorage.getItem('user') || '{}').id || null }
  catch { return null }
})()

const isShared = computed(() => {
  return props.destination.owner_id && props.destination.owner_id !== currentUserId
})

const dragOver = ref(false)
const uploading = ref(false)
const localThumbnail = ref(null)
const thumbError = ref(false)

const extractUrl = (text) => {
  if (!text) return null
  const trimmed = text.trim()
  try {
    const url = new URL(trimmed)
    if (url.protocol === 'http:' || url.protocol === 'https:') return trimmed
  } catch { /* not a valid URL */ }
  const match = trimmed.match(/https?:\/\/[^\s"'<>]+/i)
  return match ? match[0] : null
}

const extractImageFromHtml = (html) => {
  if (!html) return null
  const match = html.match(/<img[^>]+src=["']([^"']+)["']/i)
  if (match && match[1]) {
    const src = match[1]
    if (src.startsWith('http://') || src.startsWith('https://')) return src
  }
  return null
}

// Prevent navigation while uploading; toggle selection in select mode
const onClick = (event) => {
  if (uploading.value) { event.preventDefault(); return }
  if (props.selectable) {
    emit('toggle-select', props.destination.id)
  }
}

const onDragOver = (event) => {
  dragOver.value = true
}

const onDragLeave = () => {
  dragOver.value = false
}

const onDrop = async (event) => {
  dragOver.value = false
  const destId = props.destination.id

  const html = event.dataTransfer.getData('text/html')
  const imgUrl = extractImageFromHtml(html)
  const uriList = event.dataTransfer.getData('text/uri-list')
  const plainText = event.dataTransfer.getData('text/plain')
  const textUrl = extractUrl(uriList) || extractUrl(plainText)
  const files = Array.from(event.dataTransfer.files || [])
  const imageFiles = files.filter(f => f.type && f.type.startsWith('image/'))

  const tryFileUpload = async () => {
    if (!imageFiles.length) return false
    uploading.value = true
    try {
      await uploadMedia(destId, imageFiles)
      return true
    } catch {
      return false
    } finally {
      uploading.value = false
    }
  }

  // 1. Try direct image URL from text/html (e.g. Google Images preview)
  if (imgUrl) {
    uploading.value = true
    try {
      await uploadMediaFromUrl(destId, imgUrl, true)
      await refreshCard()
      return
    } catch {
      uploading.value = false
      if (await tryFileUpload()) {
        await refreshCard()
        return
      }
    }
  }

  // 2. Try text URL
  if (textUrl) {
    uploading.value = true
    try {
      await uploadMediaFromUrl(destId, textUrl, true)
      await refreshCard()
      return
    } catch {
      uploading.value = false
    }
  }

  // 3. Fall back to dropped files
  if (await tryFileUpload()) {
    await refreshCard()
    return
  }

  toast.add({
    severity: 'warn',
    summary: 'Upload failed',
    detail: 'Could not upload image from dropped content',
    life: 3000
  })
}

const refreshCard = async () => {
  try {
    const updated = await destinationsStore.fetchDestination(props.destination.id)
    if (updated?.thumbnail_url) {
      localThumbnail.value = updated.thumbnail_url + '?t=' + Date.now()
    }
    // Refresh the full list to update the store
    await destinationsStore.fetchDestinations({ page_size: 9999 })
    toast.add({
      severity: 'success',
      summary: 'Cover set',
      detail: `Image added to ${props.destination.name}`,
      life: 3000
    })
  } catch { /* ignore */ }
  uploading.value = false
}
</script>

<style scoped>
.card-link {
  text-decoration: none;
  color: inherit;
  display: block;
}

.destination-card {
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  overflow: hidden;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.destination-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
  border-color: var(--color-border);
}

.destination-card.drag-over {
  border-color: var(--color-accent-hover);
  box-shadow: 0 0 0 2px var(--color-accent-hover);
}

.card-image {
  width: 100%;
  aspect-ratio: 1;
  overflow: hidden;
  background: var(--color-bg-hover);
  position: relative;
}

.select-circle {
  position: absolute;
  top: 10px;
  left: 10px;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
  transition: background 0.15s, border-color 0.15s;
  background: rgba(0, 0, 0, 0.35);
  border: 2px solid rgba(255, 255, 255, 0.75);
}

.select-circle.checked {
  background: var(--color-accent-hover, #3b82f6);
  border-color: #fff;
}

.select-circle i {
  color: #fff;
  font-size: 14px;
  font-weight: bold;
}

.card-selectable {
  cursor: pointer;
}

.card-selected {
  border-color: var(--color-accent-hover, #3b82f6);
  border-width: 2px;
}

.card-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.2s;
}

.destination-card:hover .card-image img {
  transform: scale(1.05);
}

.placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);
  font-size: 2rem;
}

.placeholder.uploading {
  color: var(--color-accent-hover);
}

.card-body {
  padding: 1rem;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
  flex: 1;
}

.card-owner {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.8rem;
  color: #FFFF00;
  margin-bottom: 0.5rem;
  padding: 0.15rem 0.5rem;
  background: var(--color-bg-light);
  border-radius: 9999px;
  width: fit-content;
}

.card-location {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: var(--color-text-muted);
  margin-bottom: 0.75rem;
}

.card-location i {
  flex-shrink: 0;
}

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  min-height: 1.5rem;
}

.tag-chip {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: auto;
  padding-top: 0.75rem;
  border-top: 1px solid var(--color-border);
}

.priority {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  text-transform: capitalize;
}

.priority-low {
  color: #93c5fd;
}

.priority-medium {
  color: #22c55e;
}

.priority-high {
  color: #f87171;
}

.rating {
  display: flex;
  align-items: center;
}

.rating :deep(.p-rating-item) {
  margin-right: 0.25rem;
}
</style>
