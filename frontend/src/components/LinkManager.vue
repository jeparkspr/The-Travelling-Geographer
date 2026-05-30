<template>
  <div
    class="link-manager"
    :class="{ 'drag-over': dragOver }"
    @dragover.prevent="dragOver = true"
    @dragenter.prevent="dragOver = true"
    @dragleave.prevent="dragOver = false"
    @drop.prevent="onDrop"
  >
    <!-- Drop indicator -->
    <div v-if="dropping" class="drop-status">
      <i class="pi pi-spin pi-spinner"></i>
      <span>Adding link...</span>
    </div>

    <!-- Links List -->
    <div v-if="links && links.length" class="links-list">
      <div v-for="link in links" :key="link.id" class="link-item">
        <div class="link-content">
          <div class="link-header">
            <h4 class="link-title">{{ link.title }}</h4>
            <div v-if="editable" class="link-actions">
              <Button
                icon="pi pi-pencil"
                text
                size="small"
                @click="editLink(link)"
              />
              <Button
                icon="pi pi-trash"
                text
                severity="danger"
                size="small"
                @click="confirmDelete(link.id)"
              />
            </div>
          </div>
          <a :href="link.url" target="_blank" class="link-url">
            {{ link.url }}
            <i class="pi pi-external-link"></i>
          </a>
          <div v-if="link.image_url" class="link-preview">
            <img :src="link.image_url" :alt="link.title" />
          </div>
          <Button
            v-if="editable"
            icon="pi pi-refresh"
            label="Fetch Image"
            text
            size="small"
            @click="fetchImage(link.id)"
            :loading="fetchingImageId === link.id"
          />
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="empty-state">
      <p>No links added yet</p>
    </div>

    <!-- Add/Edit Form -->
    <div v-if="editable" class="link-form">
      <h4>{{ editingLink ? 'Edit Link' : 'Add Link' }}</h4>
      <div class="form-fields">
        <div class="field">
          <label>URL</label>
          <InputText
            v-model="formData.url"
            placeholder="https://example.com"
            class="w-full"
          />
        </div>
        <div class="field">
          <label>Title</label>
          <InputText
            v-model="formData.title"
            placeholder="Link title"
            class="w-full"
          />
        </div>
        <div class="form-actions">
          <Button
            :label="editingLink ? 'Save' : 'Add'"
            @click="saveLink"
            class="mb-2"
          />
          <Button
            v-if="editingLink"
            label="Cancel"
            severity="secondary"
            @click="cancelEdit"
          />
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useApi } from '@/composables/useApi'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'

const props = defineProps({
  links: {
    type: Array,
    default: () => []
  },
  destinationId: {
    type: String,
    required: true
  },
  editable: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['updated'])

const { addLink, updateLink, deleteLink, fetchLinkImage } = useApi()
const confirm = useConfirm()
const toast = useToast()

const editingLink = ref(null)
const fetchingImageId = ref(null)
const dragOver = ref(false)
const dropping = ref(false)
const formData = reactive({
  url: '',
  title: ''
})

const extractUrl = (dataTransfer) => {
  // Try text/uri-list first, then text/plain
  let url = dataTransfer.getData('text/uri-list') || dataTransfer.getData('text/plain') || ''
  url = url.trim().split('\n')[0].trim()
  if (url && (url.startsWith('http://') || url.startsWith('https://'))) {
    return url
  }
  return null
}

const onDrop = async (event) => {
  dragOver.value = false
  const url = extractUrl(event.dataTransfer)
  if (!url) return

  dropping.value = true
  try {
    // Use the URL's hostname as a default title
    let title = ''
    try {
      title = new URL(url).hostname.replace(/^www\./, '')
    } catch { title = url }

    await addLink(props.destinationId, { url, title })
    toast.add({ severity: 'success', summary: 'Success', detail: 'Link added', life: 3000 })
    emit('updated')
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to add link', life: 3000 })
  } finally {
    dropping.value = false
  }
}

const resetForm = () => {
  formData.url = ''
  formData.title = ''
  editingLink.value = null
}

const editLink = (link) => {
  editingLink.value = link.id
  formData.url = link.url
  formData.title = link.title
}

const cancelEdit = () => {
  resetForm()
}

const saveLink = async () => {
  if (!formData.url || !formData.title) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'URL and Title are required',
      life: 3000
    })
    return
  }

  try {
    if (editingLink.value) {
      await updateLink(props.destinationId, editingLink.value, {
        url: formData.url,
        title: formData.title
      })
      toast.add({
        severity: 'success',
        summary: 'Success',
        detail: 'Link updated',
        life: 3000
      })
    } else {
      await addLink(props.destinationId, {
        url: formData.url,
        title: formData.title
      })
      toast.add({
        severity: 'success',
        summary: 'Success',
        detail: 'Link added',
        life: 3000
      })
    }

    resetForm()
    emit('updated')
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to save link',
      life: 3000
    })
  }
}

const fetchImage = async (linkId) => {
  fetchingImageId.value = linkId
  try {
    await fetchLinkImage(props.destinationId, linkId)
    toast.add({
      severity: 'success',
      summary: 'Success',
      detail: 'Image fetched successfully',
      life: 3000
    })
    emit('updated')
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to fetch image',
      life: 3000
    })
  } finally {
    fetchingImageId.value = null
  }
}

const confirmDelete = (linkId) => {
  confirm.require({
    message: 'Are you sure you want to delete this link?',
    header: 'Confirm',
    icon: 'pi pi-exclamation-triangle',
    accept: async () => {
      try {
        await deleteLink(props.destinationId, linkId)
        toast.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Link deleted',
          life: 3000
        })
        emit('updated')
      } catch (error) {
        toast.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to delete link',
          life: 3000
        })
      }
    }
  })
}
</script>

<style scoped>
.link-manager {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  border-radius: 0.5rem;
  padding: 0.25rem;
  transition: outline 0.15s, background 0.15s;
}

.link-manager.drag-over {
  outline: 2px dashed var(--color-accent);
  outline-offset: -2px;
  background: rgba(59, 130, 246, 0.05);
}

.drop-status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem;
  color: var(--color-accent);
  font-size: 0.875rem;
}

.links-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.link-item {
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  padding: 1rem;
  background: var(--color-bg-light);
}

.link-content {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.link-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.link-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text-bright);
}

.link-actions {
  display: flex;
  gap: 0.25rem;
  flex-shrink: 0;
}

.link-url {
  color: var(--color-accent-hover);
  text-decoration: none;
  font-size: 0.875rem;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  transition: color 0.2s;
}

.link-url:hover {
  color: var(--color-accent-hover);
  text-decoration: underline;
}

.link-url i {
  font-size: 0.75rem;
}

.link-preview {
  margin: 0.75rem 0;
}

.link-preview img {
  max-width: 100%;
  max-height: 150px;
  border-radius: 0.375rem;
  object-fit: cover;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: var(--color-text-muted);
  border: 2px dashed var(--color-border);
  border-radius: 0.5rem;
  background: var(--color-bg-light);
}

.link-form {
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  padding: 1rem;
  background: var(--color-bg-light);
}

.link-form h4 {
  margin: 0 0 1rem 0;
  font-size: 1rem;
}

.form-fields {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.field label {
  font-weight: 600;
  font-size: 0.875rem;
  color: var(--color-text-bright);
}

.field :deep(.p-inputtext),
.field :deep(.p-inputtextarea) {
  font-size: 0.875rem;
}

.form-actions {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.mb-2 {
  margin-bottom: 0.5rem;
}

.w-full {
  width: 100%;
}
</style>
