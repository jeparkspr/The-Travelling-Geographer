<template>
  <div class="setup-page">
    <div class="setup-card">
      <div class="setup-header">
        <span class="brand-icon">🌎</span>
        <h1>The Travelling Geographer</h1>
        <p class="subtitle">Welcome! Let's set up your admin account.</p>
      </div>

      <div v-if="!done">
        <div class="step-indicator">
          <span class="step active">1. Create Admin</span>
        </div>

        <form @submit.prevent="handleSetup" class="setup-form">
          <div class="field">
            <label for="name">Display Name</label>
            <InputText id="name" v-model="displayName" placeholder="Your name" class="w-full" autofocus />
          </div>
          <div class="field">
            <label for="email">Email</label>
            <InputText id="email" v-model="email" type="email" placeholder="admin@example.com" class="w-full" />
          </div>
          <div class="field">
            <label for="password">Password</label>
            <InputText id="password" v-model="password" type="password" placeholder="Choose a strong password" class="w-full" />
            <div v-if="pwTouched && password" class="password-rules">
              <p class="rules-title">Password requirements:</p>
              <ul>
                <li v-for="rule in pwRules" :key="rule.label" :class="rule.met ? 'met' : 'unmet'">
                  <i :class="rule.met ? 'pi pi-check' : 'pi pi-times'" /> {{ rule.label }}
                </li>
              </ul>
              <p v-if="pwDisallowed" class="unmet">
                <i class="pi pi-times" /> Character '{{ pwDisallowed }}' is not allowed.
              </p>
              <p class="symbols-hint">Allowed symbols: {{ ALLOWED_SYMBOLS_DISPLAY }}</p>
            </div>
          </div>
          <div class="field">
            <label for="confirm">Confirm Password</label>
            <InputText id="confirm" v-model="confirmPassword" type="password" placeholder="Confirm password" class="w-full" />
          </div>

          <Button type="submit" label="Create Admin & Start" icon="pi pi-check" :loading="submitting" class="w-full"
            :disabled="password && !pwIsValid" />
          <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>
        </form>
      </div>

      <div v-else class="done-section">
        <i class="pi pi-check-circle done-icon"></i>
        <h2>Setup Complete!</h2>
        <p>Your admin account has been created. Redirecting...</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePasswordValidation } from '@/composables/usePasswordValidation'

const router = useRouter()
const authStore = useAuthStore()

const displayName = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const submitting = ref(false)
const errorMsg = ref('')
const done = ref(false)

const {
  rules: pwRules,
  disallowedChar: pwDisallowed,
  isValid: pwIsValid,
  touched: pwTouched,
  ALLOWED_SYMBOLS_DISPLAY,
} = usePasswordValidation(password)

async function handleSetup() {
  errorMsg.value = ''

  if (!displayName.value || !email.value || !password.value) {
    errorMsg.value = 'Please fill in all fields.'
    return
  }
  if (!pwIsValid.value) {
    errorMsg.value = 'Password does not meet complexity requirements.'
    return
  }
  if (password.value !== confirmPassword.value) {
    errorMsg.value = 'Passwords do not match.'
    return
  }

  submitting.value = true
  try {
    await authStore.setup(email.value, displayName.value, password.value)
    done.value = true
    setTimeout(() => router.push('/'), 1500)
  } catch (err) {
    errorMsg.value = err.response?.data?.detail || 'Setup failed. Please try again.'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.setup-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 64px);
  padding: 2rem;
}

.setup-card {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 2.5rem;
  width: 100%;
  max-width: 480px;
}

.setup-header {
  text-align: center;
  margin-bottom: 2rem;
}

.setup-header .brand-icon {
  font-size: 2.5rem;
}

.setup-header h1 {
  font-size: 1.25rem;
  color: #f1f5f9;
  margin-top: 0.5rem;
}

.subtitle {
  color: #94a3b8;
  margin-top: 0.5rem;
  font-size: 0.9rem;
}

.step-indicator {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  justify-content: center;
}

.step {
  color: #475569;
  font-size: 0.85rem;
  font-weight: 500;
}

.step.active {
  color: #60a5fa;
}

.setup-form .field {
  margin-bottom: 1rem;
}

.setup-form label {
  display: block;
  color: #94a3b8;
  margin-bottom: 0.35rem;
  font-size: 0.875rem;
}

.w-full {
  width: 100%;
}

.error-msg {
  color: #f87171;
  font-size: 0.875rem;
  margin-top: 0.75rem;
  text-align: center;
}

.done-section {
  text-align: center;
  padding: 2rem 0;
}

.done-icon {
  font-size: 3rem;
  color: #4ade80;
  margin-bottom: 1rem;
}

.done-section h2 {
  color: #f1f5f9;
  margin-bottom: 0.5rem;
}

.done-section p {
  color: #94a3b8;
}

.password-rules {
  margin-top: 0.5rem;
  padding: 0.6rem 0.8rem;
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 8px;
  font-size: 0.8rem;
}

.password-rules .rules-title {
  color: #94a3b8;
  margin: 0 0 0.35rem 0;
  font-weight: 600;
}

.password-rules ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.password-rules li {
  padding: 0.15rem 0;
}

.password-rules li i {
  margin-right: 0.4rem;
  font-size: 0.75rem;
}

.password-rules .met {
  color: #4ade80;
}

.password-rules .unmet {
  color: #f87171;
}

.password-rules .symbols-hint {
  color: #64748b;
  font-size: 0.75rem;
  margin: 0.4rem 0 0 0;
  word-break: break-all;
}
</style>
