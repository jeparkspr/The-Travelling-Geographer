import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useApi } from '@/composables/useApi'

export const useDestinationsStore = defineStore('destinations', () => {
  const { getDestinations, getDestination, createDestination, updateDestination, deleteDestination, getTags } = useApi()

  const destinations = ref([])
  const currentDestination = ref(null)
  const loading = ref(false)
  const tags = ref([])
  const filters = ref({
    ownership: 'all',
    status: [],
    country: [],
    region: [],
    tags: [],
    priority: [],
    best_season: [],
    rating: [],
    search: '',
    noCover: false
  })

  // Computed
  const destinationsByStatus = computed(() => {
    return destinations.value.reduce((acc, dest) => {
      if (!acc[dest.status]) {
        acc[dest.status] = []
      }
      acc[dest.status].push(dest)
      return acc
    }, {})
  })

  const destinationCountByStatus = computed(() => {
    const counts = {
      suggested: 0,
      researching: 0,
      want_to_visit: 0,
      planned: 0,
      visited: 0,
      archived: 0
    }
    destinations.value.forEach(dest => {
      if (counts[dest.status] !== undefined) {
        counts[dest.status]++
      }
    })
    return counts
  })

  // Actions
  const fetchDestinations = async (filterParams = {}) => {
    loading.value = true
    try {
      const response = await getDestinations(filterParams)
      destinations.value = response.data || []
      return destinations.value
    } catch (error) {
      console.error('Error fetching destinations:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const fetchDestination = async (id) => {
    loading.value = true
    try {
      const response = await getDestination(id)
      currentDestination.value = response.data
      return currentDestination.value
    } catch (error) {
      console.error('Error fetching destination:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const createNewDestination = async (data) => {
    try {
      const response = await createDestination(data)
      destinations.value.push(response.data)
      return response.data
    } catch (error) {
      console.error('Error creating destination:', error)
      throw error
    }
  }

  const updateCurrentDestination = async (id, data) => {
    try {
      const response = await updateDestination(id, data)
      const index = destinations.value.findIndex(d => d.id === id)
      if (index > -1) {
        destinations.value[index] = response.data
      }
      currentDestination.value = response.data
      return response.data
    } catch (error) {
      console.error('Error updating destination:', error)
      throw error
    }
  }

  const deleteCurrentDestination = async (id) => {
    try {
      await deleteDestination(id)
      destinations.value = destinations.value.filter(d => d.id !== id)
      if (currentDestination.value?.id === id) {
        currentDestination.value = null
      }
    } catch (error) {
      console.error('Error deleting destination:', error)
      throw error
    }
  }

  const fetchTags = async () => {
    try {
      const response = await getTags()
      const data = response.data || {}
      // Backend returns {tagName: count} dict — convert to array of strings
      if (Array.isArray(data)) {
        tags.value = data
      } else {
        tags.value = Object.keys(data)
      }
      return tags.value
    } catch (error) {
      console.error('Error fetching tags:', error)
      throw error
    }
  }

  const setFilters = (newFilters) => {
    filters.value = { ...filters.value, ...newFilters }
  }

  const clearFilters = () => {
    filters.value = {
      ownership: 'all',
      status: [],
      country: [],
      region: [],
      tags: [],
      priority: [],
      best_season: [],
      rating: [],
      search: '',
      noCover: false
    }
  }

  return {
    destinations,
    currentDestination,
    loading,
    tags,
    filters,
    destinationsByStatus,
    destinationCountByStatus,
    fetchDestinations,
    fetchDestination,
    createNewDestination,
    updateCurrentDestination,
    deleteCurrentDestination,
    fetchTags,
    setFilters,
    clearFilters
  }
})
