<template>
  <div class="editor-container">
    <div class="editor-toolbar">
      <Button
        label="B"
        text
        @click="toggleBold"
        :class="{ 'active': editor?.isActive('bold') }"
        title="Bold (Ctrl+B)"
        class="toolbar-btn bold-btn"
      />
      <Button
        label="I"
        text
        @click="toggleItalic"
        :class="{ 'active': editor?.isActive('italic') }"
        title="Italic (Ctrl+I)"
        class="toolbar-btn italic-btn"
      />
      <Button
        label="S"
        text
        @click="toggleStrike"
        title="Strikethrough"
        class="toolbar-btn strike-btn"
      />

      <div class="toolbar-divider"></div>

      <Button
        label="H1"
        text
        @click="toggleHeading(1)"
        :class="{ 'active': editor?.isActive('heading', { level: 1 }) }"
        title="Heading 1"
        class="toolbar-btn"
      />
      <Button
        label="H2"
        text
        @click="toggleHeading(2)"
        :class="{ 'active': editor?.isActive('heading', { level: 2 }) }"
        title="Heading 2"
        class="toolbar-btn"
      />
      <Button
        label="H3"
        text
        @click="toggleHeading(3)"
        :class="{ 'active': editor?.isActive('heading', { level: 3 }) }"
        title="Heading 3"
        class="toolbar-btn"
      />

      <div class="toolbar-divider"></div>

      <Button
        icon="pi pi-list"
        text
        @click="toggleBulletList"
        :class="{ 'active': editor?.isActive('bulletList') }"
        title="Bullet List"
        class="toolbar-btn"
      />
      <Button
        icon="pi pi-sort-numeric-up"
        text
        @click="toggleOrderedList"
        :class="{ 'active': editor?.isActive('orderedList') }"
        title="Ordered List"
        class="toolbar-btn"
      />
      <Button
        label="❝"
        text
        @click="toggleBlockquote"
        :class="{ 'active': editor?.isActive('blockquote') }"
        title="Blockquote"
        class="toolbar-btn quote-btn"
      />

      <div class="toolbar-divider"></div>

      <Button
        icon="pi pi-link"
        text
        @click="addLink"
        title="Add Link"
        class="toolbar-btn"
      />
      <Button
        icon="pi pi-image"
        text
        @click="addImage"
        title="Add Image"
        class="toolbar-btn"
      />

      <div class="toolbar-divider"></div>

      <Button
        icon="pi pi-arrow-left"
        text
        @click="undo"
        title="Undo"
        class="toolbar-btn"
      />
      <Button
        icon="pi pi-arrow-right"
        text
        @click="redo"
        title="Redo"
        class="toolbar-btn"
      />
    </div>

    <EditorContent :editor="editor" class="editor-content" />
  </div>
</template>

<script setup>
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Image from '@tiptap/extension-image'
import Link from '@tiptap/extension-link'
import Placeholder from '@tiptap/extension-placeholder'
import { watch, onBeforeUnmount } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: 'Start typing...'
  }
})

const emit = defineEmits(['update:modelValue'])

const editor = useEditor({
  content: props.modelValue,
  extensions: [
    StarterKit,
    Image.configure({
      allowBase64: true
    }),
    Link.configure({
      openOnClick: false
    }),
    Placeholder.configure({
      placeholder: props.placeholder
    })
  ],
  onUpdate: ({ editor }) => {
    emit('update:modelValue', editor.getHTML())
  }
})

watch(
  () => props.modelValue,
  (newVal) => {
    if (editor.value && editor.value.getHTML() !== newVal) {
      editor.value.commands.setContent(newVal, false)
    }
  }
)

const toggleBold = () => editor.value?.chain().focus().toggleBold().run()
const toggleItalic = () => editor.value?.chain().focus().toggleItalic().run()
const toggleStrike = () => editor.value?.chain().focus().toggleStrike().run()
const toggleHeading = (level) => editor.value?.chain().focus().toggleHeading({ level }).run()
const toggleBulletList = () => editor.value?.chain().focus().toggleBulletList().run()
const toggleOrderedList = () => editor.value?.chain().focus().toggleOrderedList().run()
const toggleBlockquote = () => editor.value?.chain().focus().toggleBlockquote().run()

const addLink = () => {
  const url = prompt('Enter URL:')
  if (url) {
    editor.value?.chain().focus().extendMarkRange('link').setLink({ href: url }).run()
  }
}

const addImage = () => {
  const url = prompt('Enter image URL:')
  if (url) {
    editor.value?.chain().focus().setImage({ src: url }).run()
  }
}

const undo = () => editor.value?.chain().focus().undo().run()
const redo = () => editor.value?.chain().focus().redo().run()

onBeforeUnmount(() => {
  editor.value?.destroy()
})
</script>

<style scoped>
.editor-container {
  border: 1px solid var(--color-border);
  border-radius: 0.375rem;
  background: var(--color-bg-light);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.editor-container:focus-within {
  border-color: var(--color-border);
}

.editor-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  padding: 0.75rem;
  border-bottom: 1px solid var(--color-border);
  background-color: var(--color-bg-hover);
  align-items: center;
}

.toolbar-btn {
  width: 2.25rem;
  height: 2.25rem;
  padding: 0;
  font-size: 0.875rem;
}

.toolbar-btn.bold-btn :deep(.p-button-label) {
  font-weight: 800;
}

.toolbar-btn.italic-btn :deep(.p-button-label) {
  font-style: italic;
  font-family: Georgia, serif;
}

.toolbar-btn.strike-btn :deep(.p-button-label) {
  text-decoration: line-through;
}

.toolbar-btn.quote-btn :deep(.p-button-label) {
  font-size: 1.1rem;
  line-height: 1;
}

.toolbar-btn.active {
  background-color: var(--color-bg-light);
  color: var(--color-accent-hover);
}

.toolbar-divider {
  width: 1px;
  height: 1.75rem;
  background-color: var(--color-border);
  margin: 0 0.25rem;
}

.editor-content {
  min-height: 200px;
  overflow-y: auto;
  max-height: 500px;
}

.editor-content :deep(.tiptap) {
  min-height: 200px;
  padding: 0.75rem 1rem;
  outline: none;
}

.editor-content :deep(.tiptap.ProseMirror-focused) {
  outline: none;
}

.editor-content :deep(h1) {
  font-size: 1.875rem;
  font-weight: 700;
  margin: 1rem 0 0.5rem 0;
}

.editor-content :deep(h2) {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0.875rem 0 0.5rem 0;
}

.editor-content :deep(h3) {
  font-size: 1.25rem;
  font-weight: 700;
  margin: 0.75rem 0 0.5rem 0;
}

.editor-content :deep(p) {
  margin: 0.5rem 0;
}

.editor-content :deep(ul),
.editor-content :deep(ol) {
  margin: 0.75rem 0 0.75rem 1.5rem;
}

.editor-content :deep(li) {
  margin: 0.25rem 0;
}

.editor-content :deep(blockquote) {
  border-left: 4px solid var(--color-accent-hover);
  padding-left: 1rem;
  margin: 0.75rem 0;
  color: var(--color-text-muted);
  font-style: italic;
}

.editor-content :deep(code) {
  background: var(--color-bg-hover);
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-family: 'Monaco', 'Courier New', monospace;
  font-size: 0.875em;
}

.editor-content :deep(pre) {
  background: var(--color-bg-hover);
  padding: 1rem;
  border-radius: 0.375rem;
  overflow-x: auto;
  margin: 0.75rem 0;
}

.editor-content :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 0.375rem;
  margin: 0.5rem 0;
}

.editor-content :deep(a) {
  color: var(--color-accent-hover);
  text-decoration: underline;
}

.editor-content :deep(p.is-editor-empty:first-child::before) {
  color: var(--color-text-muted);
  content: attr(data-placeholder);
  float: left;
  height: 0;
  pointer-events: none;
}
</style>
