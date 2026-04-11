<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2 class="mb-0">Materials</h2>
      <button class="btn btn-danger btn-sm" @click="openNew">
        <i class="fa-solid fa-plus me-1"></i>Add Material
      </button>
    </div>

    <div v-if="store.loading.materials" class="text-center py-5">
      <div class="spinner-border text-secondary" role="status"></div>
    </div>

    <div v-else class="card">
      <div class="table-responsive">
        <table class="table table-hover mb-0">
          <thead class="table-light">
            <tr>
              <th>Short Name</th>
              <th>Description</th>
              <th style="width:120px"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="store.materials.length === 0">
              <td colspan="3" class="text-center text-muted py-4">
                No materials yet. Add one to get started.
              </td>
            </tr>
            <tr v-for="m in store.materials" :key="m.id">
              <td class="fw-semibold">{{ m.short_name }}</td>
              <td class="text-muted">{{ m.description }}</td>
              <td class="text-end">
                <button class="btn btn-sm btn-outline-secondary me-1" @click="openEdit(m)">
                  <i class="fa-solid fa-pencil"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" @click="confirmDelete(m)">
                  <i class="fa-solid fa-trash"></i>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Add / Edit modal -->
    <div v-if="showModal" class="sk-modal-overlay" @click.self="closeModal">
      <div class="sk-modal">
        <div class="sk-modal-header">
          <h5>{{ editing ? 'Edit Material' : 'New Material' }}</h5>
          <button class="btn-close" @click="closeModal"></button>
        </div>
        <form @submit.prevent="save">
          <div class="mb-3">
            <label class="form-label">Short Name</label>
            <input v-model="form.short_name" class="form-control" required maxlength="64" />
          </div>
          <div class="mb-3">
            <label class="form-label">Description</label>
            <textarea v-model="form.description" class="form-control" rows="3" maxlength="512"></textarea>
          </div>
          <p v-if="saveError" class="text-danger small">{{ saveError }}</p>
          <div class="d-flex justify-content-end gap-2">
            <button type="button" class="btn btn-outline-secondary btn-sm" @click="closeModal">Cancel</button>
            <button type="submit" class="btn btn-danger btn-sm" :disabled="saving">
              {{ saving ? 'Saving…' : 'Save' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Delete confirmation -->
    <div v-if="deleteTarget" class="sk-modal-overlay" @click.self="deleteTarget = null">
      <div class="sk-modal">
        <div class="sk-modal-header">
          <h5>Delete Material</h5>
          <button class="btn-close" @click="deleteTarget = null"></button>
        </div>
        <p>Delete <strong>{{ deleteTarget.short_name }}</strong>? This cannot be undone.</p>
        <div class="d-flex justify-content-end gap-2">
          <button class="btn btn-outline-secondary btn-sm" @click="deleteTarget = null">Cancel</button>
          <button class="btn btn-danger btn-sm" @click="doDelete">Delete</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useSmolkraftStore } from '../stores/smolkraft'

const store = useSmolkraftStore()
onMounted(() => store.fetchMaterials())

const showModal  = ref(false)
const editing    = ref(null)   // material object if editing, null if new
const saving     = ref(false)
const saveError  = ref('')
const deleteTarget = ref(null)

const form = reactive({ short_name: '', description: '' })

function openNew() {
  editing.value = null
  form.short_name = ''
  form.description = ''
  saveError.value = ''
  showModal.value = true
}

function openEdit(m) {
  editing.value = m
  form.short_name = m.short_name
  form.description = m.description
  saveError.value = ''
  showModal.value = true
}

function closeModal() { showModal.value = false }

async function save() {
  saving.value = true
  saveError.value = ''
  try {
    if (editing.value) {
      await store.updateMaterial(editing.value.id, { ...form })
    } else {
      await store.createMaterial({ ...form })
    }
    closeModal()
  } catch (e) {
    saveError.value = JSON.stringify(e.response?.data ?? e.message)
  } finally {
    saving.value = false
  }
}

function confirmDelete(m) { deleteTarget.value = m }

async function doDelete() {
  await store.deleteMaterial(deleteTarget.value.id)
  deleteTarget.value = null
}
</script>

<style scoped>
.sk-modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex; align-items: center; justify-content: center;
  z-index: 1050;
}
.sk-modal {
  background: #fff;
  border-radius: 10px;
  padding: 1.5rem;
  width: 100%; max-width: 480px;
  box-shadow: 0 8px 30px rgba(0,0,0,0.15);
}
.sk-modal-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 1rem;
}
</style>
