<template>
  <div class="gallery-container">
    <div class="gallery-grid">
      <div
        v-for="item in media"
        :key="item.id"
        class="gallery-item"
        :class="{ 'is-cover': item.id === coverMediaId }"
        @click="selectMedia(item)"
      >
        <div v-if="isImage(item.file_type)" class="image-wrapper">
          <img :src="item.thumbnail_url" :alt="item.file_name" @error="e => e.target.src = item.url" />
          <!-- Cover badge -->
          <div v-if="item.id === coverMediaId" class="cover-badge">
            <i class="pi pi-star-fill"></i> Cover
          </div>
          <div v-if="editable" class="action-overlay">
            <button
              v-if="item.id !== coverMediaId"
              class="cover-btn"
              @click.stop="setCover(item.id)"
              title="Set as cover image"
            >
              <i class="pi pi-star"></i>
            </button>
            <button
              class="delete-btn"
              @click.stop="deleteMedia(item.id)"
              title="Delete"
            >
              <i class="pi pi-trash"></i>
            </button>
          </div>
        </div>
        <div v-else class="file-wrapper">
          <div class="file-icon">
            <i :class="getFileIcon(item.file_type)"></i>
          </div>
          <div class="file-name">{{ item.file_name }}</div>
          <button
            v-if="editable"
            class="delete-btn"
            @click.stop="deleteMedia(item.id)"
            title="Delete"
          >
            <i class="pi pi-trash"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- Lightbox Dialog -->
    <Dialog
      v-model:visible="lightboxOpen"
      modal
      :header="selectedItem?.file_name"
      :style="{ width: '90vw', maxWidth: '900px' }"
    >
      <div v-if="selectedItem" class="lightbox-content">
        <img
          v-if="isImage(selectedItem.file_type)"
          :src="selectedItem.url"
          :alt="selectedItem.file_name"
          class="lightbox-image"
        />
        <div v-else class="file-preview">
          <i :class="getFileIcon(selectedItem.file_type)"></i>
          <p>{{ selectedItem.file_name }}</p>
          <a :href="selectedItem.url" target="_blank" class="download-link">
            Download File
          </a>
        </div>
      </div>
    </Dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  media: {
    type: Array,
    default: () => []
  },
  editable: {
    type: Boolean,
    default: false
  },
  coverMediaId: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['delete', 'setCover'])

const lightboxOpen = ref(false)
const selectedItem = ref(null)

const isImage = (fileType) => {
  return fileType.startsWith('image/')
}

const getFileIcon = (fileType) => {
  if (fileType.startsWith('image/')) return 'pi pi-image'
  if (fileType.includes('pdf')) return 'pi pi-file-pdf'
  if (fileType.includes('video')) return 'pi pi-video'
  if (fileType.includes('word') || fileType.includes('document')) return 'pi pi-file-word'
  return 'pi pi-file'
}

const selectMedia = (item) => {
  if (isImage(item.file_type)) {
    selectedItem.value = item
    lightboxOpen.value = true
  }
}

const deleteMedia = (id) => {
  emit('delete', id)
}

const setCover = (id) => {
  emit('setCover', id)
}
</script>

<style scoped>
.gallery-container {
  width: 100%;
}

.gallery-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 1rem;
}

.gallery-item {
  position: relative;
  aspect-ratio: 1;
  overflow: hidden;
  border-radius: 0.5rem;
  background: var(--color-bg-hover);
  cursor: pointer;
  border: 2px solid var(--color-border);
  transition: all 0.2s;
}

.gallery-item.is-cover {
  border-color: #f59e0b;
  box-shadow: 0 0 0 1px #f59e0b;
}

.gallery-item:hover {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.4);
  border-color: var(--color-border);
}

.gallery-item.is-cover:hover {
  border-color: #f59e0b;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.4), 0 0 0 1px #f59e0b;
}

.image-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
}

.image-wrapper img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.2s;
}

.gallery-item:hover .image-wrapper img {
  transform: scale(1.05);
}

.cover-badge {
  position: absolute;
  top: 0.5rem;
  left: 0.5rem;
  background: rgba(245, 158, 11, 0.95);
  color: white;
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.2rem 0.5rem;
  border-radius: 0.25rem;
  display: flex;
  align-items: center;
  gap: 0.25rem;
  z-index: 2;
}

.cover-badge i {
  font-size: 0.65rem;
}

.action-overlay {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  opacity: 0;
  transition: opacity 0.2s;
  z-index: 2;
}

.gallery-item:hover .action-overlay {
  opacity: 1;
}

.cover-btn {
  background: rgba(245, 158, 11, 0.9);
  color: white;
  border: none;
  border-radius: 0.25rem;
  padding: 0.5rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.875rem;
}

.cover-btn:hover {
  background: rgba(217, 119, 6, 1);
}

.delete-btn {
  background: rgba(239, 68, 68, 0.9);
  color: white;
  border: none;
  border-radius: 0.25rem;
  padding: 0.5rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.875rem;
}

.file-wrapper .delete-btn {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  opacity: 0;
  transition: opacity 0.2s;
}

.gallery-item:hover .file-wrapper .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  background: rgba(220, 38, 38, 1);
}

.file-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  text-align: center;
  position: relative;
}

.file-icon {
  font-size: 2rem;
  color: var(--color-text-muted);
  margin-bottom: 0.5rem;
}

.file-name {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  word-break: break-word;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.lightbox-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.lightbox-image {
  max-width: 100%;
  max-height: 70vh;
  object-fit: contain;
}

.file-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 2rem;
}

.file-preview i {
  font-size: 3rem;
  color: var(--color-text-muted);
}

.file-preview p {
  margin: 0;
  word-break: break-all;
  color: var(--color-text-muted);
}

.download-link {
  color: var(--color-accent-hover);
  text-decoration: none;
  font-weight: 500;
}

.download-link:hover {
  text-decoration: underline;
}

@media (max-width: 768px) {
  .gallery-grid {
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 0.75rem;
  }
}
</style>
