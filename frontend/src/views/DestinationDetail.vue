<template>
  <div v-if="loading" class="loading-state">
    <Skeleton height="2rem" class="mb-3" />
    <Skeleton height="400px" />
  </div>

  <div v-else-if="destination" class="destination-detail">
    <div class="detail-header">
      <div class="header-content">
        <div class="header-title">
          <h1>{{ destination.name }}</h1>
          <StatusBadge :status="destination.status" />
        </div>
        <div class="header-meta">
          <span v-if="destination.owner_name && destination.owner_id !== currentUserId" class="owner-label">
            <i class="pi pi-user"></i> {{ destination.owner_name }}
          </span>
          <span v-if="destination.permission_tier && destination.permission_tier !== 'manage'" class="tier-badge">
            {{ destination.permission_tier }}
          </span>
        </div>
        <div class="header-actions">
          <Button
            v-if="canManage"
            icon="pi pi-share-alt"
            label="Share"
            text
            @click="openShareDialog"
          />
          <router-link v-if="canEdit" :to="`/destinations/${destination.id}/edit`" class="btn">
            <Button icon="pi pi-pencil" label="Edit" text />
          </router-link>
          <Button
            v-if="canManage"
            icon="pi pi-trash"
            label="Delete"
            severity="danger"
            text
            @click="confirmDelete"
          />
        </div>
      </div>
    </div>

    <div class="detail-container">
      <Tabs value="overview">
        <TabList>
          <Tab value="overview">Overview</Tab>
          <Tab value="media">Media</Tab>
          <Tab v-if="showJournalTab" value="journal">Journal</Tab>
        </TabList>
        <TabPanels>
          <TabPanel value="overview">
            <div class="tab-content">
              <div class="overview-grid">
                <!-- Left Column -->
                <div class="overview-left">
                  <!-- Description -->
                  <div class="section">
                    <h3>Description</h3>
                    <div v-if="destination.description" class="rich-content" v-html="destination.description"></div>
                    <p v-else class="text-muted">No description added</p>
                  </div>

                  <!-- Links -->
                  <div class="section">
                    <h3>Links</h3>
                    <LinkManager
                      :links="destination.links"
                      :destination-id="destination.id"
                      :editable="canContribute"
                      @updated="refreshDestination"
                    />
                  </div>

                  <!-- Custom Fields -->
                  <div v-if="customFieldValues.length" class="section">
                    <h3>Custom Fields</h3>
                    <div class="custom-fields">
                      <div v-for="field in customFieldValues" :key="field.field_id" class="custom-field">
                        <label>{{ field.field_name }}</label>
                        <p>{{ field.value || 'N/A' }}</p>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Right Column -->
                <div class="overview-right">
                  <!-- Cover Image -->
                  <div v-if="coverImageUrl" class="cover-image-wrapper">
                    <img :src="coverImageUrl" :alt="destination.name" class="cover-image" />
                  </div>

                  <!-- Mini Map -->
                  <div class="section">
                    <div class="location-header">
                      <h3>Location</h3>
                      <div class="location-header-actions">
                        <a
                          v-if="destination.name"
                          :href="`https://www.google.com/search?tbm=isch&q=${encodeURIComponent((destination.name || '') + ' ' + (destination.city || ''))}`"
                          target="_blank"
                          rel="noopener noreferrer"
                          class="location-action-btn"
                          title="Search Google Images"
                        ><i class="pi pi-camera"></i></a>
                        <a
                          v-if="destination.latitude && destination.longitude"
                          :href="`https://www.google.com/maps/@${destination.latitude},${destination.longitude},14z`"
                          target="_blank"
                          rel="noopener noreferrer"
                          class="location-action-btn"
                          title="Open in Google Maps"
                        ><i class="pi pi-globe"></i></a>
                      </div>
                    </div>
                    <div class="map-container medium">
                      <MapComponent
                        :destinations="[destination]"
                        :center="[destination.latitude, destination.longitude]"
                        :zoom="8"
                        :show-layer-control="true"
                        map-id="detail-overview"
                      />
                    </div>
                  </div>

                  <!-- Info Card -->
                  <div class="section info-card">
                    <h3>Details</h3>
                    <div class="info-row">
                      <span class="info-label">Country:</span>
                      <span>{{ destination.country || 'N/A' }}</span>
                    </div>
                    <div v-if="destination.region" class="info-row">
                      <span class="info-label">Region:</span>
                      <span>{{ destination.region }}</span>
                    </div>
                    <div v-if="destination.city" class="info-row">
                      <span class="info-label">City:</span>
                      <span>{{ destination.city }}</span>
                    </div>
                    <div class="info-row">
                      <span class="info-label">Coordinates:</span>
                      <span>{{ destination.latitude.toFixed(4) }}, {{ destination.longitude.toFixed(4) }}</span>
                    </div>
                    <div v-if="destination.cost_estimate" class="info-row">
                      <span class="info-label">Est. Cost:</span>
                      <span>${{ destination.cost_estimate }}</span>
                    </div>
                    <div v-if="destination.priority" class="info-row">
                      <span class="info-label">Priority:</span>
                      <span class="priority-badge" :class="`priority-${destination.priority}`">{{ getPriorityLabel(destination.priority) }}</span>
                    </div>
                    <div v-if="destination.rating" class="info-row">
                      <span class="info-label">Rating:</span>
                      <Rating v-model="destination.rating" :cancel="false" readonly />
                    </div>
                    <div v-if="destination.best_season && destination.best_season.length" class="info-row">
                      <span class="info-label">Best Season:</span>
                      <div class="season-list">
                        <Chip v-for="season in destination.best_season" :key="season" :label="season" />
                      </div>
                    </div>
                    <div v-if="destination.tags && destination.tags.length" class="info-row">
                      <span class="info-label">Tags:</span>
                      <div class="tag-list">
                        <Chip v-for="tag in destination.tags" :key="tag" :label="tag" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </TabPanel>

          <TabPanel value="media">
            <div class="tab-content">
              <div class="media-header">
                <h3>Gallery</h3>
                <FileUpload
                  v-if="canContribute"
                  mode="basic"
                  name="files"
                  :multiple="true"
                  accept="image/*,video/*,application/pdf"
                  :auto="false"
                  choose-label="Upload Media"
                  @select="handleMediaUpload"
                />
              </div>
              <!-- URL Drop / Paste Zone -->
              <div
                v-if="canContribute"
                class="url-drop-zone"
                :class="{ 'drag-over': urlDragOver, 'uploading': urlUploading }"
                @dragover.prevent="onUrlDragOver"
                @dragleave.prevent="urlDragOver = false"
                @drop.prevent="onUrlDrop"
                @paste="onUrlPaste"
                tabindex="0"
              >
                <div v-if="urlUploading" class="url-drop-content">
                  <i class="pi pi-spin pi-spinner" style="font-size: 1.5rem;"></i>
                  <span>Downloading image...</span>
                </div>
                <div v-else class="url-drop-content">
                  <i class="pi pi-link" style="font-size: 1.5rem;"></i>
                  <span>Drop or paste an image URL here to upload &amp; set as cover</span>
                </div>
              </div>
              <div v-if="mediaList.length" class="section">
                <MediaGallery
                  :media="mediaList"
                  :editable="canEdit"
                  :cover-media-id="destination.cover_media_id"
                  @delete="handleMediaDelete"
                  @set-cover="handleSetCover"
                />
              </div>
              <div v-else class="empty-state">
                <i class="pi pi-image" style="font-size: 2rem;"></i>
                <p>No media added yet. Upload images, videos, or documents above.</p>
              </div>
            </div>
          </TabPanel>

          <TabPanel value="journal">
            <div class="tab-content">
              <div class="journal-header">
                <h3>Journal Entries</h3>
                <Button
                  v-if="canContribute"
                  icon="pi pi-plus"
                  label="Add Entry"
                  @click="openNewJournal"
                />
              </div>

              <div v-if="journalEntries.length" class="journal-list">
                <div v-for="entry in sortedJournalEntries" :key="entry.id" class="journal-item">
                  <div class="journal-header-item">
                    <div>
                      <h4>{{ entry.title }}</h4>
                      <p class="journal-date">{{ formatDate(entry.entry_date) }}</p>
                    </div>
                    <div class="journal-actions-row">
                      <div v-if="entry.rating" class="journal-rating">
                        <Rating v-model="entry.rating" :cancel="false" readonly />
                      </div>
                      <div v-if="canEdit" class="journal-entry-actions">
                        <Button
                          icon="pi pi-pencil"
                          severity="secondary"
                          text
                          rounded
                          size="small"
                          @click="openEditJournal(entry)"
                          title="Edit entry"
                        />
                        <Button
                          icon="pi pi-trash"
                          severity="danger"
                          text
                          rounded
                          size="small"
                          @click="confirmDeleteJournal(entry)"
                          title="Delete entry"
                        />
                      </div>
                    </div>
                  </div>
                  <div class="journal-body" v-html="entry.body_html || entry.body"></div>
                </div>
              </div>

              <div v-else class="empty-state">
                <p>No journal entries yet</p>
              </div>

              <!-- Journal Form Dialog (Create & Edit) -->
              <Dialog
                v-model:visible="journalFormOpen"
                :header="editingEntryId ? 'Edit Journal Entry' : 'New Journal Entry'"
                :modal="true"
                :style="{ width: '90vw', maxWidth: '700px' }"
              >
                <div class="journal-form">
                  <div class="field">
                    <label>Title</label>
                    <InputText v-model="journalForm.title" placeholder="Entry title" class="w-full" />
                  </div>
                  <div class="field">
                    <label>Date</label>
                    <Calendar v-model="journalForm.entry_date" date-format="yy-mm-dd" show-icon class="w-full" />
                  </div>
                  <div class="field">
                    <label>Rating</label>
                    <Rating v-model="journalForm.rating" />
                  </div>
                  <div class="field">
                    <label>Entry</label>
                    <RichTextEditor
                      v-model="journalForm.body"
                      placeholder="Write your journal entry..."
                    />
                  </div>
                  <div class="dialog-actions">
                    <Button label="Save" @click="saveJournalEntry" />
                    <Button label="Cancel" severity="secondary" @click="journalFormOpen = false" />
                  </div>
                </div>
              </Dialog>
            </div>
          </TabPanel>

        </TabPanels>
      </Tabs>
    </div>

    <!-- Share Dialog -->
    <Dialog
      v-model:visible="shareDialogVisible"
      header="Share Destination"
      :modal="true"
      :style="{ width: '90vw', maxWidth: '500px' }"
    >
      <div class="share-dialog">
        <div class="share-add-row">
          <Select
            v-model="newShareUserId"
            :options="availableUsers"
            option-label="display_name"
            option-value="id"
            placeholder="Select user..."
            class="share-user-select"
            :loading="sharingLoading"
          >
            <template #option="{ option }">
              <div>{{ option.display_name }} <span class="share-email-hint">{{ option.email }}</span></div>
            </template>
          </Select>
          <Select
            v-model="newShareTier"
            :options="tierOptions"
            option-label="label"
            option-value="value"
            class="share-tier-select"
          />
          <Button icon="pi pi-plus" @click="handleShare" :disabled="!newShareUserId" />
        </div>

        <div v-if="shares.length" class="share-list">
          <div v-for="share in shares" :key="share.id" class="share-item">
            <div class="share-item-info">
              <span class="share-item-name">{{ share.shared_with_name || share.shared_with_email }}</span>
              <span class="share-item-email" v-if="share.shared_with_name">{{ share.shared_with_email }}</span>
            </div>
            <span class="tier-badge share-tier">{{ share.permission_tier }}</span>
            <Button
              icon="pi pi-times"
              severity="danger"
              text
              rounded
              size="small"
              @click="handleRemoveShare(share.id)"
            />
          </div>
        </div>
        <div v-else class="share-empty">
          <p>Not shared with anyone yet</p>
        </div>
      </div>
    </Dialog>

  </div>

  <div v-else class="error-state">
    <i class="pi pi-exclamation-circle"></i>
    <p>Destination not found</p>
    <router-link to="/destinations" class="btn-link">Back to Destinations</router-link>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDestinationsStore } from '@/stores/destinations'
import { useCustomFieldsStore } from '@/stores/customFields'
import { useApi } from '@/composables/useApi'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import { format } from 'date-fns'
import MapComponent from '@/components/MapComponent.vue'
import MediaGallery from '@/components/MediaGallery.vue'
import LinkManager from '@/components/LinkManager.vue'
import RichTextEditor from '@/components/RichTextEditor.vue'
import StatusBadge from '@/components/StatusBadge.vue'

const route = useRoute()
const router = useRouter()
const destinationsStore = useDestinationsStore()
const customFieldsStore = useCustomFieldsStore()
const {
  getJournalEntries, createJournalEntry, updateJournalEntry, deleteJournalEntry,
  deleteDestination, uploadMedia, uploadMediaFromUrl, deleteMedia, getMedia, setCoverImage,
  getDestinationShares, shareDestination, removeDestinationShare, getShareableUsers
} = useApi()
const confirm = useConfirm()
const toast = useToast()

// Returns true if the error is a 403 (access revoked) and handles redirect
const isAccessRevoked = (error) => {
  if (error.response?.status === 403) {
    toast.add({
      severity: 'warn',
      summary: 'Access Revoked',
      detail: 'Your access to this destination has been removed. Redirecting...',
      life: 5000
    })
    router.push('/destinations')
    return true
  }
  return false
}

const loading = ref(false)
const mediaList = ref([])
const journalEntries = ref([])
const journalFormOpen = ref(false)
const editingEntryId = ref(null)
const journalForm = reactive({
  title: '',
  entry_date: new Date(),
  rating: 0,
  body: ''
})

// Sharing state
const shareDialogVisible = ref(false)
const shares = ref([])
const shareableUsers = ref([])
const sharingLoading = ref(false)
const newShareUserId = ref(null)
const newShareTier = ref('view')
const tierOptions = [
  { label: 'View', value: 'view' },
  { label: 'Contribute', value: 'contribute' },
  { label: 'Edit', value: 'edit' },
  { label: 'Manage', value: 'manage' }
]

// Current user
const currentUserId = computed(() => {
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    return user.id || null
  } catch { return null }
})

// Permission helpers
const effectiveTier = computed(() => destination.value?.permission_tier || 'manage')
const canManage = computed(() => effectiveTier.value === 'manage')
const canEdit = computed(() => ['edit', 'manage'].includes(effectiveTier.value))
const canContribute = computed(() => ['contribute', 'edit', 'manage'].includes(effectiveTier.value))
const showJournalTab = computed(() => ['planned', 'visited', 'archived'].includes(destination.value?.status))

const destination = computed(() => destinationsStore.currentDestination)

const coverImageUrl = computed(() => {
  if (!destination.value?.cover_media_id || !mediaList.value.length) return null
  const coverMedia = mediaList.value.find(m => m.id === destination.value.cover_media_id)
  return coverMedia?.url || null
})

const customFieldValues = computed(() => {
  if (!destination.value || !destination.value.custom_fields) return []
  return destination.value.custom_fields.map(field => ({
    field_id: field.field_id,
    field_name: field.field_name,
    value: field.value
  }))
})

const getPriorityLabel = (priority) => {
  const labels = { low: 'Low', medium: 'Medium', high: 'High' }
  return labels[priority] || priority
}

const sortedJournalEntries = computed(() => {
  return [...journalEntries.value].sort((a, b) => {
    const dateA = a.entry_date || ''
    const dateB = b.entry_date || ''
    return dateA.localeCompare(dateB)
  })
})

const refreshDestination = async () => {
  await destinationsStore.fetchDestination(route.params.id)
}

const formatDate = (date) => {
  try {
    // Parse date-only strings (e.g. "2015-09-04") as local time, not UTC
    if (typeof date === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(date)) {
      const [y, m, d] = date.split('-').map(Number)
      return format(new Date(y, m - 1, d), 'MMM d, yyyy')
    }
    return format(new Date(date), 'MMM d, yyyy')
  } catch {
    return 'Invalid date'
  }
}

const loadMedia = async () => {
  try {
    const response = await getMedia(route.params.id)
    mediaList.value = response.data || []
  } catch (error) {
    if (isAccessRevoked(error)) return
    console.error('Error loading media:', error)
    // Fall back to destination's media array
    mediaList.value = destination.value?.media || []
  }
}

const handleMediaUpload = async (event) => {
  const files = event.files
  if (!files || !files.length) return

  try {
    await uploadMedia(route.params.id, Array.from(files))
    toast.add({
      severity: 'success',
      summary: 'Success',
      detail: `${files.length} file(s) uploaded`,
      life: 3000
    })
    await loadMedia()
  } catch (error) {
    if (isAccessRevoked(error)) return
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to upload media',
      life: 3000
    })
  }
}

const handleMediaDelete = async (mediaId) => {
  try {
    await deleteMedia(mediaId)
    toast.add({
      severity: 'success',
      summary: 'Success',
      detail: 'Media deleted',
      life: 3000
    })
    await loadMedia()
  } catch (error) {
    if (isAccessRevoked(error)) return
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to delete media',
      life: 3000
    })
  }
}

const handleSetCover = async (mediaId) => {
  try {
    await setCoverImage(route.params.id, mediaId)
    // Refresh destination to get updated cover_media_id
    await destinationsStore.fetchDestination(route.params.id)
    toast.add({
      severity: 'success',
      summary: 'Success',
      detail: 'Cover image updated',
      life: 3000
    })
  } catch (error) {
    if (isAccessRevoked(error)) return
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to set cover image',
      life: 3000
    })
  }
}

// URL drop/paste upload
const urlDragOver = ref(false)
const urlUploading = ref(false)

const onUrlDragOver = () => {
  urlDragOver.value = true
}

const extractUrl = (text) => {
  if (!text) return null
  const trimmed = text.trim()
  try {
    const url = new URL(trimmed)
    if (url.protocol === 'http:' || url.protocol === 'https:') return trimmed
  } catch { /* not a valid URL */ }
  // Try to find a URL in the text
  const match = trimmed.match(/https?:\/\/[^\s"'<>]+/i)
  return match ? match[0] : null
}

const handleUrlUpload = async (url) => {
  if (!url) return
  urlUploading.value = true
  try {
    await uploadMediaFromUrl(route.params.id, url, true)
    toast.add({
      severity: 'success',
      summary: 'Success',
      detail: 'Image uploaded from URL and set as cover',
      life: 3000
    })
    await loadMedia()
    await destinationsStore.fetchDestination(route.params.id)
  } catch (error) {
    if (isAccessRevoked(error)) return
    const detail = error.response?.data?.detail || 'Failed to upload image from URL'
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail,
      life: 5000
    })
  } finally {
    urlUploading.value = false
  }
}

const extractImageFromHtml = (html) => {
  if (!html) return null
  // Parse the HTML fragment for <img src="..."> — the browser puts the actual
  // image URL here when you drag an image element from a page.
  const match = html.match(/<img[^>]+src=["']([^"']+)["']/i)
  if (match && match[1]) {
    const src = match[1]
    // Only use http(s) URLs (skip data: URIs which are tiny thumbnails)
    if (src.startsWith('http://') || src.startsWith('https://')) return src
  }
  return null
}

const onUrlDrop = async (event) => {
  urlDragOver.value = false

  // Gather all available data upfront
  const html = event.dataTransfer.getData('text/html')
  const imgUrl = extractImageFromHtml(html)
  const uriList = event.dataTransfer.getData('text/uri-list')
  const plainText = event.dataTransfer.getData('text/plain')
  const textUrl = extractUrl(uriList) || extractUrl(plainText)
  const files = Array.from(event.dataTransfer.files || [])
  const imageFiles = files.filter(f => f.type && f.type.startsWith('image/'))

  // Helper: try uploading dropped files directly
  const tryFileUpload = async () => {
    if (!imageFiles.length) return false
    urlUploading.value = true
    try {
      await uploadMedia(route.params.id, imageFiles)
      toast.add({
        severity: 'success',
        summary: 'Success',
        detail: `${imageFiles.length} image(s) uploaded`,
        life: 3000
      })
      await loadMedia()
      await destinationsStore.fetchDestination(route.params.id)
      return true
    } catch (error) {
      if (isAccessRevoked(error)) return true  // true = stop further attempts
      return false
    } finally {
      urlUploading.value = false
    }
  }

  // 1. Try the direct image URL from text/html (e.g. Google Images preview)
  //    If the server-side fetch fails (CDN blocks it), fall back to the
  //    browser's dropped file which was already downloaded client-side.
  if (imgUrl) {
    urlUploading.value = true
    try {
      await uploadMediaFromUrl(route.params.id, imgUrl, true)
      toast.add({ severity: 'success', summary: 'Success', detail: 'Image uploaded from URL and set as cover', life: 3000 })
      await loadMedia()
      await destinationsStore.fetchDestination(route.params.id)
      urlUploading.value = false
      return
    } catch (error) {
      urlUploading.value = false
      if (isAccessRevoked(error)) return
      // Fall through to file upload
      if (await tryFileUpload()) return
    }
  }

  // 2. Check for text URLs (uri-list / plain text)
  if (textUrl) {
    handleUrlUpload(textUrl)
    return
  }

  // 3. Fall back to dropped image files
  if (await tryFileUpload()) return

  toast.add({
    severity: 'warn',
    summary: 'No URL found',
    detail: 'Could not find a valid image URL in the dropped content',
    life: 3000
  })
}


const onUrlPaste = (event) => {
  const text = event.clipboardData?.getData('text/plain')
  const url = extractUrl(text)
  if (url) {
    event.preventDefault()
    handleUrlUpload(url)
  }
}

const loadJournalEntries = async () => {
  try {
    const response = await getJournalEntries(route.params.id)
    journalEntries.value = response.data || []
  } catch (error) {
    if (isAccessRevoked(error)) return
    console.error('Error loading journal entries:', error)
  }
}

const resetJournalForm = () => {
  journalForm.title = ''
  journalForm.entry_date = new Date()
  journalForm.rating = 0
  journalForm.body = ''
  editingEntryId.value = null
}

const openNewJournal = () => {
  resetJournalForm()
  journalFormOpen.value = true
}

const openEditJournal = (entry) => {
  editingEntryId.value = entry.id
  journalForm.title = entry.title || ''
  journalForm.body = entry.body || ''
  journalForm.rating = entry.rating || 0
  if (entry.entry_date && /^\d{4}-\d{2}-\d{2}$/.test(entry.entry_date)) {
    const [y, m, d] = entry.entry_date.split('-').map(Number)
    journalForm.entry_date = new Date(y, m - 1, d)
  } else {
    journalForm.entry_date = entry.entry_date ? new Date(entry.entry_date) : new Date()
  }
  journalFormOpen.value = true
}

const saveJournalEntry = async () => {
  if (!journalForm.title || !journalForm.body) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Title and body are required',
      life: 3000
    })
    return
  }

  try {
    const payload = {
      title: journalForm.title,
      entry_date: format(journalForm.entry_date, 'yyyy-MM-dd'),
      body: journalForm.body,
      rating: journalForm.rating || null
    }

    if (editingEntryId.value) {
      await updateJournalEntry(route.params.id, editingEntryId.value, payload)
    } else {
      await createJournalEntry(route.params.id, payload)
    }

    toast.add({
      severity: 'success',
      summary: 'Success',
      detail: editingEntryId.value ? 'Journal entry updated' : 'Journal entry saved',
      life: 3000
    })

    resetJournalForm()
    journalFormOpen.value = false
    await loadJournalEntries()
  } catch (error) {
    if (isAccessRevoked(error)) return
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to save journal entry',
      life: 3000
    })
  }
}

const confirmDeleteJournal = (entry) => {
  confirm.require({
    message: `Are you sure you want to delete "${entry.title}"?`,
    header: 'Delete Journal Entry',
    icon: 'pi pi-exclamation-triangle',
    accept: async () => {
      try {
        await deleteJournalEntry(route.params.id, entry.id)
        toast.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Journal entry deleted',
          life: 3000
        })
        await loadJournalEntries()
      } catch (error) {
        if (isAccessRevoked(error)) return
        toast.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to delete journal entry',
          life: 3000
        })
      }
    }
  })
}

const confirmDelete = () => {
  confirm.require({
    message: 'Are you sure you want to delete this destination?',
    header: 'Confirm Delete',
    icon: 'pi pi-exclamation-triangle',
    accept: async () => {
      try {
        await destinationsStore.deleteCurrentDestination(route.params.id)
        toast.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Destination deleted',
          life: 3000
        })
        router.push('/destinations')
      } catch (error) {
        if (isAccessRevoked(error)) return
        toast.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to delete destination',
          life: 3000
        })
      }
    }
  })
}

// Sharing methods
const loadShares = async () => {
  sharingLoading.value = true
  try {
    const [sharesRes, usersRes] = await Promise.all([
      getDestinationShares(route.params.id),
      getShareableUsers()
    ])
    shares.value = sharesRes.data || []
    shareableUsers.value = usersRes.data || []
  } catch (error) {
    console.error('Error loading shares:', error)
  } finally {
    sharingLoading.value = false
  }
}

const openShareDialog = async () => {
  shareDialogVisible.value = true
  newShareUserId.value = null
  newShareTier.value = 'view'
  await loadShares()
}

const handleShare = async () => {
  if (!newShareUserId.value) return
  try {
    await shareDestination(route.params.id, newShareUserId.value, newShareTier.value)
    toast.add({
      severity: 'success',
      summary: 'Shared',
      detail: 'Destination shared successfully',
      life: 3000
    })
    newShareUserId.value = null
    newShareTier.value = 'view'
    await loadShares()
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: error.response?.data?.detail || 'Failed to share destination',
      life: 3000
    })
  }
}

const handleRemoveShare = async (shareId) => {
  try {
    await removeDestinationShare(route.params.id, shareId)
    toast.add({
      severity: 'success',
      summary: 'Removed',
      detail: 'Share removed',
      life: 3000
    })
    await loadShares()
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to remove share',
      life: 3000
    })
  }
}

// Filter out users already shared with
const availableUsers = computed(() => {
  const sharedIds = new Set(shares.value.map(s => s.shared_with_id))
  return shareableUsers.value.filter(u => !sharedIds.has(u.id))
})

onMounted(async () => {
  loading.value = true
  try {
    await destinationsStore.fetchDestination(route.params.id)
    await customFieldsStore.fetchFields()
    await loadMedia()
    await loadJournalEntries()
  } catch (error) {
    if (isAccessRevoked(error)) return
    console.error('Error loading destination:', error)
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to load destination',
      life: 3000
    })
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.destination-detail {
  min-height: 100vh;
}

.detail-header {
  background: var(--color-bg-elevated);
  border-bottom: 1px solid var(--color-border);
  padding: 2rem;
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 2rem;
}

.header-title {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  flex: 1;
}

.header-title h1 {
  margin: 0;
  font-size: 2.25rem;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
  flex-shrink: 0;
}

.btn {
  text-decoration: none;
}

.detail-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}

.detail-container :deep(.p-tabs) {
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  overflow: hidden;
}

.detail-container :deep(.p-tablist) {
  background: var(--color-bg);
  border-bottom: 1px solid var(--color-border);
}

.tab-content {
  padding: 2rem;
}

.overview-grid {
  display: grid;
  grid-template-columns: 1fr 350px;
  gap: 2rem;
}

.section {
  margin-bottom: 2rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid var(--color-border);
}

.section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.section h3 {
  margin: 0 0 1rem 0;
  font-size: 1.125rem;
}

.overview-left {
  min-width: 0;
  overflow: hidden;
}

.rich-content {
  color: var(--color-text);
  line-height: 1.6;
  overflow-wrap: break-word;
  word-break: break-word;
}

.rich-content :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 0.375rem;
  margin: 0.5rem 0;
}

.rich-content :deep(h1),
.rich-content :deep(h2),
.rich-content :deep(h3) {
  margin: 1rem 0 0.5rem 0;
}

.rich-content :deep(p) {
  margin: 0.5rem 0;
}

.rich-content :deep(ul),
.rich-content :deep(ol) {
  margin: 0.5rem 0 0.5rem 1.5rem;
}

.rich-content :deep(li) {
  margin: 0.25rem 0;
}

.text-muted {
  color: var(--color-text-muted);
  font-style: italic;
}

.info-card {
  background: var(--color-bg-light);
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  padding: 2rem;
  margin: 0;
  border-bottom: 1px solid var(--color-border);
}

.info-row {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-bottom: 0.75rem;
  font-size: 0.875rem;
}

.info-row:last-child {
  margin-bottom: 0;
}

.info-label {
  font-weight: 600;
  color: var(--color-text-bright);
}

.info-row span:not(.info-label) {
  color: var(--color-text-muted);
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

.season-list,
.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.season-list :deep(.p-chip),
.tag-list :deep(.p-chip) {
  font-size: 0.75rem;
}

.overview-right {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.location-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.4rem;
}

.location-header h3 {
  margin-bottom: 0;
}

.location-header-actions {
  display: flex;
  gap: 0.35rem;
}

.location-action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 6px;
  background: var(--color-bg-light);
  border: 1px solid var(--color-border);
  text-decoration: none;
  color: var(--color-text-muted);
  font-size: 0.875rem;
  transition: background 0.2s, color 0.2s;
}

.location-action-btn:hover {
  background: var(--color-bg-hover);
  color: var(--color-text-bright);
}

.cover-image-wrapper {
  width: 100%;
  aspect-ratio: 1 / 1;
  overflow: hidden;
  border-radius: 12px;
}

.cover-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.overview-right .section {
  margin: 0;
  padding: 0;
  border: none;
}

.overview-right .section.info-card {
  padding: 1.5rem;
}

.media-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
}

.media-header h3 {
  margin: 0;
}

.journal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
}

.journal-header h3 {
  margin: 0;
}

.journal-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.journal-item {
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  padding: 1.5rem;
  background: var(--color-bg-elevated);
}

.journal-header-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.journal-header-item h4 {
  margin: 0 0 0.25rem 0;
  font-size: 1rem;
}

.journal-date {
  margin: 0;
  font-size: 0.875rem;
  color: var(--color-text-muted);
}

.journal-actions-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-shrink: 0;
}

.journal-entry-actions {
  display: flex;
  gap: 0.25rem;
}

.journal-rating {
  display: flex;
  align-items: center;
}

.journal-body {
  color: var(--color-text);
  line-height: 1.6;
  overflow-wrap: break-word;
  word-break: break-word;
}

.journal-body :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 0.375rem;
  margin: 0.5rem 0;
}

.journal-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.field label {
  font-weight: 600;
  font-size: 0.875rem;
}

.field :deep(.p-inputtext),
.field :deep(.p-calendar),
.field :deep(.p-rating) {
  width: 100%;
}

.dialog-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1rem;
}

.dialog-actions button {
  flex: 1;
}

.empty-state {
  text-align: center;
  padding: 3rem 2rem;
  color: var(--color-text-muted);
}

.empty-state p {
  margin: 1rem 0 0 0;
}

.error-state {
  text-align: center;
  padding: 4rem 2rem;
  color: var(--color-text-muted);
}

.error-state i {
  font-size: 3rem;
  color: #ef4444;
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
}

.btn-link:hover {
  background: var(--color-bg-hover);
}

.loading-state {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.mb-3 {
  margin-bottom: 1rem;
}

.w-full {
  width: 100%;
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
  }

  .header-actions {
    width: 100%;
  }

  .detail-container {
    padding: 0.5rem;
  }

  .tab-content {
    padding: 0.3rem;
  }

  .section {
    margin-bottom: 1rem;
    padding-bottom: 1rem;
  }

  .info-card {
    padding: 1rem;
  }

  .overview-right .section.info-card {
    padding: 1rem;
  }

  .overview-grid {
    grid-template-columns: 1fr;
  }

  .overview-left,
  .overview-right {
    grid-column: 1;
  }

  .journal-header {
    flex-direction: column;
    align-items: stretch;
    gap: 1rem;
  }

  .journal-header button {
    width: 100%;
  }
}

/* URL drop zone */
.url-drop-zone {
  border: 2px dashed var(--color-border);
  border-radius: 0.5rem;
  padding: 1.25rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 1rem;
  outline: none;
}

.url-drop-zone:hover,
.url-drop-zone:focus {
  border-color: var(--color-accent-hover);
  background: rgba(59, 130, 246, 0.05);
}

.url-drop-zone.drag-over {
  border-color: var(--color-accent-hover);
  background: rgba(59, 130, 246, 0.1);
  border-style: solid;
}

.url-drop-zone.uploading {
  opacity: 0.7;
  pointer-events: none;
}

.url-drop-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  color: var(--color-text-muted);
  font-size: 0.875rem;
}

.url-drop-zone:hover .url-drop-content,
.url-drop-zone.drag-over .url-drop-content {
  color: var(--color-accent-hover);
}

/* Header meta (owner label & tier badge) */
.header-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}

.owner-label {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.8rem;
  color: var(--color-text-muted);
  background: var(--color-bg-light);
  border: 1px solid var(--color-border);
  border-radius: 9999px;
  padding: 0.2rem 0.65rem;
}

.tier-badge {
  display: inline-block;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0.2rem 0.6rem;
  border-radius: 9999px;
  background: rgba(59, 130, 246, 0.12);
  color: #60a5fa;
}

/* Share Dialog */
.share-dialog {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.share-add-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.share-user-select {
  flex: 1;
}

.share-tier-select {
  width: 130px;
}

.share-email-hint {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  margin-left: 0.25rem;
}

.share-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.share-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  background: var(--color-bg-light);
}

.share-item-info {
  flex: 1;
  min-width: 0;
}

.share-item-name {
  display: block;
  font-weight: 500;
  font-size: 0.875rem;
}

.share-item-email {
  display: block;
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

.share-tier {
  flex-shrink: 0;
}

.share-empty {
  text-align: center;
  color: var(--color-text-muted);
  padding: 1rem;
  font-size: 0.875rem;
}

.share-empty p {
  margin: 0;
}
</style>
