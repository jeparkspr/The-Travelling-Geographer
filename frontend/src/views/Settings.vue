<template>
  <div class="settings-page">
    <div class="container py-4">
      <h1 class="page-title">Settings</h1>

      <Tabs value="general">
        <TabList>
          <Tab value="general">General</Tab>
          <Tab value="data">{{ authStore.isAdmin ? 'Backup & Restore' : 'Export' }}</Tab>
          <Tab value="ai">AI</Tab>
          <Tab value="bookmarklet">Bookmarklet</Tab>
          <Tab value="tags">Tags</Tab>
          <Tab value="custom-fields">Custom Fields</Tab>
        </TabList>
        <TabPanels>
        <!-- General Tab -->
        <TabPanel value="general">
          <div class="tab-content">
            <h2>General</h2>
            <div class="toggle-settings">
              <div class="toggle-row">
                <ToggleSwitch v-model="darkMode" inputId="darkMode" />
                <div class="toggle-label">
                  <label for="darkMode">Dark mode</label>
                  <p class="field-hint">Toggle between dark and light appearance.</p>
                </div>
              </div>

              <div class="toggle-row">
                <ToggleSwitch v-model="showArchived" inputId="showArchived" />
                <div class="toggle-label">
                  <label for="showArchived">Show archived destinations</label>
                  <p class="field-hint">When off, archived destinations are hidden from all views.</p>
                </div>
              </div>

              <div class="toggle-row">
                <ToggleSwitch v-model="showToasts" inputId="showToasts" />
                <div class="toggle-label">
                  <label for="showToasts">Show notification pop-ups</label>
                  <p class="field-hint">When off, success, info, and error notifications are hidden.</p>
                </div>
              </div>

              <div class="toggle-row">
                <ToggleSwitch v-model="useMetricUnits" inputId="useMetricUnits" />
                <div class="toggle-label">
                  <label for="useMetricUnits">Metric units</label>
                  <p class="field-hint">Show map scale in kilometers. When off, scale is shown in miles.</p>
                </div>
              </div>
            </div>
          </div>
        </TabPanel>

        <!-- Custom Fields Tab -->
        <TabPanel value="custom-fields">
          <div class="tab-content">
            <div class="section-header">
              <h2>Custom Fields</h2>
              <Button
                icon="pi pi-plus"
                label="Add Field"
                @click="openFieldForm"
              />
            </div>

            <div v-if="customFields.length" class="fields-list">
              <div v-for="field in customFields" :key="field.id" class="field-item">
                <div class="field-info">
                  <h4>{{ field.field_name || field.name }}</h4>
                  <p>Type: {{ field.field_type }}</p>
                </div>
                <div class="field-actions">
                  <Button
                    icon="pi pi-pencil"
                    text
                    severity="info"
                    @click="editField(field)"
                  />
                  <Button
                    icon="pi pi-trash"
                    text
                    severity="danger"
                    @click="confirmDeleteField(field.id)"
                  />
                </div>
              </div>
            </div>

            <div v-else class="empty-state">
              <p>No custom fields yet</p>
            </div>

            <!-- Field Form Dialog -->
            <Dialog
              v-model:visible="fieldFormOpen"
              :header="editingField ? 'Edit Field' : 'New Custom Field'"
              :modal="true"
              :style="{ width: '90vw', maxWidth: '500px' }"
            >
              <div class="form">
                <div class="field">
                  <label>Field Name</label>
                  <InputText
                    v-model="fieldForm.name"
                    placeholder="e.g., Budget"
                    class="w-full"
                  />
                </div>
                <div class="field">
                  <label>Field Type</label>
                  <Dropdown
                    v-model="fieldForm.field_type"
                    :options="['text', 'select']"
                    class="w-full"
                  />
                </div>
                <div v-if="fieldForm.field_type === 'select'" class="field">
                  <label>Options (comma-separated)</label>
                  <Textarea
                    v-model="fieldForm.optionsText"
                    rows="3"
                    placeholder="Option 1, Option 2, Option 3"
                    class="w-full"
                  />
                </div>
                <div class="dialog-actions">
                  <Button label="Save" @click="saveField" />
                  <Button label="Cancel" severity="secondary" @click="fieldFormOpen = false" />
                </div>
              </div>
            </Dialog>
          </div>
        </TabPanel>

        <!-- Tags Tab -->
        <TabPanel value="tags">
          <div class="tab-content tags-tab-content">
            <div class="tags-fixed-header">
              <div class="section-header">
                <h2>Tags</h2>
                <span class="tag-total">{{ allTags.length }} tag(s)</span>
              </div>

              <!-- Toolbar: search, sort, bulk actions -->
              <div class="tags-toolbar">
                <span class="tags-search">
                  <i class="pi pi-search tags-search-label"></i>
                </span>
                <InputText
                  v-model="tagSearch"
                  placeholder="Search tags..."
                  class="tags-search-input"
                />
                <Dropdown
                  v-model="tagSortMode"
                  :options="[
                    { label: 'A → Z', value: 'alpha-asc' },
                    { label: 'Z → A', value: 'alpha-desc' },
                    { label: 'Count (high to low)', value: 'count-desc' },
                    { label: 'Count (low to high)', value: 'count-asc' },
                  ]"
                  optionLabel="label"
                  optionValue="value"
                  class="tags-sort-dropdown"
                />
                <template v-if="authStore.isAdmin">
                  <Button
                    v-if="selectedTags.length >= 2"
                    icon="pi pi-arrows-h"
                    :label="`Merge ${selectedTags.length}...`"
                    size="small"
                    severity="info"
                    @click="openMergeDialog"
                  />
                  <Button
                    icon="pi pi-trash"
                    label="Delete unused"
                    size="small"
                    severity="danger"
                    outlined
                    @click="confirmDeleteUnused"
                    :disabled="unusedTagCount === 0"
                  />
                </template>
              </div>
            </div>

            <div class="tags-scroll-area">
              <div v-if="tagsLoading" class="empty-state">
                <p>Loading tags...</p>
              </div>

              <div v-else-if="tagsWithCounts.length" class="tags-list">
              <div v-for="tag in tagsWithCounts" :key="tag.id" class="tag-item">
                <Checkbox
                  v-if="authStore.isAdmin"
                  :modelValue="selectedTags.includes(tag.name)"
                  @update:modelValue="toggleTagSelection(tag.name)"
                  :binary="true"
                  class="tag-checkbox"
                />
                <div class="tag-info" v-if="editingTagId !== tag.id">
                  <a class="tag-name tag-link" @click.prevent="router.push({ path: '/destinations', query: { tag: tag.name } })" href="#">{{ tag.name }}</a>
                  <span class="tag-count">{{ tag.count }} destination(s)</span>
                </div>
                <div class="tag-edit-row" v-else>
                  <InputText
                    v-model="editingTagName"
                    class="tag-edit-input"
                    @keyup.enter="submitTagRename(tag)"
                    @keyup.escape="cancelTagEdit"
                    autofocus
                  />
                </div>
                <div class="tag-actions">
                  <template v-if="editingTagId !== tag.id">
                    <Button
                      icon="pi pi-pencil"
                      text
                      severity="secondary"
                      @click="startTagEdit(tag)"
                      title="Rename tag"
                    />
                    <Button
                      icon="pi pi-trash"
                      text
                      severity="danger"
                      @click="confirmDeleteTag(tag.name)"
                    />
                  </template>
                  <template v-else>
                    <Button
                      icon="pi pi-check"
                      text
                      severity="success"
                      @click="submitTagRename(tag)"
                      title="Save"
                    />
                    <Button
                      icon="pi pi-times"
                      text
                      severity="secondary"
                      @click="cancelTagEdit"
                      title="Cancel"
                    />
                  </template>
                </div>
              </div>
            </div>

              <div v-else class="empty-state">
                <p>{{ tagSearch ? 'No tags match your search' : 'No tags yet' }}</p>
              </div>
            </div>

            <!-- Bulk Merge Dialog -->
            <Dialog
              v-model:visible="mergeDialogOpen"
              header="Merge Tags"
              :modal="true"
              :style="{ width: '90vw', maxWidth: '450px' }"
            >
              <div class="merge-dialog">
                <p>Merge the following {{ mergeSourceTags.length }} tag(s) into a single tag:</p>
                <div class="merge-source-tags">
                  <span v-for="t in mergeSourceTags" :key="t" class="merge-tag-chip">{{ t }}</span>
                </div>
                <div class="field">
                  <label>Target tag name</label>
                  <InputText
                    v-model="mergeTargetName"
                    placeholder="Enter target tag name..."
                    class="w-full"
                    @keyup.enter="submitBulkMerge"
                  />
                  <p class="field-hint">All selected tags will be replaced with this tag on every destination.</p>
                </div>
                <div class="dialog-actions">
                  <Button label="Merge" icon="pi pi-arrows-h" @click="submitBulkMerge" />
                  <Button label="Cancel" severity="secondary" @click="mergeDialogOpen = false" />
                </div>
              </div>
            </Dialog>
          </div>
        </TabPanel>

        <!-- Backup & Restore Tab -->
        <TabPanel value="data">
          <div class="tab-content">
            <template v-if="authStore.isAdmin">
              <div class="section">
                <h2>Backup</h2>
                <p>Download all your data and media files as a single compressed archive.</p>
                <Button
                  icon="pi pi-download"
                  label="Backup"
                  @click="handleBackup"
                  severity="info"
                  :loading="backupLoading"
                  :disabled="backupLoading"
                />
                <div v-if="backupProgress" class="backup-progress">
                  <div class="progress-bar-track">
                    <div
                      class="progress-bar-fill"
                      :style="{ width: backupPercent + '%' }"
                    ></div>
                  </div>
                  <div class="progress-info">
                    <span>{{ backupProgress.filesDone }} / {{ backupProgress.totalFiles }} files</span>
                    <span>{{ backupPercent }}%</span>
                  </div>
                  <div class="progress-file">{{ backupProgress.currentFile }}</div>
                </div>
              </div>

              <div class="section">
                <h2>Restore</h2>
                <p>Restore all data and media from a previously created backup archive.</p>
                <FileUpload
                  name="restoreFile"
                  mode="basic"
                  accept=".tgz"
                  :auto="false"
                  choose-label="Select Backup File"
                  @select="onRestoreFileSelected"
                  class="import-upload"
                  :disabled="restoreLoading"
                />
                <div v-if="selectedRestoreFile && !restoreProgress" class="file-info">
                  <p>Selected: {{ selectedRestoreFile.name }}</p>
                </div>
                <Button
                  v-if="selectedRestoreFile && !restoreLoading"
                  icon="pi pi-upload"
                  label="Restore"
                  @click="handleRestore"
                  severity="success"
                  class="restore-btn"
                />
                <div v-if="restoreProgress" class="backup-progress">
                  <div class="progress-bar-track">
                    <div
                      class="progress-bar-fill"
                      :style="{ width: restorePercent + '%' }"
                    ></div>
                  </div>
                  <div class="progress-info">
                    <span>{{ restoreProgress.filesDone }} / {{ restoreProgress.totalFiles }} files</span>
                    <span>{{ restorePercent }}%</span>
                  </div>
                  <div class="progress-file">{{ restoreProgress.currentFile }}</div>
                </div>
              </div>
            </template>

            <div class="section">
              <h2>Export</h2>
              <p>Export all destinations as a CSV file.</p>
              <Button
                icon="pi pi-file-export"
                label="Export CSV"
                @click="openExportDialog"
                severity="info"
              />
            </div>

            <!-- Export CSV Dialog -->
            <Dialog
              v-model:visible="exportDialogVisible"
              header="Export Destinations to CSV"
              :modal="true"
              :style="{ width: '90vw', maxWidth: '480px' }"
            >
              <div class="export-dialog">
                <Button
                  icon="pi pi-download"
                  label="Export Now"
                  @click="handleExportCsv"
                  severity="info"
                  :loading="exportLoading"
                  :disabled="exportLoading || !exportSelectedFields.length"
                  class="export-now-btn"
                />

                <div class="export-toggle-links">
                  <a href="#" @click.prevent="selectAllExportFields">Select All</a>
                  <span>|</span>
                  <a href="#" @click.prevent="deselectAllExportFields">Deselect All</a>
                </div>

                <div class="export-fields-list">
                  <div v-for="field in exportAvailableFields" :key="field.key" class="export-field-item">
                    <Checkbox
                      v-model="exportSelectedFields"
                      :inputId="'export-' + field.key"
                      :value="field.key"
                    />
                    <label :for="'export-' + field.key">{{ field.label }}</label>
                  </div>
                </div>
              </div>
            </Dialog>
          </div>
        </TabPanel>

        <!-- AI Tab -->
        <TabPanel value="ai">
          <div class="tab-content">
            <h2>AI Assistant</h2>
            <p v-if="!authStore.isAdmin" class="ai-readonly-notice">As a regular user, you are not able to change the settings on this page. They are provided for your information only.</p>
            <p>Configure AI-powered destination information using Google Gemini.</p>

            <div class="section">
              <h3>Model</h3>
              <div class="ai-model-row">
                <Dropdown
                  v-model="geminiModel"
                  :options="modelOptions"
                  optionLabel="label"
                  optionValue="value"
                  class="ai-model-dropdown"
                  @change="saveModel"
                  :disabled="!authStore.isAdmin"
                />
              </div>
            </div>

            <div class="section">
              <h3>Gemini API Key</h3>
              <p>
                Get a free API key from
                <a href="https://aistudio.google.com/apikey" target="_blank" class="ai-link">Google AI Studio</a>.
              </p>
              <div class="ai-key-row">
                <InputText
                  v-model="geminiApiKey"
                  type="password"
                  placeholder="Enter your Gemini API key..."
                  class="ai-key-input"
                  :disabled="!authStore.isAdmin"
                />
              </div>
              <div class="ai-key-actions">
                <Button
                  label="Save Key"
                  icon="pi pi-save"
                  @click="saveApiKey"
                  size="small"
                  :disabled="!authStore.isAdmin"
                />
                <Button
                  label="Test Connection"
                  icon="pi pi-bolt"
                  severity="info"
                  @click="testConnection"
                  :loading="testingConnection"
                  size="small"
                />
              </div>
              <div v-if="connectionStatus" class="connection-status" :class="connectionStatus.success ? 'status-ok' : 'status-error'">
                <i :class="connectionStatus.success ? 'pi pi-check-circle' : 'pi pi-times-circle'"></i>
                {{ connectionStatus.message }}
              </div>
            </div>

            <div class="section">
              <h3>Prompt Template</h3>
              <p>This prompt is sent to Gemini when you use the AI populate button on the destination form. Available placeholders:</p>
              <div class="placeholder-list">
                <code>{location_name}</code> <code>{country}</code> <code>{latitude}</code> <code>{longitude}</code>
              </div>
              <Textarea
                v-model="aiPromptTemplate"
                rows="16"
                class="w-full ai-prompt-textarea"
                :disabled="!authStore.isAdmin"
              />
              <div class="ai-prompt-actions">
                <Button
                  label="Save Prompt"
                  icon="pi pi-save"
                  @click="savePromptTemplate"
                  size="small"
                  :disabled="!authStore.isAdmin"
                />
                <Button
                  label="Reset to Default"
                  icon="pi pi-refresh"
                  severity="secondary"
                  @click="resetPromptTemplate"
                  size="small"
                  :disabled="!authStore.isAdmin"
                />
              </div>
            </div>
          </div>
        </TabPanel>

        <!-- Bookmarklet Tab -->
        <TabPanel value="bookmarklet">
          <div class="tab-content">
            <h2>Web Clipper Bookmarklet</h2>

            <div class="section">
              <p>Use this bookmarklet to quickly save web pages to your wishlist.</p>

              <div class="form">
                <div class="field">
                  <label>Your App URL</label>
                  <InputText
                    v-model="appUrl"
                    placeholder="https://yourdomain.com"
                    class="w-full"
                  />
                </div>
              </div>

              <div class="bookmarklet-container">
                <h3>Instructions</h3>
                <ol>
                  <li>Right-click the button below and select "Bookmark This Link"</li>
                  <li>Name it something like "Save Travel Destination"</li>
                  <li>Click the bookmarklet while viewing any website to clip it</li>
                </ol>

                <div class="bookmarklet-button-container">
                  <a :href="bookmarkletCode" class="bookmarklet-btn" title="Bookmark this link">
                    Save Travel Destination
                  </a>
                </div>

                <details class="code-details">
                  <summary>Show Bookmarklet Code</summary>
                  <pre class="code-block">{{ bookmarkletCode }}</pre>
                  <Button
                    icon="pi pi-copy"
                    text
                    @click="copyBookmarklet"
                    label="Copy Code"
                  />
                </details>
              </div>
            </div>
          </div>
        </TabPanel>
        </TabPanels>
      </Tabs>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useApi } from '@/composables/useApi'
import { useCustomFieldsStore } from '@/stores/customFields'
import { useDestinationsStore } from '@/stores/destinations'
import { useSettingsStore } from '@/stores/settings'
import { useAuthStore } from '@/stores/auth'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'

const { createCustomField, updateCustomField, deleteCustomField, getExportFields, exportCsv, backupDownload: apiBackupDownload, restoreUpload: apiRestoreUpload, getTags, renameTag, deleteTag, deleteUnusedTags, bulkMergeTags, getAISettings, updateAISettings, testAIConnection } = useApi()
const customFieldsStore = useCustomFieldsStore()
const destinationsStore = useDestinationsStore()
const settingsStore = useSettingsStore()
const authStore = useAuthStore()
const router = useRouter()
const confirm = useConfirm()
const toast = useToast()

const fieldFormOpen = ref(false)
const editingField = ref(null)
const selectedRestoreFile = ref(null)
const exportDialogVisible = ref(false)
const exportAvailableFields = ref([])
const exportSelectedFields = ref([])
const exportLoading = ref(false)
const backupLoading = ref(false)
const backupProgress = ref(null) // { filesDone, totalFiles, currentFile }
const restoreLoading = ref(false)
const restoreProgress = ref(null) // { filesDone, totalFiles, currentFile }
const appUrl = ref(window.location.origin || 'https://yourdomain.com')
const editingTagId = ref(null)
const editingTagName = ref('')
const allTags = ref([]) // { name, count }[] from backend
const tagSearch = ref('')
const tagSortMode = ref('alpha-asc') // alpha-asc, alpha-desc, count-desc, count-asc
const selectedTags = ref([]) // names of selected tags for bulk merge
const mergeTargetName = ref('')
const mergeDialogOpen = ref(false)
const mergeSourceTags = ref([]) // snapshot of tags to merge
const tagsLoading = ref(false)

// AI settings
const geminiApiKey = ref('')
const aiPromptTemplate = ref('')
const defaultPromptTemplate = ref('')
const testingConnection = ref(false)
const connectionStatus = ref(null)
const geminiModel = ref('gemini-2.5-flash')
const modelOptions = [
  { label: 'Gemini 2.5 Flash', value: 'gemini-2.5-flash' },
  { label: 'Gemini Flash (Latest)', value: 'gemini-flash-latest' }
]

// General settings
const showArchived = ref(settingsStore.showArchived)
const showToasts = ref(settingsStore.showToasts)
const darkMode = ref(settingsStore.theme === 'dark')
const useMetricUnits = ref(settingsStore.useMetricUnits)
watch(showArchived, (val) => {
  settingsStore.setShowArchived(val)
})
watch(showToasts, (val) => {
  settingsStore.setShowToasts(val)
})
watch(darkMode, (val) => {
  settingsStore.setTheme(val ? 'dark' : 'light')
})
watch(useMetricUnits, (val) => {
  settingsStore.setUseMetricUnits(val)
})

const fieldForm = reactive({
  name: '',
  field_type: 'text',
  optionsText: ''
})

const customFields = computed(() => customFieldsStore.fields)
const destinations = computed(() => destinationsStore.destinations)

const tagsWithCounts = computed(() => {
  let tags = allTags.value

  // Filter by search
  if (tagSearch.value.trim()) {
    const q = tagSearch.value.trim().toLowerCase()
    tags = tags.filter(t => t.name.toLowerCase().includes(q))
  }

  // Sort
  const sorted = [...tags]
  switch (tagSortMode.value) {
    case 'count-desc':
      sorted.sort((a, b) => b.count - a.count || a.name.localeCompare(b.name))
      break
    case 'count-asc':
      sorted.sort((a, b) => a.count - b.count || a.name.localeCompare(b.name))
      break
    case 'alpha-asc':
      sorted.sort((a, b) => a.name.localeCompare(b.name))
      break
    case 'alpha-desc':
      sorted.sort((a, b) => b.name.localeCompare(a.name))
      break
  }

  return sorted
})

const unusedTagCount = computed(() => allTags.value.filter(t => t.count === 0).length)

const loadTags = async () => {
  tagsLoading.value = true
  try {
    const response = await getTags()
    // Backend returns { tagName: count, ... }
    allTags.value = Object.entries(response.data).map(([name, count]) => ({
      id: name,
      name,
      count,
    }))
  } catch (error) {
    console.error('Failed to load tags:', error)
  } finally {
    tagsLoading.value = false
  }
}

const backupPercent = computed(() => {
  if (!backupProgress.value || !backupProgress.value.totalFiles) return 0
  return Math.round((backupProgress.value.filesDone / backupProgress.value.totalFiles) * 100)
})

const restorePercent = computed(() => {
  if (!restoreProgress.value || !restoreProgress.value.totalFiles) return 0
  return Math.round((restoreProgress.value.filesDone / restoreProgress.value.totalFiles) * 100)
})

const bookmarkletCode = computed(() => {
  const code = `javascript:(function(){var u=encodeURIComponent(window.location.href);var t=encodeURIComponent(document.title);var d=encodeURIComponent((document.querySelector('meta[name="description"]')||{}).content||'');window.open('${appUrl.value}/clip?url='+u+'&title='+t+'&description='+d,'_blank');})();`
  return code
})

const openFieldForm = () => {
  editingField.value = null
  fieldForm.name = ''
  fieldForm.field_type = 'text'
  fieldForm.optionsText = ''
  fieldFormOpen.value = true
}

const editField = (field) => {
  editingField.value = field
  fieldForm.name = field.field_name || field.name
  fieldForm.field_type = field.field_type
  fieldForm.optionsText = (field.options || []).join(', ')
  fieldFormOpen.value = true
}

const saveField = async () => {
  if (!fieldForm.name) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Field name is required',
      life: 3000
    })
    return
  }

  try {
    const data = {
      field_name: fieldForm.name,
      field_key: fieldForm.name.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, ''),
      field_type: fieldForm.field_type,
      options: fieldForm.field_type === 'select'
        ? fieldForm.optionsText.split(',').map(o => o.trim())
        : []
    }

    if (editingField.value) {
      await customFieldsStore.updateField(editingField.value.id, data)
      toast.add({
        severity: 'success',
        summary: 'Success',
        detail: 'Field updated',
        life: 3000
      })
    } else {
      await customFieldsStore.createField(data)
      toast.add({
        severity: 'success',
        summary: 'Success',
        detail: 'Field created',
        life: 3000
      })
    }

    fieldFormOpen.value = false
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to save field',
      life: 3000
    })
  }
}

const confirmDeleteField = (fieldId) => {
  confirm.require({
    message: 'Are you sure you want to delete this field?',
    header: 'Confirm Delete',
    icon: 'pi pi-exclamation-triangle',
    accept: async () => {
      try {
        await customFieldsStore.deleteField(fieldId)
        toast.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Field deleted',
          life: 3000
        })
      } catch (error) {
        toast.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to delete field',
          life: 3000
        })
      }
    }
  })
}

const startTagEdit = (tag) => {
  editingTagId.value = tag.id
  editingTagName.value = tag.name
}

const cancelTagEdit = () => {
  editingTagId.value = null
  editingTagName.value = ''
}

const submitTagRename = async (tag, merge = false) => {
  const newName = editingTagName.value.trim()
  if (!newName) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Tag name cannot be empty', life: 3000 })
    return
  }
  if (newName === tag.name && !merge) {
    cancelTagEdit()
    return
  }

  try {
    await renameTag(tag.name, newName, merge)
    toast.add({
      severity: 'success',
      summary: 'Success',
      detail: merge ? `Tags merged into "${newName}"` : `Tag renamed to "${newName}"`,
      life: 3000
    })
    cancelTagEdit()
    await loadTags()
  } catch (error) {
    if (error.response?.status === 409) {
      // Conflict — tag already exists, offer to merge
      confirm.require({
        message: `A tag named "${newName}" already exists. Would you like to merge "${tag.name}" into "${newName}"? All destinations with either tag will end up with "${newName}".`,
        header: 'Merge Tags?',
        icon: 'pi pi-exclamation-triangle',
        acceptLabel: 'Merge',
        rejectLabel: 'Cancel',
        accept: () => submitTagRename(tag, true)
      })
    } else {
      toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to rename tag', life: 3000 })
    }
  }
}

const confirmDeleteTag = (tagName) => {
  confirm.require({
    message: `Are you sure you want to delete the tag "${tagName}"? It will be removed from all destinations.`,
    header: 'Confirm Delete',
    icon: 'pi pi-exclamation-triangle',
    accept: async () => {
      try {
        const response = await deleteTag(tagName)
        toast.add({
          severity: 'success',
          summary: 'Success',
          detail: `Tag "${tagName}" deleted from ${response.data.destinations_updated} destination(s)`,
          life: 3000
        })
        selectedTags.value = selectedTags.value.filter(t => t !== tagName)
        await loadTags()
      } catch (error) {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to delete tag', life: 3000 })
      }
    }
  })
}

const toggleTagSelection = (tagName) => {
  const idx = selectedTags.value.indexOf(tagName)
  if (idx >= 0) {
    selectedTags.value.splice(idx, 1)
  } else {
    selectedTags.value.push(tagName)
  }
}

const openMergeDialog = () => {
  mergeSourceTags.value = [...selectedTags.value]
  mergeTargetName.value = ''
  mergeDialogOpen.value = true
}

const submitBulkMerge = async () => {
  const target = mergeTargetName.value.trim()
  if (!target) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Enter a target tag name', life: 3000 })
    return
  }
  if (mergeSourceTags.value.length === 0) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'No tags selected', life: 3000 })
    return
  }
  try {
    const response = await bulkMergeTags(mergeSourceTags.value, target)
    toast.add({
      severity: 'success',
      summary: 'Success',
      detail: `Merged ${response.data.source_tags.length} tag(s) into "${target}" across ${response.data.destinations_updated} destination(s)`,
      life: 4000
    })
    mergeDialogOpen.value = false
    selectedTags.value = []
    await loadTags()
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: error.response?.data?.detail || 'Merge failed', life: 3000 })
  }
}

const confirmDeleteUnused = () => {
  const unused = allTags.value.filter(t => t.count === 0)
  if (unused.length === 0) {
    toast.add({ severity: 'info', summary: 'Info', detail: 'No unused tags to delete', life: 3000 })
    return
  }
  confirm.require({
    message: `Delete ${unused.length} tag(s) with 0 destinations?`,
    header: 'Delete Unused Tags',
    icon: 'pi pi-exclamation-triangle',
    accept: async () => {
      try {
        // Delete each unused tag individually
        let deleted = 0
        for (const tag of unused) {
          await deleteTag(tag.name)
          deleted++
        }
        toast.add({
          severity: 'success',
          summary: 'Success',
          detail: `Deleted ${deleted} unused tag(s)`,
          life: 3000
        })
        selectedTags.value = []
        await loadTags()
      } catch (error) {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to delete unused tags', life: 3000 })
      }
    }
  })
}

const onRestoreFileSelected = (event) => {
  selectedRestoreFile.value = event.files[0]
}

const handleBackup = () => {
  backupLoading.value = true
  backupProgress.value = { filesDone: 0, totalFiles: 0, currentFile: '' }

  const evtSource = new EventSource(`/api/admin/backup-stream?token=${encodeURIComponent(authStore.accessToken)}`)

  evtSource.onmessage = async (event) => {
    try {
      const data = JSON.parse(event.data)

      if (data.type === 'progress') {
        backupProgress.value = {
          filesDone: data.files_done,
          totalFiles: data.total_files,
          currentFile: data.current_file,
        }
      } else if (data.type === 'done') {
        evtSource.close()
        backupProgress.value = null

        try {
          const response = await apiBackupDownload(data.token)
          const url = window.URL.createObjectURL(response.data)
          const link = document.createElement('a')
          link.href = url
          link.download = `geographer-backup-${new Date().toISOString().split('T')[0]}.tgz`
          document.body.appendChild(link)
          link.click()
          document.body.removeChild(link)
          window.URL.revokeObjectURL(url)

          toast.add({
            severity: 'success',
            summary: 'Success',
            detail: `Backup complete — ${data.total_files} files`,
            life: 3000
          })
        } catch (dlError) {
          toast.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Archive built but download failed',
            life: 3000
          })
        }
        backupLoading.value = false
      } else if (data.type === 'error') {
        evtSource.close()
        backupProgress.value = null
        backupLoading.value = false
        toast.add({
          severity: 'error',
          summary: 'Error',
          detail: data.detail || 'Backup failed',
          life: 3000
        })
      }
    } catch (parseErr) {
      console.error('SSE parse error:', parseErr)
    }
  }

  evtSource.onerror = () => {
    evtSource.close()
    backupProgress.value = null
    backupLoading.value = false
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Lost connection during backup',
      life: 3000
    })
  }
}

const handleRestore = async () => {
  if (!selectedRestoreFile.value) return

  restoreLoading.value = true
  restoreProgress.value = { filesDone: 0, totalFiles: 0, currentFile: 'Uploading...' }

  try {
    // Step 1: Upload the file
    const uploadResponse = await apiRestoreUpload(selectedRestoreFile.value)
    const token = uploadResponse.data.token

    // Step 2: Connect to SSE for restore progress
    const evtSource = new EventSource(`/api/admin/restore-stream/${token}?auth_token=${encodeURIComponent(authStore.accessToken)}`)

    evtSource.onmessage = async (event) => {
      try {
        const data = JSON.parse(event.data)

        if (data.type === 'progress') {
          restoreProgress.value = {
            filesDone: data.files_done,
            totalFiles: data.total_files,
            currentFile: data.current_file,
          }
        } else if (data.type === 'done') {
          evtSource.close()
          restoreProgress.value = null
          restoreLoading.value = false
          selectedRestoreFile.value = null

          toast.add({
            severity: 'success',
            summary: 'Success',
            detail: data.message || 'Restore completed successfully',
            life: 5000
          })

          await destinationsStore.fetchDestinations()
        } else if (data.type === 'error') {
          evtSource.close()
          restoreProgress.value = null
          restoreLoading.value = false
          toast.add({
            severity: 'error',
            summary: 'Error',
            detail: data.detail || 'Restore failed',
            life: 5000
          })
        }
      } catch (parseErr) {
        console.error('SSE parse error:', parseErr)
      }
    }

    evtSource.onerror = () => {
      evtSource.close()
      restoreProgress.value = null
      restoreLoading.value = false
      toast.add({
        severity: 'error',
        summary: 'Error',
        detail: 'Lost connection during restore',
        life: 5000
      })
    }
  } catch (error) {
    restoreProgress.value = null
    restoreLoading.value = false
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Upload failed: ' + (error.response?.data?.detail || error.message),
      life: 5000
    })
  }
}

const openExportDialog = async () => {
  try {
    const response = await getExportFields()
    exportAvailableFields.value = response.data
    // Select all fields except description by default
    exportSelectedFields.value = response.data
      .filter(f => f.key !== 'description')
      .map(f => f.key)
    exportDialogVisible.value = true
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load export fields', life: 3000 })
  }
}

const selectAllExportFields = () => {
  exportSelectedFields.value = exportAvailableFields.value.map(f => f.key)
}

const deselectAllExportFields = () => {
  exportSelectedFields.value = []
}

const handleExportCsv = async () => {
  exportLoading.value = true
  try {
    const response = await exportCsv(exportSelectedFields.value)
    const url = window.URL.createObjectURL(response.data)
    const link = document.createElement('a')
    link.href = url
    link.download = `destinations-${new Date().toISOString().split('T')[0]}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    exportDialogVisible.value = false
    toast.add({ severity: 'success', summary: 'Success', detail: 'CSV exported', life: 3000 })
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'CSV export failed', life: 3000 })
  } finally {
    exportLoading.value = false
  }
}

// AI Settings functions
const loadAISettings = async () => {
  try {
    const response = await getAISettings()
    const data = response.data
    aiPromptTemplate.value = data.ai_prompt_template
    defaultPromptTemplate.value = data.ai_prompt_template
    geminiModel.value = data.gemini_model || 'gemini-2.5-flash'
    // Don't populate the key field — it's not returned for security
    if (data.gemini_api_key_set) {
      geminiApiKey.value = '••••••••••••••••'
    }
  } catch (error) {
    console.error('Failed to load AI settings:', error)
  }
}

const saveApiKey = async () => {
  if (!geminiApiKey.value || geminiApiKey.value === '••••••••••••••••') {
    toast.add({ severity: 'warn', summary: 'Warning', detail: 'Enter a new API key to save', life: 3000 })
    return
  }
  try {
    await updateAISettings({ gemini_api_key: geminiApiKey.value })
    toast.add({ severity: 'success', summary: 'Success', detail: 'API key saved', life: 3000 })
    geminiApiKey.value = '••••••••••••••••'
    connectionStatus.value = null
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to save API key', life: 3000 })
  }
}

const testConnection = async () => {
  testingConnection.value = true
  connectionStatus.value = null
  try {
    const response = await testAIConnection()
    connectionStatus.value = response.data
  } catch (error) {
    connectionStatus.value = { success: false, message: 'Request failed' }
  } finally {
    testingConnection.value = false
  }
}

const saveModel = async () => {
  try {
    await updateAISettings({ gemini_model: geminiModel.value })
    toast.add({ severity: 'success', summary: 'Success', detail: `Model switched to ${geminiModel.value}`, life: 3000 })
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to save model', life: 3000 })
  }
}

const savePromptTemplate = async () => {
  try {
    await updateAISettings({ ai_prompt_template: aiPromptTemplate.value })
    toast.add({ severity: 'success', summary: 'Success', detail: 'Prompt template saved', life: 3000 })
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to save prompt', life: 3000 })
  }
}

const resetPromptTemplate = async () => {
  try {
    // Send empty string to reset to default on backend
    await updateAISettings({ ai_prompt_template: '' })
    const response = await getAISettings()
    aiPromptTemplate.value = response.data.ai_prompt_template
    toast.add({ severity: 'success', summary: 'Success', detail: 'Prompt reset to default', life: 3000 })
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to reset prompt', life: 3000 })
  }
}

const copyBookmarklet = () => {
  navigator.clipboard.writeText(bookmarkletCode.value)
  toast.add({
    severity: 'success',
    summary: 'Success',
    detail: 'Bookmarklet code copied to clipboard',
    life: 3000
  })
}

onMounted(async () => {
  try {
    await Promise.all([
      customFieldsStore.fetchFields(),
      destinationsStore.fetchDestinations(),
      loadAISettings(),
      loadTags()
    ])
  } catch (error) {
    console.error('Error loading settings:', error)
  }
})
</script>

<style scoped>
.settings-page {
  min-height: 100vh;
  background: var(--color-bg);
  padding-bottom: 4rem;
}

.page-title {
  margin: 0 0 2rem 0;
  font-size: 2.25rem;
  color: var(--color-text-bright);
}

.settings-page :deep(.p-tabs) {
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  overflow: hidden;
}

.settings-page :deep(.p-tablist) {
  background: var(--color-bg-light);
  border-bottom: 1px solid var(--color-border);
}

.tab-content {
  padding: 2rem;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
}

.section-header h2 {
  margin: 0;
}

h2 {
  font-size: 1.25rem;
  margin-bottom: 1.5rem;
  color: var(--color-text-bright);
}

h3 {
  font-size: 1rem;
  margin-bottom: 0.75rem;
  color: var(--color-text-bright);
}

h4 {
  margin: 0;
  color: var(--color-text-bright);
}

p {
  color: var(--color-text-muted);
  line-height: 1.6;
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

.fields-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.field-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  background: var(--color-bg-light);
  border: 1px solid var(--color-border);
  border-radius: 0.375rem;
  transition: all 0.2s;
}

.field-item:hover {
  background: var(--color-bg-hover);
}

.field-info {
  flex: 1;
}

.field-info h4 {
  margin-bottom: 0.25rem;
}

.field-info p {
  margin: 0;
  font-size: 0.875rem;
}

.field-actions {
  display: flex;
  gap: 0.5rem;
}

.tags-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.tag-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem;
  background: var(--color-bg-light);
  border: 1px solid var(--color-border);
  border-radius: 0.375rem;
}

.tag-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex: 1;
}

.tag-name {
  font-weight: 600;
  color: var(--color-text-bright);
}

.tag-count {
  font-size: 0.875rem;
  color: var(--color-text-muted);
}

.tag-edit-row {
  flex: 1;
  display: flex;
  align-items: center;
}

.tag-edit-input {
  width: 100%;
  font-size: 0.875rem;
}

.tag-checkbox {
  flex-shrink: 0;
  margin-right: 0.5rem;
}

.tag-link {
  color: var(--color-accent-hover);
  text-decoration: none;
  cursor: pointer;
}

.tag-link:hover {
  text-decoration: underline;
}

.tag-actions {
  display: flex;
  gap: 0.25rem;
  flex-shrink: 0;
}

.tag-total {
  font-size: 0.875rem;
  color: var(--color-text-muted);
  font-weight: 400;
}

.tags-tab-content {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.tags-fixed-header {
  flex-shrink: 0;
}

.tags-scroll-area {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  max-height: calc(100vh - 320px);
}

.tags-toolbar {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1rem;
  align-items: center;
  flex-wrap: wrap;
}

.tags-search {
  color: var(--color-text-muted);
  font-size: 1rem;
  display: flex;
  align-items: center;
}

.tags-search-input {
  flex: 0 1 400px;
  min-width: 150px;
  font-size: 0.875rem;
}

.tags-sort-dropdown {
  min-width: 190px;
  font-size: 0.875rem;
}

.merge-dialog {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.merge-source-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.merge-tag-chip {
  display: inline-block;
  padding: 0.25rem 0.6rem;
  background: var(--color-bg-light);
  border: 1px solid var(--color-border);
  border-radius: 1rem;
  font-size: 0.8rem;
  color: var(--color-text-bright);
}

.toggle-settings {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.toggle-row {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
}

.toggle-label label {
  font-weight: 500;
  color: var(--color-text-bright);
  cursor: pointer;
}

.toggle-label .field-hint {
  margin-top: 0.25rem;
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

.field-hint {
  margin-top: 0.5rem;
  font-size: 0.8rem;
  color: var(--color-text-muted);
}


.import-upload {
  margin-top: 0.5rem;
}

.restore-btn {
  margin-top: 0.75rem;
  width: 100%;
}

.backup-progress {
  margin-top: 1rem;
}

.progress-bar-track {
  width: 100%;
  height: 8px;
  background: var(--color-bg-light);
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid var(--color-border);
}

.progress-bar-fill {
  height: 100%;
  background: #3b82f6;
  border-radius: 4px;
  transition: width 0.2s ease;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-top: 0.4rem;
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

.progress-file {
  margin-top: 0.2rem;
  font-size: 0.75rem;
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-info {
  margin-top: 1rem;
  padding: 0.75rem;
  background: var(--color-bg-hover);
  border-left: 3px solid var(--color-accent-hover);
  color: var(--color-accent-hover);
  border-radius: 0.375rem;
  font-size: 0.875rem;
}

.file-info p {
  margin: 0;
}

.bookmarklet-container {
  background: var(--color-bg-light);
  border: 1px solid var(--color-border);
  border-radius: 0.375rem;
  padding: 1.5rem;
  margin-top: 1.5rem;
}

.bookmarklet-button-container {
  margin: 1.5rem 0;
  padding: 1.5rem;
  background: var(--color-bg-elevated);
  border: 2px dashed var(--color-border);
  border-radius: 0.375rem;
  text-align: center;
}

.bookmarklet-btn {
  display: inline-block;
  padding: 0.75rem 1.5rem;
  background: var(--color-accent);
  color: white;
  text-decoration: none;
  border-radius: 0.375rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.bookmarklet-btn:hover {
  background: var(--color-accent-hover);
}

.code-details {
  margin-top: 1.5rem;
  cursor: pointer;
}

.code-details summary {
  padding: 0.75rem;
  background: var(--color-bg-light);
  border-radius: 0.375rem;
  font-weight: 600;
  color: var(--color-text-bright);
}

.code-details summary:hover {
  background: var(--color-bg-hover);
}

.code-block {
  background: #1f2937;
  color: #d1d5db;
  padding: 1rem;
  border-radius: 0.375rem;
  overflow-x: auto;
  font-size: 0.75rem;
  margin: 1rem 0;
  font-family: 'Monaco', 'Courier New', monospace;
}

.form {
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
  color: var(--color-text-bright);
}

.field :deep(.p-inputtext),
.field :deep(.p-inputtextarea),
.field :deep(.p-dropdown) {
  width: 100%;
  font-size: 0.875rem;
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
  padding: 2rem;
  color: var(--color-text-muted);
  background: var(--color-bg-light);
  border: 1px dashed var(--color-border);
  border-radius: 0.375rem;
  margin: 1rem 0;
}

.w-full {
  width: 100%;
}

.py-4 {
  padding-top: 1.5rem;
  padding-bottom: 1.5rem;
}

ol {
  margin: 1rem 0 1rem 1.5rem;
  color: var(--color-text);
}

li {
  margin: 0.5rem 0;
  line-height: 1.6;
}

/* AI Tab */
.ai-model-row {
  margin-bottom: 0.5rem;
}

.ai-model-dropdown {
  min-width: 220px;
}

.ai-link {
  color: var(--color-accent);
  text-decoration: none;
}

.ai-link:hover {
  text-decoration: underline;
}

.ai-readonly-notice {
  background: var(--color-bg-hover);
  border: 1px solid var(--color-accent);
  border-radius: 0.375rem;
  padding: 0.75rem 1rem;
  color: var(--color-accent-hover);
  font-size: 0.875rem;
  margin-bottom: 1rem;
}

.ai-key-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.ai-key-input {
  flex: 1;
  font-size: 0.875rem;
}

.ai-key-actions {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  margin-top: 0.25rem;
}

.status-ok {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
  border: 1px solid rgba(34, 197, 94, 0.25);
}

.status-error {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.25);
}

.placeholder-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.placeholder-list code {
  background: var(--color-bg-light);
  border: 1px solid var(--color-border);
  padding: 0.2rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.8rem;
  color: var(--color-accent);
}

.ai-prompt-textarea {
  font-family: 'Monaco', 'Courier New', monospace;
  font-size: 0.8rem;
  line-height: 1.5;
}

.ai-prompt-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.75rem;
}

/* Export Dialog */
.export-dialog {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.export-now-btn {
  width: 100%;
}

.export-toggle-links {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  font-size: 0.85rem;
}

.export-toggle-links a {
  color: var(--color-accent);
  text-decoration: none;
  cursor: pointer;
}

.export-toggle-links a:hover {
  text-decoration: underline;
}

.export-toggle-links span {
  color: var(--color-text-muted);
}

.export-fields-list {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  max-height: 400px;
  overflow-y: auto;
}

.export-field-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.export-field-item label {
  cursor: pointer;
  font-size: 0.875rem;
  color: var(--color-text-bright);
}

@media (max-width: 768px) {
  .container {
    padding-left: 0.5rem;
    padding-right: 0.5rem;
  }

  .tab-content {
    padding: 0.3rem;
  }

  .section-header {
    flex-direction: column;
    align-items: stretch;
    gap: 1rem;
  }

  .section-header button {
    width: 100%;
  }

  .tags-toolbar {
    flex-wrap: wrap;
  }

  .tags-search-input {
    flex: 1 1 100%;
    min-width: unset;
  }

  .tags-sort-dropdown {
    flex: 1;
    min-width: unset;
  }
}
</style>

