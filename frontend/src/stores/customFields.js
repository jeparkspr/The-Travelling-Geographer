import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useApi } from '@/composables/useApi'

export const useCustomFieldsStore = defineStore('customFields', () => {
  const { getCustomFields, createCustomField, updateCustomField, deleteCustomField } = useApi()

  const fields = ref([])
  const loading = ref(false)

  const fetchFields = async () => {
    loading.value = true
    try {
      const response = await getCustomFields()
      fields.value = response.data || []
      return fields.value
    } catch (error) {
      console.error('Error fetching custom fields:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const createField = async (data) => {
    try {
      const response = await createCustomField(data)
      fields.value.push(response.data)
      return response.data
    } catch (error) {
      console.error('Error creating custom field:', error)
      throw error
    }
  }

  const updateField = async (id, data) => {
    try {
      const response = await updateCustomField(id, data)
      const index = fields.value.findIndex(f => f.id === id)
      if (index > -1) {
        fields.value[index] = response.data
      }
      return response.data
    } catch (error) {
      console.error('Error updating custom field:', error)
      throw error
    }
  }

  const deleteField = async (id) => {
    try {
      await deleteCustomField(id)
      fields.value = fields.value.filter(f => f.id !== id)
    } catch (error) {
      console.error('Error deleting custom field:', error)
      throw error
    }
  }

  return {
    fields,
    loading,
    fetchFields,
    createField,
    updateField,
    deleteField
  }
})
