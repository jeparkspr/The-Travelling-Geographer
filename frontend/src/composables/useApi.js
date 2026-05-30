import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json'
  }
})

// Attach Bearer token to every request
api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 → attempt token refresh once, then retry
let isRefreshing = false
let refreshSubscribers = []

function onRefreshed(newToken) {
  refreshSubscribers.forEach(cb => cb(newToken))
  refreshSubscribers = []
}

api.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      const refreshToken = localStorage.getItem('refresh_token')
      if (!refreshToken) {
        return Promise.reject(error)
      }

      if (isRefreshing) {
        // Queue this request until the refresh completes
        return new Promise(resolve => {
          refreshSubscribers.push(token => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            resolve(api(originalRequest))
          })
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const { data } = await axios.post('/api/auth/refresh', { refresh_token: refreshToken })
        localStorage.setItem('access_token', data.access_token)
        localStorage.setItem('refresh_token', data.refresh_token)
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`
        onRefreshed(data.access_token)
        return api(originalRequest)
      } catch {
        // Refresh failed — clear auth state, redirect to login
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
        window.location.href = '/login'
        return Promise.reject(error)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

export const useApi = () => {
  // Destinations
  const getDestinations = (params = {}) => {
    return api.get('/destinations', { params })
  }

  const getDestination = (id) => {
    return api.get(`/destinations/${id}`)
  }

  const createDestination = (data) => {
    return api.post('/destinations', data)
  }

  const updateDestination = (id, data) => {
    return api.put(`/destinations/${id}`, data)
  }

  const deleteDestination = (id) => {
    return api.delete(`/destinations/${id}`)
  }

  // Clip
  const clipDestination = (data) => {
    return api.post('/destinations/clip', data)
  }

  // Media
  const uploadMedia = (destinationId, files) => {
    const formData = new FormData()
    files.forEach(file => {
      formData.append('files', file)
    })
    return api.post(`/destinations/${destinationId}/media`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  }

  const getMedia = (destinationId) => {
    return api.get(`/destinations/${destinationId}/media`)
  }

  const deleteMedia = (id) => {
    return api.delete(`/destinations/media/${id}`)
  }

  const uploadMediaFromUrl = (destinationId, url, setAsCover = true) => {
    return api.post(`/destinations/${destinationId}/media/from-url`, {
      url,
      set_as_cover: setAsCover
    })
  }

  const setCoverImage = (destinationId, mediaId) => {
    return api.put(`/destinations/${destinationId}/cover/${mediaId}`)
  }

  // Journal
  const getAllJournalEntries = (statuses = 'planned,visited,archived') => {
    return api.get('/journal/all', { params: { statuses } })
  }

  const getJournalEntries = (destinationId) => {
    return api.get(`/destinations/${destinationId}/journal`)
  }

  const createJournalEntry = (destinationId, data) => {
    // Backend expects Form data (multipart), not JSON
    const formData = new FormData()
    formData.append('title', data.title)
    if (data.body) formData.append('body', data.body)
    if (data.entry_date) formData.append('entry_date', data.entry_date)
    if (data.rating != null) formData.append('rating', data.rating)
    return api.post(`/destinations/${destinationId}/journal`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  }

  const updateJournalEntry = (destinationId, entryId, data) => {
    return api.put(`/destinations/${destinationId}/journal/${entryId}`, data)
  }

  const deleteJournalEntry = (destinationId, entryId) => {
    return api.delete(`/destinations/${destinationId}/journal/${entryId}`)
  }

  // Geocoding
  const geocode = (query) => {
    return api.get('/geocode', { params: { q: query } })
  }

  const reverseGeocode = (lat, lng) => {
    return api.get('/geocode/reverse', { params: { lat, lon: lng } })
  }

  // Tags
  const getTags = () => {
    return api.get('/admin/tags')
  }

  const renameTag = (oldName, newName, merge = false) => {
    return api.put('/admin/tags/rename', { old_name: oldName, new_name: newName, merge })
  }

  const deleteTag = (tagName) => {
    return api.delete(`/admin/tags/${encodeURIComponent(tagName)}`)
  }

  const deleteUnusedTags = () => {
    return api.post('/admin/tags/delete-unused')
  }

  const bulkMergeTags = (sourceTags, targetTag) => {
    return api.post('/admin/tags/bulk-merge', { source_tags: sourceTags, target_tag: targetTag })
  }

  // Filter options (unique countries/regions)
  const getFilterOptions = () => {
    return api.get('/admin/filter-options')
  }

  // Custom Fields
  const getCustomFields = () => {
    return api.get('/custom-fields')
  }

  const createCustomField = (data) => {
    return api.post('/custom-fields', data)
  }

  const updateCustomField = (id, data) => {
    return api.put(`/custom-fields/${id}`, data)
  }

  const deleteCustomField = (id) => {
    return api.delete(`/custom-fields/${id}`)
  }

  // Search
  const searchAll = (query) => {
    return api.get('/search', { params: { query } })
  }

  // Links
  const fetchLinkImage = (destinationId, linkId) => {
    return api.post(`/destinations/${destinationId}/links/${linkId}/fetch-image`)
  }

  const addLink = (destinationId, data) => {
    return api.post(`/destinations/${destinationId}/links`, data)
  }

  const updateLink = (destinationId, linkId, data) => {
    return api.put(`/destinations/${destinationId}/links/${linkId}`, data)
  }

  const deleteLink = (destinationId, linkId) => {
    return api.delete(`/destinations/${destinationId}/links/${linkId}`)
  }

  // Export
  const getExportFields = () => {
    return api.get('/admin/export-fields')
  }

  const exportCsv = (fields) => {
    const params = {}
    if (fields && fields.length) {
      params.fields = fields.join(',')
    }
    return api.get('/admin/export-csv', { params, responseType: 'blob' })
  }

  // Unified backup/restore
  const backupDownload = (token) => {
    const authToken = localStorage.getItem('access_token')
    return api.get(`/admin/backup-download/${token}`, {
      responseType: 'blob',
      params: { auth_token: authToken },
    })
  }

  const restoreUpload = (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/admin/restore-upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  }

  // AI
  const getAISettings = () => {
    return api.get('/ai/settings')
  }

  const updateAISettings = (data) => {
    return api.put('/ai/settings', data)
  }

  const testAIConnection = () => {
    return api.post('/ai/test-connection')
  }

  const aiPopulate = (data) => {
    return api.post('/ai/populate', data)
  }

  // Users (admin)
  const getUsers = () => api.get('/users')
  const getRoles = () => api.get('/users/roles')
  const createUser = (data) => api.post('/users', data)
  const getUser = (id) => api.get(`/users/${id}`)
  const updateUser = (id, data) => api.put(`/users/${id}`, data)
  const deleteUser = (id, action, transferToUserId = null) => {
    return api.delete(`/users/${id}`, {
      data: { action, transfer_to_user_id: transferToUserId }
    })
  }
  const getUserDestinationCount = (id) => api.get(`/users/${id}/destination-count`)

  // Sharing — destination-level
  const getDestinationShares = (destId) => api.get(`/destinations/${destId}/share`)
  const shareDestination = (destId, userId, permissionTier) =>
    api.post(`/destinations/${destId}/share`, { user_id: userId, permission_tier: permissionTier })
  const removeDestinationShare = (destId, shareId) =>
    api.delete(`/destinations/${destId}/share/${shareId}`)

  // Sharing — board-level
  const getBoardShares = () => api.get('/board/share')
  const shareBoard = (userId, permissionTier) =>
    api.post('/board/share', { user_id: userId, permission_tier: permissionTier })
  const removeBoardShare = (shareId) => api.delete(`/board/share/${shareId}`)

  // User lookup for sharing
  const getShareableUsers = () => api.get('/users/shareable')

  // Bulk operations
  const bulkEditDestinations = (data) => api.post('/destinations/bulk/edit', data)
  const bulkShareDestinations = (data) => api.post('/destinations/bulk/share', data)
  const bulkDeleteDestinations = (data) => api.post('/destinations/bulk/delete', data)

  return {
    getDestinations,
    getDestination,
    createDestination,
    updateDestination,
    deleteDestination,
    clipDestination,
    uploadMedia,
    uploadMediaFromUrl,
    getMedia,
    deleteMedia,
    setCoverImage,
    getAllJournalEntries,
    getJournalEntries,
    createJournalEntry,
    updateJournalEntry,
    deleteJournalEntry,
    geocode,
    reverseGeocode,
    getTags,
    renameTag,
    deleteTag,
    deleteUnusedTags,
    bulkMergeTags,
    getFilterOptions,
    getCustomFields,
    createCustomField,
    updateCustomField,
    deleteCustomField,
    searchAll,
    fetchLinkImage,
    addLink,
    updateLink,
    deleteLink,
    getExportFields,
    exportCsv,
    backupDownload,
    restoreUpload,
    getAISettings,
    updateAISettings,
    testAIConnection,
    aiPopulate,
    getUsers,
    getRoles,
    createUser,
    getUser,
    updateUser,
    deleteUser,
    getUserDestinationCount,
    getDestinationShares,
    shareDestination,
    removeDestinationShare,
    getBoardShares,
    shareBoard,
    removeBoardShare,
    getShareableUsers,
    bulkEditDestinations,
    bulkShareDestinations,
    bulkDeleteDestinations,
  }
}
