<template>
  <div class="app">
    <header class="navbar" :class="{ 'navbar-light': isLightTheme }">
      <div class="navbar-container">
        <div class="navbar-brand">
          <router-link to="/" class="brand-text">
            <span class="brand-icon">🌎</span>The Travelling Geographer
          </router-link>
        </div>

        <button v-if="isMobile" class="menu-toggle" @click="mobileMenuOpen = !mobileMenuOpen">
          <i :class="mobileMenuOpen ? 'pi pi-times' : 'pi pi-bars'"></i>
        </button>

        <nav v-if="(!isMobile || mobileMenuOpen) && authStore.isAuthenticated" class="nav-menu">
          <router-link to="/" class="nav-link" @click="mobileMenuOpen = false">Dashboard</router-link>
          <router-link to="/map" class="nav-link" @click="mobileMenuOpen = false">Map</router-link>
          <router-link to="/destinations" class="nav-link" @click="mobileMenuOpen = false">Destinations</router-link>
          <router-link to="/journal" class="nav-link" @click="mobileMenuOpen = false">Journal</router-link>
          <router-link to="/help" class="nav-link" @click="mobileMenuOpen = false">Help</router-link>
          <span class="nav-separator"></span>
          <div class="user-menu" :class="{ open: userMenuOpen }">
            <button class="user-menu-trigger" @click.stop="userMenuOpen = !userMenuOpen">
              <i class="pi pi-user"></i>
              <span>{{ authStore.displayName }}</span>
              <i class="pi pi-chevron-down chevron"></i>
            </button>
            <div v-if="userMenuOpen" class="user-menu-dropdown">
              <router-link to="/settings" class="menu-item" @click="closeMenus">
                <i class="pi pi-cog"></i> Settings
              </router-link>
              <router-link v-if="authStore.canManageUsers" to="/admin/users" class="menu-item" @click="closeMenus">
                <i class="pi pi-users"></i> Users
              </router-link>
              <div class="menu-divider"></div>
              <a href="#" class="menu-item" @click.prevent="openAbout">
                <i class="pi pi-info-circle"></i> About
              </a>
              <a href="#" class="menu-item" @click.prevent="handleLogout">
                <i class="pi pi-sign-out"></i> Logout
              </a>
            </div>
          </div>
        </nav>
      </div>
    </header>

    <div v-if="isMobile && mobileMenuOpen" class="menu-backdrop" @click="mobileMenuOpen = false"></div>

    <main class="main-content">
      <router-view />
    </main>

    <Toast v-if="settingsStore.showToasts" />
    <ConfirmDialog />

    <!-- About Dialog -->
    <Dialog v-model:visible="aboutVisible" header="About" modal :style="{ width: '400px' }" :draggable="false">
      <div class="about-content">
        <div class="about-brand">
          <span class="about-icon">🌎</span>
          <h2>The Travelling Geographer</h2>
        </div>
        <div class="about-version">
          <span class="version-label">Version</span>
          <span class="version-value">{{ buildVersion || '...' }}</span>
        </div>
        <div v-if="buildDate" class="about-date">
          <span class="version-label">Built</span>
          <span class="version-value">{{ buildDate }}</span>
        </div>
        <div class="about-license">
          <p class="copyright">&copy; 2025-2026 John E Parks</p>
          <p class="license-text">Licensed under the <a href="#" @click.prevent="licenseVisible = true">MIT License</a></p>
        </div>
      </div>
    </Dialog>

    <!-- License Dialog -->
    <Dialog v-model:visible="licenseVisible" header="MIT License" modal :style="{ width: '520px' }" :draggable="false">
      <div class="license-content">
        <p>Copyright (c) 2025-2026 John E Parks</p>
        <p>Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:</p>
        <p>The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.</p>
        <p>THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.</p>
      </div>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSettingsStore } from '@/stores/settings'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const settingsStore = useSettingsStore()
const authStore = useAuthStore()

const isLightTheme = computed(() => !settingsStore.isDark)

const mobileMenuOpen = ref(false)
const isMobile = ref(false)
const userMenuOpen = ref(false)
const aboutVisible = ref(false)
const licenseVisible = ref(false)
const buildVersion = ref('')
const buildDate = ref('')

function closeMenus() {
  mobileMenuOpen.value = false
  userMenuOpen.value = false
}

function closeUserMenu(e) {
  // Close dropdown when clicking outside
  if (userMenuOpen.value) {
    userMenuOpen.value = false
  }
}

async function openAbout() {
  closeMenus()
  // Fetch build info (cached by browser after first load)
  try {
    const res = await fetch('/build-info.json')
    if (res.ok) {
      const info = await res.json()
      buildVersion.value = info.version
      buildDate.value = info.date
    }
  } catch {
    buildVersion.value = 'unknown'
  }
  aboutVisible.value = true
}

async function handleLogout() {
  closeMenus()
  await authStore.logout()
  router.push('/login')
}

const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
  if (window.innerWidth >= 768) {
    mobileMenuOpen.value = false
  }
}

watch(() => route.path, () => {
  closeMenus()
})

onMounted(async () => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  document.addEventListener('click', closeUserMenu)
  await authStore.init()
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
  document.removeEventListener('click', closeUserMenu)
})
</script>

<style scoped>
.app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.navbar {
  background-color: var(--nav-bg);
  border-bottom: 1px solid var(--nav-border);
  box-shadow: 0 1px 3px var(--color-shadow);
  position: sticky;
  top: 0;
  z-index: 100;
  height: 64px;

  --nav-bg: #0f172a;
  --nav-border: #1e293b;
  --nav-text: #94a3b8;
  --nav-text-active: #f1f5f9;
  --nav-hover-bg: #1e293b;
  --nav-separator: #334155;
}

.navbar-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 1rem;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.navbar-brand {
  display: flex;
  align-items: center;
}

.brand-text {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--nav-text-active);
  text-decoration: none;
  display: flex;
  align-items: center;
  transition: color 0.2s;
}

.brand-text:hover {
  color: var(--nav-text);
}

.nav-menu {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.nav-link {
  color: var(--nav-text);
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s;
}

.nav-link:hover,
.nav-link.router-link-active {
  color: var(--nav-text-active);
}

.nav-separator {
  width: 1px;
  height: 20px;
  background: var(--nav-separator);
  margin: 0 0.25rem;
}

.user-menu {
  position: relative;
}

.user-menu-trigger {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: none;
  border: 1px solid transparent;
  border-radius: 8px;
  padding: 0.4rem 0.75rem;
  color: var(--nav-text);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.user-menu-trigger:hover,
.user-menu.open .user-menu-trigger {
  color: var(--nav-text-active);
  background: var(--nav-hover-bg);
  border-color: var(--nav-separator);
}

.user-menu-trigger .chevron {
  font-size: 0.7rem;
  transition: transform 0.2s;
}

.user-menu.open .chevron {
  transform: rotate(180deg);
}

.user-menu-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  background: var(--nav-hover-bg);
  border: 1px solid var(--nav-separator);
  border-radius: 8px;
  min-width: 180px;
  padding: 0.35rem 0;
  box-shadow: 0 8px 24px var(--color-shadow);
  z-index: 200;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.6rem 1rem;
  color: var(--nav-text);
  text-decoration: none;
  font-size: 0.875rem;
  transition: all 0.15s;
}

.menu-item:hover {
  color: var(--nav-text-active);
  background: var(--nav-separator);
}

.menu-item .pi {
  font-size: 0.85rem;
  width: 1rem;
  text-align: center;
}

.menu-divider {
  height: 1px;
  background: var(--nav-separator);
  margin: 0.35rem 0;
}

.menu-toggle {
  display: none;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--nav-text);
  font-size: 1.5rem;
  padding: 0.5rem;
}

.main-content {
  flex: 1;
  background-color: var(--color-bg);
}

.brand-icon {
  margin-right: 0.5rem;
  font-size: 1.4rem;
}

.menu-backdrop {
  position: fixed;
  top: 64px;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 99;
}

.about-content {
  text-align: center;
  padding: 0.5rem 0;
}

.about-brand {
  margin-bottom: 1.5rem;
}

.about-icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 0.5rem;
}

.about-brand h2 {
  color: var(--color-text-bright);
  font-size: 1.2rem;
  margin: 0;
}

.about-version,
.about-date {
  display: flex;
  justify-content: center;
  gap: 0.75rem;
  padding: 0.35rem 0;
}

.version-label {
  color: var(--color-text-muted);
  font-size: 0.875rem;
}

.version-value {
  color: var(--color-text-bright);
  font-size: 0.875rem;
  font-weight: 500;
  font-family: 'Courier New', monospace;
}

.about-license {
  margin-top: 1.25rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border);
}

.about-license .copyright {
  color: var(--color-text-muted);
  font-size: 0.8rem;
  margin: 0 0 0.25rem 0;
}

.about-license .license-text {
  color: var(--color-text-muted);
  font-size: 0.75rem;
  margin: 0;
}

.about-license a {
  color: var(--color-accent-hover);
  text-decoration: none;
}

.about-license a:hover {
  text-decoration: underline;
}

.license-content {
  color: var(--color-text-muted);
  font-size: 0.8rem;
  line-height: 1.5;
}

.license-content p {
  margin: 0 0 0.75rem 0;
}

.license-content p:first-child {
  color: var(--color-text-bright);
  font-weight: 600;
}

.license-content p:last-child {
  margin-bottom: 0;
  font-size: 0.7rem;
}

@media (max-width: 767px) {
  .menu-toggle {
    display: block;
  }

  .navbar {
    height: 64px;
  }

  .navbar-container {
    flex-direction: row;
    align-items: center;
    padding: 0 1rem;
    height: 64px;
  }

  .nav-menu {
    position: absolute;
    top: 64px;
    left: 0;
    right: 0;
    background: var(--nav-bg);
    flex-direction: column;
    gap: 0;
    border-bottom: 1px solid var(--nav-border);
    padding: 0.5rem 0;
    z-index: 100;
    box-shadow: 0 4px 12px var(--color-shadow);
  }

  .nav-link {
    display: block;
    padding: 0.75rem 1rem;
    border-left: 3px solid transparent;
    color: var(--nav-text);
  }

  .nav-link.router-link-active {
    border-left-color: var(--color-accent);
    color: var(--nav-text-active);
    background-color: var(--nav-hover-bg);
  }

  .nav-separator {
    width: auto;
    height: 1px;
    background: var(--nav-border);
    margin: 0.25rem 1rem;
  }

  .user-menu-trigger {
    width: 100%;
    padding: 0.75rem 1rem;
    border-radius: 0;
    border: none;
    border-left: 3px solid transparent;
  }

  .user-menu-trigger:hover,
  .user-menu.open .user-menu-trigger {
    border-left-color: var(--color-accent);
    background: var(--nav-hover-bg);
  }

  .user-menu-dropdown {
    position: static;
    border: none;
    border-radius: 0;
    box-shadow: none;
    background: var(--nav-bg);
    min-width: auto;
    padding: 0;
  }

  .menu-item {
    padding-left: 2.5rem;
  }

  .menu-divider {
    margin: 0.25rem 1rem;
  }
}

/* Light theme navbar */
.navbar-light {
  --nav-bg: #ffffff;
  --nav-border: #e5e7eb;
  --nav-text: #6b7280;
  --nav-text-active: #111827;
  --nav-hover-bg: #f3f4f6;
  --nav-separator: #e5e7eb;
}
</style>