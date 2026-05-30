import { ref } from 'vue'
import { useApi } from './useApi'

let debounceTimer = null

export const useGeocoding = () => {
  const { geocode } = useApi()
  const results = ref([])
  const loading = ref(false)

  const searchLocation = (query) => {
    return new Promise((resolve, reject) => {
      clearTimeout(debounceTimer)

      if (!query || query.trim().length === 0) {
        results.value = []
        resolve([])
        return
      }

      loading.value = true
      debounceTimer = setTimeout(async () => {
        try {
          const response = await geocode(query)
          const data = Array.isArray(response.data) ? response.data : []
          results.value = data
          resolve(data)
        } catch (error) {
          console.error('Geocoding error:', error)
          results.value = []
          reject(error)
        } finally {
          loading.value = false
        }
      }, 300)
    })
  }

  const resolveLocation = async (query) => {
    try {
      const response = await geocode(query)
      const data = response.data || []
      if (data.length > 0) {
        const first = data[0]
        return {
          lat: first.lat,
          lon: first.lon,
          display_name: first.display_name
        }
      }
      return null
    } catch (error) {
      console.error('Geocoding error:', error)
      return null
    }
  }

  return {
    results,
    loading,
    searchLocation,
    resolveLocation
  }
}
