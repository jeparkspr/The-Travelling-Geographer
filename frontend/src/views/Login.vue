<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <span class="brand-icon">🌎</span>
        <h1>The Travelling Geographer</h1>
      </div>

      <div v-if="mode === 'login'">
        <h2>Sign In</h2>
        <form @submit.prevent="handleLogin" class="login-form">
          <div class="field">
            <label for="email">Email</label>
            <InputText id="email" v-model="email" type="email" placeholder="you@example.com" class="w-full" autofocus autocomplete="username" />
          </div>
          <div class="field">
            <label for="password">Password</label>
            <InputText id="password" v-model="password" type="password" placeholder="Password" class="w-full" autocomplete="current-password" />
          </div>
          <Button type="submit" label="Sign In" icon="pi pi-sign-in" :loading="submitting" class="w-full" />
          <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>
          <p v-if="errorMsg" class="forgot-link">
            <a href="#" @click.prevent="showRecovery = true">Forgot your password?</a>
          </p>
          <div v-if="showRecovery" class="recovery-info">
            <p>Contact your administrator to reset your password.</p>
          </div>
        </form>
        <p class="switch-mode">
          Don't have an account?
          <a href="#" @click.prevent="mode = 'register'">Register</a>
        </p>
      </div>

      <div v-else>
        <h2>Create Account</h2>
        <form @submit.prevent="handleRegister" class="login-form">
          <div class="field">
            <label for="reg-name">Display Name</label>
            <InputText id="reg-name" v-model="regName" placeholder="Your name" class="w-full" autofocus autocomplete="name" />
          </div>
          <div class="field">
            <label for="reg-email">Email</label>
            <InputText id="reg-email" v-model="regEmail" type="email" placeholder="you@example.com" class="w-full" autocomplete="email" />
          </div>
          <div class="field">
            <label for="reg-password">Password</label>
            <InputText id="reg-password" v-model="regPassword" type="password" placeholder="Choose a password" class="w-full" autocomplete="new-password" />
            <div v-if="pwTouched && regPassword" class="password-rules">
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
            <label for="reg-confirm">Confirm Password</label>
            <InputText id="reg-confirm" v-model="regConfirm" type="password" placeholder="Confirm password" class="w-full" autocomplete="new-password" />
          </div>
          <Button type="submit" label="Create Account" icon="pi pi-user-plus" :loading="submitting" class="w-full"
            :disabled="regPassword && !pwIsValid" />
          <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>
        </form>
        <p class="switch-mode">
          Already have an account?
          <a href="#" @click.prevent="mode = 'login'">Sign In</a>
        </p>
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

const mode = ref('login')
const email = ref('')
const password = ref('')
const regName = ref('')
const regEmail = ref('')
const regPassword = ref('')
const regConfirm = ref('')
const submitting = ref(false)
const errorMsg = ref('')
const showRecovery = ref(false)

const {
  rules: pwRules,
  disallowedChar: pwDisallowed,
  isValid: pwIsValid,
  touched: pwTouched,
  ALLOWED_SYMBOLS_DISPLAY,
} = usePasswordValidation(regPassword)

async function handleLogin() {
  errorMsg.value = ''
  if (!email.value || !password.value) {
    errorMsg.value = 'Please fill in all fields.'
    return
  }
  submitting.value = true
  try {
    await authStore.login(email.value, password.value)
    router.push('/')
  } catch (err) {
    errorMsg.value = err.response?.data?.detail || 'Login failed. Please check your credentials.'
  } finally {
    submitting.value = false
  }
}

async function handleRegister() {
  errorMsg.value = ''
  if (!regName.value || !regEmail.value || !regPassword.value) {
    errorMsg.value = 'Please fill in all fields.'
    return
  }
  if (!pwIsValid.value) {
    errorMsg.value = 'Password does not meet complexity requirements.'
    return
  }
  if (regPassword.value !== regConfirm.value) {
    errorMsg.value = 'Passwords do not match.'
    return
  }
  submitting.value = true
  try {
    await authStore.register(regEmail.value, regName.value, regPassword.value)
    router.push('/')
  } catch (err) {
    errorMsg.value = err.response?.data?.detail || 'Registration failed.'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 64px);
  padding: 2rem;
}

.login-card {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 2.5rem;
  width: 100%;
  max-width: 420px;
}

.login-header {
  text-align: center;
  margin-bottom: 2rem;
}

.login-header .brand-icon {
  font-size: 2.5rem;
}

.login-header h1 {
  font-size: 1.25rem;
  color: #f1f5f9;
  margin-top: 0.5rem;
}

h2 {
  font-size: 1.1rem;
  color: #cbd5e1;
  margin-bottom: 1.5rem;
}

.login-form .field {
  margin-bottom: 1rem;
}

.login-form label {
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

.switch-mode {
  text-align: center;
  margin-top: 1.25rem;
  color: #94a3b8;
  font-size: 0.875rem;
}

.switch-mode a {
  color: #60a5fa;
  text-decoration: none;
}

.switch-mode a:hover {
  text-decoration: underline;
}

.forgot-link {
  text-align: center;
  margin-top: 0.5rem;
  font-size: 0.825rem;
}

.forgot-link a {
  color: #60a5fa;
  text-decoration: none;
}

.forgot-link a:hover {
  text-decoration: underline;
}

.recovery-info {
  margin-top: 0.75rem;
  padding: 0.75rem 1rem;
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 8px;
  font-size: 0.825rem;
  color: #94a3b8;
  text-align: center;
}

.recovery-info p {
  margin: 0;
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
