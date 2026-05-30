<template>
  <div class="uploader-container">
    <FileUpload
      ref="fileUpload"
      name="files"
      :url="`/api/destinations/${destinationId}/media`"
      @upload="onUpload"
      @select="onSelect"
      :multiple="true"
      accept="image/*,application/pdf,video/*,.doc,.docx,.xls,.xlsx"
      :show-upload-button="true"
      :show-cancel-button="true"
      :max-file-size="50000000"
      choose-label="Choose Files"
      upload-label="Upload"
      cancel-label="Cancel"
      :auto="false"
      class="upload-control"
    >
      <template #content>
        <ul v-if="files.length">
          <li v-for="(file, index) in files" :key="index" class="file-item">
            <div class="file-info">
              <span>{{ file.name }}</span>
              <span class="file-size">({{ formatFileSize(file.size) }})</span>
            </div>
          </li>
        </ul>
      </template>
    </FileUpload>

    <div v-if="uploading" class="upload-progress">
      <ProgressBar :value="uploadProgress" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useToast } from 'primevue/usetoast'

const props = defineProps({
  destinationId: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['uploaded'])

const toast = useToast()
const fileUpload = ref(null)
const files = ref([])
const uploading = ref(false)
const uploadProgress = ref(0)

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

const onSelect = (event) => {
  files.value = event.files
}

const onUpload = (event) => {
  uploading.value = true
  uploadProgress.value = 0

  setTimeout(() => {
    uploading.value = false
    uploadProgress.value = 100
    files.value = []

    toast.add({
      severity: 'success',
      summary: 'Success',
      detail: 'Files uploaded successfully',
      life: 3000
    })

    emit('uploaded')
  }, 1000)
}
</script>

<style scoped>
.uploader-container {
  width: 100%;
  padding: 1rem;
  background: var(--color-bg-light);
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
}

.upload-control {
  width: 100%;
}

.upload-control :deep(.p-fileupload-content) {
  padding: 1rem;
}

.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem;
  background: var(--color-bg-hover);
  border: 1px solid var(--color-border);
  border-radius: 0.375rem;
  margin-bottom: 0.5rem;
  list-style: none;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex: 1;
}

.file-size {
  font-size: 0.875rem;
  color: var(--color-text-muted);
}

.upload-progress {
  margin-top: 1rem;
}
</style>
