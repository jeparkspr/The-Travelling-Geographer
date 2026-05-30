import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const useAuthStore = defineStore('auth', () => {
  // State
  const accessToken = ref(localStorage.getItem('access_token') || null)
  const refreshToken = ref(localStorage.getItem('refresh_token') || null)
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const setupRequired = ref(false)
  const loading = ref(true)

  // Getters
  const isAuthenticated = computed(() => !!accessToken.value && !!user.value)
  const isAdmin = computed(() => user.value?.permissions?.is_admin === true)
  const canManageUsers = computed(() => isAdmin.value || user.value?.permissions?.can_manage_users === true)
  const canManageSettings = computed(() => isAdmin.value || user.value?.permissions?.can_manage_settings === true)
  const displayName = computed(() => user.value?.display_name || '')
  const roles = computed(() => user.value?.roles || [])

  // Persist tokens
  function _saveTokens(access, refresh) {
    accessToken.value = access
    refreshToken.value = refresh
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  }

  function _saveUser(u) {
    user.value = u
    localStorage.setItem('user', JSON.stringify(u))
  }

  function _clearAll() {
    accessToken.value = null
    refreshToken.value = null
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  }

  // Actions
  async function checkSetup() {
    try {
      const { data } = await api.get('/setup/status')
      setupRequired.value = !data.is_setup_complete
      return data
    } catch {
      setupRequired.value = false
      return { is_setup_complete: true, has_users: true }
    }
  }

  async function setup(email, displayName, password) {
    const { data } = await api.post('/setup/initialize', { email, display_name: displayName, password })
    _saveTokens(data.access_token, data.refresh_token)
    await fetchMe()
    setupRequired.value = false
    return data
  }

  async function login(email, password) {
    const { data } = await api.post('/auth/login', { email, password })
    if (!data.success) {
      // Throw so the caller's catch block can display the message
      const err = new Error(data.detail || 'Login failed')
      err.response = { data: { detail: data.detail } }
      throw err
    }
    _saveTokens(data.access_token, data.refresh_token)
    await fetchMe()
    return data
  }

  async function register(email, displayName, password) {
    const { data } = await api.post('/auth/register', { email, display_name: displayName, password })
    _saveTokens(data.access_token, data.refresh_token)
    await fetchMe()
    return data
  }

  async function fetchMe() {
    try {
      const { data } = await api.get('/auth/me', {
        headers: { Authorization: `Bearer ${accessToken.value}` }
      })
      _saveUser(data)
      return data
    } catch {
      _clearAll()
      return null
    }
  }

  async function refreshAccessToken() {
    if (!refreshToken.value) {
      _clearAll()
      throw new Error('No refresh token')
    }
    try {
      const { data } = await api.post('/auth/refresh', { refresh_token: refreshToken.value })
      _saveTokens(data.access_token, data.refresh_token)
      return data.access_token
    } catch {
      _clearAll()
      throw new Error('Refresh failed')
    }
  }

  async function logout() {
    if (refreshToken.value) {
      try {
        await api.post('/auth/logout', { refresh_token: refreshToken.value }, {
          headers: { Authorization: `Bearer ${accessToken.value}` }
        })
      } catch {
        // Best-effort
      }
    }
    _clearAll()
  }

  async function init() {
    loading.value = true
    try {
      const status = await checkSetup()
      if (status.is_setup_complete && accessToken.value) {
        await fetchMe()
      }
    } finally {
      loading.value = false
    }
  }

  return {
    // State
    accessToken,
    refreshToken,
    user,
    setupRequired,
    loading,
    // Getters
    isAuthenticated,
    isAdmin,
    canManageUsers,
    canManageSettings,
    displayName,
    roles,
    // Actions
    checkSetup,
    setup,
    login,
    register,
    fetchMe,
    refreshAccessToken,
    logout,
    init,
  }
})
