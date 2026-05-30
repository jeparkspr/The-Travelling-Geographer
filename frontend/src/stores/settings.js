import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useSettingsStore = defineStore('settings', () => {
  const showArchived = ref(loadSetting('tg-show-archived', false))
  const showToasts = ref(loadSetting('tg-show-toasts', true))
  const filterNoCover = ref(loadSetting('tg-filter-no-cover', false))
  const theme = ref(loadSetting('tg-theme', 'dark'))
  const useMetricUnits = ref(loadSetting('tg-use-metric', true))

  function loadSetting(key, defaultValue) {
    try {
      const stored = localStorage.getItem(key)
      if (stored === null) return defaultValue
      return JSON.parse(stored)
    } catch {
      return defaultValue
    }
  }

  function setShowArchived(value) {
    showArchived.value = value
    try {
      localStorage.setItem('tg-show-archived', JSON.stringify(value))
    } catch { /* ignore */ }
  }

  function setShowToasts(value) {
    showToasts.value = value
    try {
      localStorage.setItem('tg-show-toasts', JSON.stringify(value))
    } catch { /* ignore */ }
  }

  function setFilterNoCover(value) {
    filterNoCover.value = value
    try {
      localStorage.setItem('tg-filter-no-cover', JSON.stringify(value))
    } catch { /* ignore */ }
  }

  function setUseMetricUnits(value) {
    useMetricUnits.value = value
    try {
      localStorage.setItem('tg-use-metric', JSON.stringify(value))
    } catch { /* ignore */ }
  }

  function setTheme(value) {
    theme.value = value
    try {
      localStorage.setItem('tg-theme', JSON.stringify(value))
    } catch { /* ignore */ }
    applyTheme(value)
  }

  function applyTheme(themeValue) {
    document.documentElement.setAttribute('data-theme', themeValue)
  }

  // Initialize theme on store creation
  applyTheme(theme.value)

  const isDark = computed(() => theme.value === 'dark')

  return {
    showArchived,
    setShowArchived,
    showToasts,
    setShowToasts,
    filterNoCover,
    setFilterNoCover,
    useMetricUnits,
    setUseMetricUnits,
    theme,
    setTheme,
    applyTheme,
    isDark
  }
})
