import { createRouter, createWebHistory } from 'vue-router'

import Dashboard from '@/views/Dashboard.vue'
import MapView from '@/views/MapView.vue'
import DestinationList from '@/views/DestinationList.vue'
import DestinationDetail from '@/views/DestinationDetail.vue'
import DestinationForm from '@/views/DestinationForm.vue'
import JournalView from '@/views/JournalView.vue'
import HelpView from '@/views/HelpView.vue'
import Settings from '@/views/Settings.vue'
import ClipPage from '@/views/ClipPage.vue'
import Login from '@/views/Login.vue'
import SetupWizard from '@/views/SetupWizard.vue'
import UserManagement from '@/views/UserManagement.vue'

const routes = [
  {
    path: '/login',
    component: Login,
    meta: { title: 'Sign In', public: true }
  },
  {
    path: '/setup',
    component: SetupWizard,
    meta: { title: 'Setup', public: true }
  },
  {
    path: '/',
    component: Dashboard,
    meta: { title: 'Dashboard' }
  },
  {
    path: '/map',
    component: MapView,
    meta: { title: 'Map' }
  },
  {
    path: '/destinations',
    component: DestinationList,
    meta: { title: 'Destinations' }
  },
  {
    path: '/destinations/new',
    component: DestinationForm,
    meta: { title: 'New Destination' }
  },
  {
    path: '/destinations/:id',
    component: DestinationDetail,
    meta: { title: 'Destination' }
  },
  {
    path: '/destinations/:id/edit',
    component: DestinationForm,
    meta: { title: 'Edit Destination' }
  },
  {
    path: '/journal',
    component: JournalView,
    meta: { title: 'Journal' }
  },
  {
    path: '/help',
    component: HelpView,
    meta: { title: 'Help' }
  },
  {
    path: '/settings',
    component: Settings,
    meta: { title: 'Settings' }
  },
  {
    path: '/admin/users',
    component: UserManagement,
    meta: { title: 'User Management', requiresAdmin: true }
  },
  {
    path: '/clip',
    component: ClipPage,
    meta: { title: 'Clip Page' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  document.title = `${to.meta.title || 'The Travelling Geographer'} - The Travelling Geographer`

  // Lazy-import auth store to avoid circular deps
  const { useAuthStore } = await import('@/stores/auth')
  const authStore = useAuthStore()

  // Wait for initial auth check if still loading
  if (authStore.loading) {
    await authStore.init()
  }

  // If setup hasn't been completed, redirect to setup wizard
  if (authStore.setupRequired && to.path !== '/setup') {
    return next('/setup')
  }

  // If setup is done but user is on /setup, redirect home
  if (!authStore.setupRequired && to.path === '/setup') {
    return next('/')
  }

  // Public routes don't need auth
  if (to.meta.public) {
    // If already authenticated and trying to access login, redirect home
    if (to.path === '/login' && authStore.isAuthenticated) {
      return next('/')
    }
    return next()
  }

  // Protected routes require authentication
  if (!authStore.isAuthenticated) {
    return next('/login')
  }

  // Admin-only routes
  if (to.meta.requiresAdmin && !authStore.canManageUsers) {
    return next('/')
  }

  next()
})

export default router