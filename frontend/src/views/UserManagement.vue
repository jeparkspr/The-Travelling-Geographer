<template>
  <div class="user-management">
    <div class="page-header">
      <h1>User Management</h1>
      <Button label="Add User" icon="pi pi-user-plus" @click="openCreateDialog" />
    </div>

    <DataTable :value="users" :loading="loading" stripedRows class="user-table">
      <Column field="display_name" header="Name" sortable />
      <Column field="email" header="Email" sortable />
      <Column header="Type" style="width: 140px">
        <template #body="{ data }">
          <Tag :value="data.roles.some(r => r.name === 'Administrator') ? 'Administrator' : 'User'"
            :severity="data.roles.some(r => r.name === 'Administrator') ? 'danger' : 'info'" />
        </template>
      </Column>
      <Column header="Status" style="width: 100px">
        <template #body="{ data }">
          <Tag :value="data.is_active ? 'Active' : 'Disabled'" :severity="data.is_active ? 'success' : 'secondary'" />
        </template>
      </Column>
      <Column header="Last Login" style="width: 160px">
        <template #body="{ data }">
          {{ data.last_login ? new Date(data.last_login).toLocaleDateString() : 'Never' }}
        </template>
      </Column>
      <Column header="Actions" style="width: 120px">
        <template #body="{ data }">
          <div class="action-buttons">
            <Button icon="pi pi-pencil" severity="info" text rounded @click="openEditDialog(data)" />
            <Button icon="pi pi-trash" severity="danger" text rounded @click="confirmDelete(data)"
              :disabled="data.id === currentUserId" />
          </div>
        </template>
      </Column>
    </DataTable>

    <!-- Create / Edit Dialog -->
    <Dialog v-model:visible="dialogVisible" :header="editingUser ? 'Edit User' : 'Create User'" modal
      :style="{ width: '450px' }">
      <div class="dialog-form">
        <div class="field">
          <label>Display Name</label>
          <InputText v-model="form.display_name" class="w-full" />
        </div>
        <div class="field">
          <label>Email</label>
          <InputText v-model="form.email" type="email" class="w-full" />
        </div>
        <div class="field">
          <label>{{ editingUser ? 'New Password (leave blank to keep)' : 'Password' }}</label>
          <InputText v-model="form.password" type="password" class="w-full" />
          <div v-if="pwTouched && form.password" class="password-rules">
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
        <div class="field-row">
          <div class="field">
            <Checkbox v-model="form.is_admin" :binary="true" inputId="admin" />
            <label for="admin" class="ml-2">Administrator</label>
          </div>
          <div class="field">
            <Checkbox v-model="form.is_active" :binary="true" inputId="active" />
            <label for="active" class="ml-2">Active</label>
          </div>
          <div class="field">
            <Checkbox v-model="form.is_approved" :binary="true" inputId="approved" />
            <label for="approved" class="ml-2">Approved</label>
          </div>
        </div>
      </div>
      <template #footer>
        <Button label="Cancel" severity="secondary" text @click="dialogVisible = false" />
        <Button :label="editingUser ? 'Save' : 'Create'" :loading="saving" @click="saveUser"
          :disabled="saveDisabled" />
      </template>
    </Dialog>

    <!-- Delete User Dialog -->
    <Dialog v-model:visible="deleteDialogVisible" header="Delete User" modal :style="{ width: '500px' }">
      <div v-if="deletingUser" class="delete-dialog">
        <p class="delete-warning">
          <i class="pi pi-exclamation-triangle"></i>
          You are about to delete <strong>{{ deletingUser.display_name }}</strong> ({{ deletingUser.email }}).
          This cannot be undone.
        </p>

        <div v-if="deletingUserDestCount > 0" class="delete-dest-info">
          <p>This user owns <strong>{{ deletingUserDestCount }}</strong> destination(s).
            What would you like to do with them?</p>

          <div class="delete-options">
            <div class="delete-option">
              <RadioButton v-model="deleteAction" value="transfer" inputId="action-transfer" />
              <label for="action-transfer">Transfer destinations to another user</label>
            </div>
            <div v-if="deleteAction === 'transfer'" class="transfer-target">
              <Dropdown
                v-model="transferTargetId"
                :options="transferTargetUsers"
                optionLabel="display_name"
                optionValue="id"
                placeholder="Select a user..."
                class="w-full"
              />
            </div>
            <div class="delete-option">
              <RadioButton v-model="deleteAction" value="delete" inputId="action-delete" />
              <label for="action-delete">Permanently delete all destinations and their media</label>
            </div>
          </div>
        </div>

        <div v-else class="delete-dest-info">
          <p>This user has no destinations.</p>
        </div>
      </div>
      <template #footer>
        <Button label="Cancel" severity="secondary" text @click="deleteDialogVisible = false" />
        <Button label="Delete User" severity="danger" icon="pi pi-trash"
          :loading="deleting"
          :disabled="deleteAction === 'transfer' && !transferTargetId"
          @click="executeDelete" />
      </template>
    </Dialog>

  </div>
</template>

<script setup>
import { ref, onMounted, computed, toRef } from 'vue'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import { useApi } from '@/composables/useApi'
import { useAuthStore } from '@/stores/auth'
import { usePasswordValidation } from '@/composables/usePasswordValidation'

const { getUsers, createUser, updateUser, deleteUser, getUserDestinationCount } = useApi()
const authStore = useAuthStore()
const confirm = useConfirm()
const toast = useToast()

const users = ref([])
const loading = ref(true)
const dialogVisible = ref(false)
const editingUser = ref(null)
const saving = ref(false)

// Delete dialog state
const deleteDialogVisible = ref(false)
const deletingUser = ref(null)
const deletingUserDestCount = ref(0)
const deleteAction = ref('transfer')
const transferTargetId = ref(null)
const deleting = ref(false)

const currentUserId = computed(() => authStore.user?.id)

const defaultForm = () => ({
  display_name: '',
  email: '',
  password: '',
  is_admin: false,
  is_active: true,
  is_approved: true,
})
const form = ref(defaultForm())

// Save disabled: only when a password is being typed and it's not yet valid
const saveDisabled = computed(() => {
  const pw = form.value.password
  if (!pw) return false
  return !pwIsValid.value
})

// Password validation — bound to form.password via a computed ref
const formPasswordRef = computed(() => form.value.password)
const {
  rules: pwRules,
  disallowedChar: pwDisallowed,
  isValid: pwIsValid,
  touched: pwTouched,
  ALLOWED_SYMBOLS_DISPLAY,
} = usePasswordValidation(formPasswordRef)

async function loadData() {
  loading.value = true
  try {
    const usersRes = await getUsers()
    users.value = usersRes.data
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load users', life: 3000 })
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  editingUser.value = null
  form.value = defaultForm()
  pwTouched.value = false
  dialogVisible.value = true
}

function openEditDialog(user) {
  editingUser.value = user
  form.value = {
    display_name: user.display_name,
    email: user.email,
    password: '',
    is_admin: user.roles.some(r => r.name === 'Administrator'),
    is_active: user.is_active,
    is_approved: user.is_approved,
  }
  pwTouched.value = false
  dialogVisible.value = true
}

async function saveUser() {
  if (!form.value.display_name || !form.value.email) {
    toast.add({ severity: 'warn', summary: 'Validation', detail: 'Name and email are required', life: 3000 })
    return
  }
  // Password validation for new users (required) and edits (only if provided)
  if (!editingUser.value && !form.value.password) {
    toast.add({ severity: 'warn', summary: 'Validation', detail: 'Password is required for new users', life: 3000 })
    return
  }
  if (form.value.password && !pwIsValid.value) {
    toast.add({ severity: 'warn', summary: 'Validation', detail: 'Password does not meet complexity requirements', life: 3000 })
    return
  }

  saving.value = true
  try {
    if (editingUser.value) {
      const payload = { ...form.value, role_names: [form.value.is_admin ? 'Administrator' : 'User'] }
      delete payload.is_admin
      if (!payload.password) delete payload.password
      await updateUser(editingUser.value.id, payload)
      toast.add({ severity: 'success', summary: 'Updated', detail: 'User updated successfully', life: 3000 })
    } else {
      const createPayload = { ...form.value, role_names: [form.value.is_admin ? 'Administrator' : 'User'] }
      delete createPayload.is_admin
      await createUser(createPayload)
      toast.add({ severity: 'success', summary: 'Created', detail: 'User created successfully', life: 3000 })
    }
    dialogVisible.value = false
    await loadData()
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.response?.data?.detail || 'Operation failed', life: 3000 })
  } finally {
    saving.value = false
  }
}

const transferTargetUsers = computed(() => {
  if (!deletingUser.value) return []
  return users.value.filter(u => u.id !== deletingUser.value.id)
})

async function confirmDelete(user) {
  deletingUser.value = user
  deleteAction.value = 'transfer'
  transferTargetId.value = null
  deleting.value = false

  // Fetch the destination count for this user
  try {
    const res = await getUserDestinationCount(user.id)
    deletingUserDestCount.value = res.data.count
  } catch {
    deletingUserDestCount.value = 0
  }

  deleteDialogVisible.value = true
}

async function executeDelete() {
  if (!deletingUser.value) return
  if (deleteAction.value === 'transfer' && deletingUserDestCount.value > 0 && !transferTargetId.value) {
    toast.add({ severity: 'warn', summary: 'Required', detail: 'Select a user to transfer destinations to', life: 3000 })
    return
  }

  deleting.value = true
  try {
    await deleteUser(
      deletingUser.value.id,
      deleteAction.value,
      deleteAction.value === 'transfer' ? transferTargetId.value : null
    )
    const action = deleteAction.value === 'transfer' ? 'transferred' : 'deleted'
    toast.add({
      severity: 'success',
      summary: 'Deleted',
      detail: `User deleted. Destinations ${action}.`,
      life: 3000
    })
    deleteDialogVisible.value = false
    await loadData()
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.response?.data?.detail || 'Delete failed', life: 3000 })
  } finally {
    deleting.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.user-management {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.page-header h1 {
  color: #f1f5f9;
  font-size: 1.5rem;
}

.action-buttons {
  display: flex;
  gap: 0.25rem;
}

.dialog-form .field {
  margin-bottom: 1rem;
}

.dialog-form label {
  display: block;
  color: #94a3b8;
  margin-bottom: 0.35rem;
  font-size: 0.875rem;
}

.field-row {
  display: flex;
  gap: 2rem;
  margin-top: 0.5rem;
}

.field-row .field {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.field-row label {
  margin-bottom: 0 !important;
}

.w-full {
  width: 100%;
}

.ml-2 {
  margin-left: 0.5rem;
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

.delete-dialog {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.delete-warning {
  color: var(--color-text);
  line-height: 1.6;
}

.delete-warning i {
  color: #f59e0b;
  margin-right: 0.5rem;
}

.delete-dest-info {
  background: var(--color-bg-light, #1e293b);
  border: 1px solid var(--color-border, #334155);
  border-radius: 0.375rem;
  padding: 1rem;
}

.delete-dest-info p {
  margin: 0 0 0.75rem 0;
  color: var(--color-text, #cbd5e1);
  line-height: 1.5;
}

.delete-options {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.delete-option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.delete-option label {
  color: var(--color-text, #cbd5e1);
  font-size: 0.875rem;
  cursor: pointer;
}

.transfer-target {
  margin-left: 1.75rem;
}

@media (max-width: 768px) {
  .user-management {
    padding: 0.5rem;
  }
}
</style>
