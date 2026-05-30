<template>
  <div class="destination-form-page">
    <div class="form-header">
      <div class="form-header-content">
        <h1>{{ isEdit ? 'Edit Destination' : 'New Destination' }}</h1>
        <div class="header-actions">
          <Button
            label="Save Destination"
            @click="submitForm"
            severity="success"
            icon="pi pi-save"
          />
          <router-link to="/destinations">
            <Button
              label="Cancel"
              severity="secondary"
              icon="pi pi-times"
            />
          </router-link>
        </div>
      </div>
    </div>

    <div class="form-container">
      <form @submit.prevent="submitForm" class="form-layout">
        <!-- Left Column -->
        <div class="form-left">
          <!-- Basic Info -->
          <div class="form-section">
            <h2>Basic Information</h2>

            <div class="field">
              <label>Destination Name *</label>
              <InputText
                v-model="formData.name"
                placeholder="e.g., Tokyo"
                class="w-full"
              />
            </div>

            <div class="field">
              <label>Status *</label>
              <Dropdown
                v-model="formData.status"
                :options="statusOptions"
                option-label="label"
                option-value="value"
                placeholder="Select status"
                class="w-full"
              />
            </div>

            <div class="form-row">
              <div class="field flex-1">
                <label>Country</label>
                <InputText
                  v-model="formData.country"
                  placeholder="e.g., Japan"
                  class="w-full"
                />
              </div>
              <div class="field flex-1">
                <label>Region</label>
                <InputText
                  v-model="formData.region"
                  placeholder="e.g., Asia"
                  class="w-full"
                />
              </div>
            </div>

            <div class="field">
              <label>City</label>
              <InputText
                v-model="formData.city"
                placeholder="e.g., Tokyo"
                class="w-full"
              />
            </div>

            <div class="field">
              <label>Description</label>
              <RichTextEditor
                v-model="formData.description"
                placeholder="Write a detailed description..."
              />
            </div>

            <div class="field">
              <label>Tags</label>
              <div class="tags-input-container">
                <div class="tags-chips">
                  <Chip
                    v-for="tag in selectedTags"
                    :key="tag"
                    :label="tag"
                    removable
                    @remove="removeTag(tag)"
                  />
                </div>
                <div class="tags-input-row">
                  <InputText
                    v-model="newTagInput"
                    placeholder="Type a tag and press Enter..."
                    class="w-full"
                    @keyup.enter="addTag"
                    list="existing-tags-list"
                  />
                  <datalist id="existing-tags-list">
                    <option v-for="tag in availableTagSuggestions" :key="tag" :value="tag" />
                  </datalist>
                  <Button
                    icon="pi pi-plus"
                    @click="addTag"
                    text
                    size="small"
                  />
                </div>
              </div>
            </div>
          </div>

          <!-- Details -->
          <div class="form-section">
            <h2>Details</h2>

            <div class="form-row">
              <div class="field flex-1">
                <label>Priority</label>
                <SelectButton
                  v-model="formData.priority"
                  :options="priorityOptions"
                  option-label="label"
                  option-value="value"
                  class="w-full"
                />
              </div>
              <div class="field flex-1">
                <label>Cost Estimate</label>
                <InputNumber
                  v-model="formData.cost_estimate"
                  prefix="$"
                  :use-grouping="true"
                  class="w-full"
                />
              </div>
            </div>

            <div class="form-row">
              <div class="field flex-1">
                <label>Rating</label>
                <Rating
                  v-model="formData.rating"
                  :cancel="true"
                />
              </div>
            </div>

            <div class="field">
              <label>Best Season</label>
              <MultiSelect
                v-model="formData.best_season"
                :options="seasonOptions"
                option-label="label"
                option-value="value"
                placeholder="Select seasons"
                class="w-full"
                display="chip"
              />
            </div>
          </div>

          <!-- Dates -->
          <div class="form-section">
            <h2>Dates</h2>

            <div class="field">
              <label>Date Researched</label>
              <Calendar
                v-model="formData.date_researched"
                date-format="yy-mm-dd"
                show-icon
                class="w-full"
              />
            </div>

            <div v-if="isPlanned" class="form-row">
              <div class="field flex-1">
                <label>Planned Start Date</label>
                <Calendar
                  v-model="formData.planned_start_date"
                  date-format="yy-mm-dd"
                  show-icon
                  class="w-full"
                />
              </div>
              <div class="field flex-1">
                <label>Planned End Date</label>
                <Calendar
                  ref="plannedEndDateRef"
                  v-model="formData.planned_end_date"
                  date-format="yy-mm-dd"
                  show-icon
                  class="w-full"
                />
              </div>
            </div>

            <div v-if="isVisited" class="form-row">
              <div class="field flex-1">
                <label>Visit Start Date</label>
                <Calendar
                  v-model="formData.visited_start_date"
                  date-format="yy-mm-dd"
                  show-icon
                  class="w-full"
                />
              </div>
              <div class="field flex-1">
                <label>Visit End Date</label>
                <Calendar
                  ref="visitedEndDateRef"
                  v-model="formData.visited_end_date"
                  date-format="yy-mm-dd"
                  show-icon
                  class="w-full"
                />
              </div>
            </div>
          </div>

          <!-- Custom Fields -->
          <div v-if="customFields.length" class="form-section">
            <h2>Custom Fields</h2>
            <div v-for="field in customFields" :key="field.id" class="field">
              <label>{{ field.name }}</label>
              <InputText
                v-if="field.field_type === 'text'"
                :model-value="getCustomFieldValue(field.id)"
                @update:model-value="updateCustomField(field.id, $event)"
                class="w-full"
              />
              <Dropdown
                v-else-if="field.field_type === 'select'"
                :model-value="getCustomFieldValue(field.id)"
                @update:model-value="updateCustomField(field.id, $event)"
                :options="field.options"
                class="w-full"
              />
            </div>
          </div>

          <!-- Links -->
          <div class="form-section">
            <h2>Links</h2>
            <div v-if="isEdit">
              <LinkManager
                :links="formData.links || []"
                :destination-id="route.params.id"
                :editable="true"
                @updated="refreshLinks"
              />
            </div>
            <div v-else>
              <!-- Local link management for new destinations (not yet saved) -->
              <div v-if="localLinks.length" class="links-list">
                <div v-for="(link, index) in localLinks" :key="index" class="local-link-item">
                  <div class="local-link-content">
                    <strong>{{ link.title || 'Untitled' }}</strong>
                    <a :href="link.url" target="_blank" class="local-link-url">{{ link.url }}</a>
                  </div>
                  <Button
                    icon="pi pi-trash"
                    text
                    severity="danger"
                    size="small"
                    @click="localLinks.splice(index, 1)"
                  />
                </div>
              </div>
              <div v-else class="empty-links">
                <p>No links yet. Add links below.</p>
              </div>
              <div class="local-link-form">
                <div class="field">
                  <label>URL</label>
                  <InputText v-model="newLink.url" placeholder="https://example.com" class="w-full" />
                </div>
                <div class="field">
                  <label>Title</label>
                  <InputText v-model="newLink.title" placeholder="Link title" class="w-full" />
                </div>
                <Button label="Add Link" icon="pi pi-plus" size="small" @click="addLocalLink" />
              </div>
            </div>
          </div>
        </div>

        <!-- Right Column -->
        <div class="form-right">
          <!-- Location Map -->
          <div class="form-section">
            <div class="section-header-row">
              <h2>Location</h2>
              <Button
                icon="pi pi-sparkles"
                label="AI Populate"
                size="small"
                severity="help"
                @click="handleAIPopulate"
                :loading="aiLoading"
                :disabled="aiLoading || (!formData.latitude && !formData.longitude)"
                title="Use AI to fill destination details from coordinates"
              />
            </div>

            <div class="field geocoding-field">
              <label>Search Location</label>
              <div class="geocoding-input">
                <InputText
                  v-model="locationSearch"
                  placeholder="Search for a location..."
                  @keyup.enter="geocodeLocation"
                  class="w-full"
                />
                <Button
                  icon="pi pi-search"
                  @click="geocodeLocation"
                  text
                />
              </div>
              <div v-if="geocodingResults.length" class="geocoding-results">
                <div
                  v-for="result in geocodingResults"
                  :key="result.display_name"
                  class="result-item"
                  @click="selectGeocodingResult(result)"
                >
                  {{ result.display_name }}
                </div>
              </div>
            </div>

            <div class="map-container medium" style="margin-bottom: 0.4rem;">
              <MapComponent
                :destinations="formData.latitude ? [createMapMarker()] : []"
                :center="[formData.latitude || 0, formData.longitude || 0]"
                :zoom="8"
                :selectable="true"
                :selected-position="selectedMapPosition"
                :show-layer-control="true"
                map-id="edit-form"
                @map-click="handleMapClick"
              />
            </div>

            <div class="form-row">
              <div class="field flex-1">
                <label>Latitude *</label>
                <InputNumber
                  v-model="formData.latitude"
                  :min="-90"
                  :max="90"
                  :step="0.0001"
                  class="w-full"
                />
              </div>
              <div class="field flex-1">
                <label>Longitude *</label>
                <InputNumber
                  v-model="formData.longitude"
                  :min="-180"
                  :max="180"
                  :step="0.0001"
                  class="w-full"
                />
              </div>
            </div>

            <div class="field">
              <label>Address</label>
              <Textarea
                v-model="formData.address"
                placeholder="Full address"
                rows="3"
                class="w-full"
              />
            </div>
          </div>
        </div>

        <!-- Form actions are in the header -->
      </form>
    </div>
    <!-- AI Overwrite Confirmation Dialog -->
    <Dialog
      v-model:visible="aiOverwriteDialogVisible"
      header="AI Populate — Existing Data"
      :modal="true"
      :style="{ width: '90vw', maxWidth: '480px' }"
    >
      <p>Some fields already have data. How would you like to proceed?</p>
      <div class="ai-overwrite-fields" v-if="fieldsToOverwrite.length">
        <p class="overwrite-label">Fields with existing data:</p>
        <ul>
          <li v-for="f in fieldsToOverwrite" :key="f">{{ f }}</li>
        </ul>
      </div>
      <div class="ai-dialog-actions">
        <Button label="Overwrite" icon="pi pi-pencil" @click="applyAIData(true)" severity="warning" />
        <Button label="Fill Empty" icon="pi pi-plus" @click="applyAIData(false)" />
        <Button label="Cancel" icon="pi pi-times" @click="aiOverwriteDialogVisible = false" severity="secondary" />
      </div>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDestinationsStore } from '@/stores/destinations'
import { useCustomFieldsStore } from '@/stores/customFields'
import { useGeocoding } from '@/composables/useGeocoding'
import { useApi } from '@/composables/useApi'
import { useToast } from 'primevue/usetoast'
import MapComponent from '@/components/MapComponent.vue'
import LinkManager from '@/components/LinkManager.vue'
import RichTextEditor from '@/components/RichTextEditor.vue'

const route = useRoute()
const router = useRouter()
const destinationsStore = useDestinationsStore()
const customFieldsStore = useCustomFieldsStore()
const { searchLocation } = useGeocoding()
const { addLink: apiAddLink, aiPopulate } = useApi()
const toast = useToast()

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

const isEdit = computed(() => !!route.params.id)

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

const locationSearch = ref('')
const geocodingResults = ref([])
const selectedTags = ref([])
const newTagInput = ref('')
const selectedMapPosition = ref(null)
const localLinks = ref([])
const newLink = reactive({ url: '', title: '' })
const plannedEndDateRef = ref(null)
const visitedEndDateRef = ref(null)

// AI populate state
const aiLoading = ref(false)
const aiOverwriteDialogVisible = ref(false)
const aiPendingData = ref(null)
const fieldsToOverwrite = ref([])

const formData = reactive({
  name: '',
  status: 'suggested',
  country: '',
  region: '',
  city: '',
  description: '',
  latitude: 0,
  longitude: 0,
  address: '',
  priority: null,
  cost_estimate: null,
  rating: null,
  best_season: [],
  date_researched: null,
  planned_start_date: null,
  planned_end_date: null,
  visited_start_date: null,
  visited_end_date: null,
  custom_fields_values: {},
  links: []
})

// Auto-stage next day and focus end date when start date is picked
watch(() => formData.planned_start_date, (newVal, oldVal) => {
  if (newVal && !oldVal && plannedEndDateRef.value) {
    const nextDay = new Date(newVal)
    nextDay.setDate(nextDay.getDate() + 1)
    formData.planned_end_date = nextDay
    nextTick(() => {
      const el = plannedEndDateRef.value?.$el || plannedEndDateRef.value
      const input = el?.querySelector?.('input')
      if (input) input.focus()
    })
  }
})

watch(() => formData.visited_start_date, (newVal, oldVal) => {
  if (newVal && !oldVal && visitedEndDateRef.value) {
    const nextDay = new Date(newVal)
    nextDay.setDate(nextDay.getDate() + 1)
    formData.visited_end_date = nextDay
    nextTick(() => {
      const el = visitedEndDateRef.value?.$el || visitedEndDateRef.value
      const input = el?.querySelector?.('input')
      if (input) input.focus()
    })
  }
})

const customFieldValues = reactive({})

const customFields = computed(() => customFieldsStore.fields)
const existingTags = computed(() => destinationsStore.tags)

const availableTagSuggestions = computed(() => {
  const existing = (existingTags.value || []).map(t => typeof t === 'string' ? t : t.name)
  return existing.filter(t => !selectedTags.value.includes(t))
})

const addTag = () => {
  const tag = newTagInput.value.trim()
  if (tag && !selectedTags.value.includes(tag)) {
    selectedTags.value.push(tag)
  }
  newTagInput.value = ''
}

const removeTag = (tag) => {
  selectedTags.value = selectedTags.value.filter(t => t !== tag)
}

const addLocalLink = () => {
  if (!newLink.url) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'URL is required', life: 3000 })
    return
  }
  localLinks.value.push({ ...newLink })
  newLink.url = ''
  newLink.title = ''
}

const refreshLinks = async () => {
  if (isEdit.value) {
    await destinationsStore.fetchDestination(route.params.id)
    formData.links = destinationsStore.currentDestination?.links || []
  }
}

const isPlanned = computed(() => formData.status === 'planned')
const isVisited = computed(() => formData.status === 'visited')

const getCustomFieldValue = (fieldId) => {
  return customFieldValues[fieldId] || ''
}

const updateCustomField = (fieldId, value) => {
  customFieldValues[fieldId] = value
}

const createMapMarker = () => ({
  id: 'temp',
  name: formData.name || 'Location',
  latitude: formData.latitude,
  longitude: formData.longitude,
  status: formData.status
})

const handleMapClick = (pos) => {
  formData.latitude = pos.lat
  formData.longitude = pos.lng
  selectedMapPosition.value = pos
}

const geocodeLocation = async () => {
  if (!locationSearch.value) return

  try {
    geocodingResults.value = await searchLocation(locationSearch.value)
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to search location',
      life: 3000
    })
  }
}

const selectGeocodingResult = (result) => {
  formData.latitude = parseFloat(result.lat)
  formData.longitude = parseFloat(result.lon)
  formData.address = result.display_name
  geocodingResults.value = []
  selectedMapPosition.value = { lat: formData.latitude, lng: formData.longitude }
}

// Format a Date object to YYYY-MM-DD string, or return null
const formatDateOnly = (val) => {
  if (!val) return null
  if (val instanceof Date) {
    const y = val.getFullYear()
    const m = String(val.getMonth() + 1).padStart(2, '0')
    const d = String(val.getDate()).padStart(2, '0')
    return `${y}-${m}-${d}`
  }
  // Already a string — return as-is
  return val
}

// AI Populate
const handleAIPopulate = async () => {
  if (!formData.latitude && !formData.longitude) {
    toast.add({ severity: 'warn', summary: 'Warning', detail: 'Set a location on the map first', life: 3000 })
    return
  }

  aiLoading.value = true
  try {
    const response = await aiPopulate({
      latitude: formData.latitude,
      longitude: formData.longitude,
      location_name: formData.name || null,
      country: formData.country || null
    })
    const data = response.data

    // Check which fields already have data
    const conflicts = []
    if (formData.name && data.name) conflicts.push('Name')
    if (formData.country && data.country) conflicts.push('Country')
    if (formData.region && data.region) conflicts.push('Region')
    if (formData.city && data.city) conflicts.push('City')
    if (formData.description && data.description) conflicts.push('Description')
    if (selectedTags.value.length && data.tags?.length) conflicts.push('Tags')
    if (formData.best_season?.length && data.best_season?.length) conflicts.push('Best Season')

    aiPendingData.value = data

    if (conflicts.length > 0) {
      fieldsToOverwrite.value = conflicts
      aiOverwriteDialogVisible.value = true
    } else {
      // No conflicts — apply everything directly
      applyAIData(true)
    }
  } catch (error) {
    const detail = error.response?.data?.detail || 'AI populate failed. Check your API key in Settings.'
    toast.add({ severity: 'error', summary: 'AI Error', detail, life: 5000 })
  } finally {
    aiLoading.value = false
  }
}

const plainTextToHtml = (text) => {
  if (!text) return text
  // If it already looks like HTML, return as-is
  if (text.trim().startsWith('<')) return text

  const knownHeadings = ['overview', 'safety', 'food', 'best time to visit']
  const blocks = text.split(/\n\n+/)
  let html = ''

  for (const block of blocks) {
    const trimmed = block.trim()
    if (!trimmed) continue
    // Check if this block is a heading (single short line matching known headings)
    const lower = trimmed.toLowerCase().replace(/[:\-*#]+/g, '').trim()
    if (knownHeadings.includes(lower) && !trimmed.includes('. ')) {
      html += `<h3>${trimmed.replace(/^[#*]+\s*/, '')}</h3>`
    } else {
      // Convert single newlines within a block to <br> for line breaks
      const content = trimmed.replace(/\n/g, '<br>')
      html += `<p>${content}</p>`
    }
  }

  return html || `<p>${text}</p>`
}

const applyAIData = (overwrite) => {
  const data = aiPendingData.value
  if (!data) return

  if (overwrite || !formData.name) formData.name = data.name || formData.name
  if (overwrite || !formData.country) formData.country = data.country || formData.country
  if (overwrite || !formData.region) formData.region = data.region || formData.region
  if (overwrite || !formData.city) formData.city = data.city || formData.city
  if (overwrite || !formData.description) formData.description = plainTextToHtml(data.description) || formData.description
  if (overwrite || !selectedTags.value.length) {
    if (data.tags?.length) {
      selectedTags.value = [...data.tags]
    }
  }
  if (overwrite || !formData.best_season?.length) {
    if (data.best_season?.length) {
      formData.best_season = [...data.best_season]
    }
  }

  aiOverwriteDialogVisible.value = false
  aiPendingData.value = null
  fieldsToOverwrite.value = []

  toast.add({ severity: 'success', summary: 'AI Populate', detail: 'Destination fields updated from AI', life: 3000 })
}

const submitForm = async () => {
  if (!formData.name || !formData.status || formData.latitude === null || formData.longitude === null) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Please fill in required fields (Name, Status, Location)',
      life: 3000
    })
    return
  }

  try {
    // Build clean payload matching the backend schema
    const data = {
      name: formData.name,
      status: formData.status,
      country: formData.country || 'Unknown',
      region: formData.region || null,
      city: formData.city || null,
      description: formData.description || null,
      latitude: formData.latitude,
      longitude: formData.longitude,
      address: formData.address || null,
      priority: formData.priority || null,
      cost_estimate: formData.cost_estimate || null,
      rating: formData.rating || null,
      best_season: formData.best_season.length ? formData.best_season : null,
      date_researched: formData.date_researched ? formData.date_researched.toISOString() : null,
      planned_start_date: formatDateOnly(formData.planned_start_date),
      planned_end_date: formatDateOnly(formData.planned_end_date),
      visited_start_date: formatDateOnly(formData.visited_start_date),
      visited_end_date: formatDateOnly(formData.visited_end_date),
      tags: selectedTags.value,
      custom_field_values: { ...customFieldValues }
    }

    if (isEdit.value) {
      await destinationsStore.updateCurrentDestination(route.params.id, data)
      toast.add({
        severity: 'success',
        summary: 'Success',
        detail: 'Destination updated',
        life: 3000
      })
      router.push(`/destinations/${route.params.id}`)
    } else {
      const result = await destinationsStore.createNewDestination(data)

      // Save any local links after destination is created
      if (localLinks.value.length && result.id) {
        for (const link of localLinks.value) {
          try {
            await apiAddLink(result.id, link)
          } catch (e) {
            console.error('Failed to save link:', e)
          }
        }
      }

      toast.add({
        severity: 'success',
        summary: 'Success',
        detail: 'Destination created',
        life: 3000
      })
      router.push(`/destinations/${result.id}`)
    }
  } catch (error) {
    if (isAccessRevoked(error)) return
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to save destination',
      life: 3000
    })
  }
}

onMounted(async () => {
  try {
    await Promise.all([
      destinationsStore.fetchTags(),
      customFieldsStore.fetchFields()
    ])

    if (isEdit.value) {
      await destinationsStore.fetchDestination(route.params.id)
      const dest = destinationsStore.currentDestination
      if (dest) {
        formData.name = dest.name
        formData.status = dest.status
        formData.country = dest.country
        formData.region = dest.region
        formData.city = dest.city
        formData.description = dest.description
        formData.latitude = dest.latitude
        formData.longitude = dest.longitude
        formData.address = dest.address
        formData.priority = dest.priority
        formData.cost_estimate = dest.cost_estimate
        formData.rating = dest.rating
        formData.best_season = dest.best_season || []
        formData.date_researched = dest.date_researched ? new Date(dest.date_researched) : null
        formData.planned_start_date = dest.planned_start_date ? new Date(dest.planned_start_date) : null
        formData.planned_end_date = dest.planned_end_date ? new Date(dest.planned_end_date) : null
        formData.visited_start_date = dest.visited_start_date ? new Date(dest.visited_start_date) : null
        formData.visited_end_date = dest.visited_end_date ? new Date(dest.visited_end_date) : null
        selectedTags.value = dest.tags || []
        formData.links = dest.links || []

        if (dest.custom_fields) {
          dest.custom_fields.forEach(field => {
            customFieldValues[field.field_id] = field.value
          })
        }

        selectedMapPosition.value = { lat: dest.latitude, lng: dest.longitude }
      }
    }
  } catch (error) {
    if (isAccessRevoked(error)) return
    console.error('Error loading data:', error)
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to load data',
      life: 3000
    })
  }
})
</script>

<style scoped>
.destination-form-page {
  min-height: 100vh;
  background: var(--color-bg);
}

.form-header {
  background: var(--color-bg-elevated);
  border-bottom: 1px solid var(--color-border);
  padding: 1rem 0;
  position: sticky;
  top: 64px;
  z-index: 50;
}

.form-header-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 1rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.form-header h1 {
  margin: 0;
  font-size: 1.5rem;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
  flex-shrink: 0;
}

.header-actions a {
  text-decoration: none;
}

.form-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}

.form-layout {
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 2rem;
  margin-bottom: 2rem;
}

.form-section {
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.form-section h2 {
  margin: 0 0 1.5rem 0;
  font-size: 1.125rem;
  color: var(--color-text-bright);
}

.field {
  margin-bottom: 1.5rem;
}

.field:last-child {
  margin-bottom: 0;
}

.field label {
  display: block;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: var(--color-text-bright);
  font-size: 0.875rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.flex-1 {
  flex: 1;
}

.w-full {
  width: 100%;
}

.field :deep(.p-inputtext),
.field :deep(.p-inputnumber),
.field :deep(.p-inputtextarea),
.field :deep(.p-dropdown),
.field :deep(.p-multiselect),
.field :deep(.p-calendar) {
  width: 100%;
  font-size: 0.875rem;
}

.links-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.local-link-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: 0.375rem;
  background: var(--color-bg-light);
}

.local-link-content {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.local-link-url {
  color: var(--color-accent-hover);
  font-size: 0.875rem;
  text-decoration: none;
}

.local-link-desc {
  margin: 0;
  color: var(--color-text-muted);
  font-size: 0.875rem;
}

.empty-links {
  text-align: center;
  padding: 1rem;
  color: var(--color-text-muted);
  border: 2px dashed var(--color-border);
  border-radius: 0.5rem;
  margin-bottom: 1rem;
}

.empty-links p {
  margin: 0;
}

.local-link-form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1rem;
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  background: var(--color-bg-light);
}

.tags-input-container {
  border: 1px solid var(--color-border);
  border-radius: 0.375rem;
  padding: 0.5rem;
  background: var(--color-bg-light);
}

.tags-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
  margin-bottom: 0.5rem;
}

.tags-chips:empty {
  margin-bottom: 0;
}

.tags-input-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.geocoding-input {
  display: flex;
  gap: 0.5rem;
  align-items: stretch;
}

.geocoding-input .p-button {
  flex-shrink: 0;
}

.geocoding-field {
  position: relative;
}

.geocoding-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: 0.375rem;
  max-height: 250px;
  overflow-y: auto;
  z-index: 50;
  margin-top: 0.25rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

.result-item {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--color-border);
  cursor: pointer;
  transition: background 0.2s;
  font-size: 0.875rem;
  color: var(--color-text);
}

.result-item:hover {
  background: var(--color-bg-hover);
}

.result-item:last-child {
  border-bottom: none;
}

.form-left {
  grid-column: 1;
}

.form-right {
  grid-column: 2;
  grid-row: 1 / 999;
}


.section-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 0 0 1.5rem 0;
}

.section-header-row h2 {
  margin: 0;
}

.ai-overwrite-fields {
  margin: 1rem 0;
  padding: 0.75rem;
  background: var(--color-bg-light);
  border: 1px solid var(--color-border);
  border-radius: 0.375rem;
}

.overwrite-label {
  margin: 0 0 0.5rem 0;
  font-weight: 600;
  font-size: 0.875rem;
  color: var(--color-text-bright);
}

.ai-overwrite-fields ul {
  margin: 0;
  padding-left: 1.25rem;
  color: var(--color-text);
  font-size: 0.875rem;
}

.ai-overwrite-fields li {
  margin: 0.25rem 0;
}

.ai-dialog-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1.25rem;
}

.ai-dialog-actions button {
  flex: 1;
}

@media (max-width: 1024px) {
  .form-layout {
    grid-template-columns: 1fr;
  }

  .form-right {
    grid-column: 1;
    grid-row: auto;
  }
}

@media (max-width: 768px) {
  .form-header-content {
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .form-header h1 {
    font-size: 1.125rem;
    width: 100%;
  }

  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .header-actions :deep(.p-button .p-button-label) {
    font-size: 0.8rem;
  }

  .form-container {
    padding: 0.5rem;
  }

  .form-layout {
    grid-template-columns: 1fr;
    gap: 0.5rem;
  }

  .form-section {
    padding: 1rem;
    margin-bottom: 0;
  }

  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
