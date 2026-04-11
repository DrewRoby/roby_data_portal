<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2 class="mb-0">Recipes (Bills of Materials)</h2>
      <button class="btn btn-danger btn-sm" @click="openNew">
        <i class="fa-solid fa-plus me-1"></i>New Recipe
      </button>
    </div>

    <div v-if="store.loading.boms" class="text-center py-5">
      <div class="spinner-border text-secondary" role="status"></div>
    </div>

    <div v-else-if="store.boms.length === 0" class="text-center text-muted py-5">
      No recipes yet. Create your first bill of materials to get started.
    </div>

    <div v-else class="bom-grid">
      <div
        v-for="bom in store.boms"
        :key="bom.id"
        class="bom-card card"
        :class="{ expanded: expanded === bom.id }"
      >
        <div class="bom-card-header" @click="toggleExpand(bom.id)">
          <div>
            <div class="bom-name">{{ bom.product_name }}</div>
            <div class="bom-meta text-muted">
              {{ bom.output_quantity }} {{ bom.output_uom }} per batch
              &nbsp;·&nbsp;
              {{ bom.materials?.length ?? 0 }} ingredient{{ bom.materials?.length === 1 ? '' : 's' }}
            </div>
          </div>
          <div class="d-flex align-items-center gap-2">
            <i class="fa-solid fa-chevron-down bom-chevron" :class="{ rotated: expanded === bom.id }"></i>
            <button class="btn btn-sm btn-outline-danger" @click.stop="confirmDelete(bom)">
              <i class="fa-solid fa-trash"></i>
            </button>
          </div>
        </div>

        <div v-if="expanded === bom.id" class="bom-detail">
          <p v-if="bom.description" class="text-muted mb-3">{{ bom.description }}</p>

          <h6 class="mb-2">Ingredients</h6>
          <table class="table table-sm table-bordered mb-3">
            <thead class="table-light">
              <tr><th>Material</th><th class="text-end">Quantity</th><th>UOM</th></tr>
            </thead>
            <tbody>
              <tr v-if="!bom.materials?.length">
                <td colspan="3" class="text-muted text-center">No ingredients defined.</td>
              </tr>
              <tr v-for="line in bom.materials" :key="line.id">
                <td>{{ line.material_name }}</td>
                <td class="text-end">{{ line.quantity }}</td>
                <td>{{ line.uom }}</td>
              </tr>
            </tbody>
          </table>

          <h6 class="mb-2">Operations</h6>
          <ol class="ps-3 text-muted" v-if="bom.operations?.length">
            <li v-for="op in bom.operations" :key="op.id" class="mb-1">
              {{ op.description }}
              <span v-if="op.estimated_time" class="badge bg-light text-dark ms-1">
                {{ op.estimated_time }} {{ op.time_uom }}
              </span>
            </li>
          </ol>
          <p v-else class="text-muted small">No operations defined.</p>
        </div>
      </div>
    </div>

    <!-- New BOM modal (header only — lines/ops managed separately) -->
    <div v-if="showModal" class="sk-modal-overlay" @click.self="closeModal">
      <div class="sk-modal">
        <div class="sk-modal-header">
          <h5>New Recipe</h5>
          <button class="btn-close" @click="closeModal"></button>
        </div>
        <form @submit.prevent="save">
          <div class="mb-3">
            <label class="form-label">Product Name</label>
            <input v-model="form.product_name" class="form-control" required maxlength="64" />
          </div>
          <div class="mb-3">
            <label class="form-label">Description</label>
            <textarea v-model="form.description" class="form-control" rows="2" maxlength="256"></textarea>
          </div>
          <div class="row g-2 mb-3">
            <div class="col">
              <label class="form-label">Output Quantity</label>
              <input v-model="form.output_quantity" type="number" step="0.0001" class="form-control" required />
            </div>
            <div class="col">
              <label class="form-label">Output UOM</label>
              <select v-model="form.output_uom" class="form-select" required>
                <option v-for="uom in uoms" :key="uom" :value="uom">{{ uom }}</option>
              </select>
            </div>
          </div>
          <p class="text-muted small">Ingredients and operations can be added via the API after creation.</p>
          <p v-if="saveError" class="text-danger small">{{ saveError }}</p>
          <div class="d-flex justify-content-end gap-2">
            <button type="button" class="btn btn-outline-secondary btn-sm" @click="closeModal">Cancel</button>
            <button type="submit" class="btn btn-danger btn-sm" :disabled="saving">
              {{ saving ? 'Creating…' : 'Create' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Delete confirmation -->
    <div v-if="deleteTarget" class="sk-modal-overlay" @click.self="deleteTarget = null">
      <div class="sk-modal">
        <div class="sk-modal-header">
          <h5>Delete Recipe</h5>
          <button class="btn-close" @click="deleteTarget = null"></button>
        </div>
        <p>Delete <strong>{{ deleteTarget.product_name }}</strong>? This cannot be undone.</p>
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
onMounted(() => store.fetchBOMs())

const expanded   = ref(null)
const showModal  = ref(false)
const saving     = ref(false)
const saveError  = ref('')
const deleteTarget = ref(null)

const uoms = ['C','CL','CM','DL','FLOZ','G','IN','KG','L','LB','M','MG','ML','MM','OZ','PC','TBSP','THOU','TSP','UNIT','YD']
const form = reactive({ product_name: '', description: '', output_quantity: 1, output_uom: 'UNIT' })

function toggleExpand(id) { expanded.value = expanded.value === id ? null : id }

function openNew() {
  form.product_name = ''; form.description = ''; form.output_quantity = 1; form.output_uom = 'UNIT'
  saveError.value = ''; showModal.value = true
}
function closeModal() { showModal.value = false }

async function save() {
  saving.value = true; saveError.value = ''
  try {
    await store.createBOM({ ...form })
    closeModal()
  } catch (e) {
    saveError.value = JSON.stringify(e.response?.data ?? e.message)
  } finally {
    saving.value = false
  }
}

function confirmDelete(bom) { deleteTarget.value = bom }
async function doDelete() {
  await store.deleteBOM(deleteTarget.value.id)
  deleteTarget.value = null
  if (expanded.value === deleteTarget.value?.id) expanded.value = null
}
</script>

<style scoped>
.bom-grid { display: flex; flex-direction: column; gap: 0.75rem; }
.bom-card { border-radius: 8px; overflow: hidden; }
.bom-card-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 1rem 1.25rem; cursor: pointer;
}
.bom-card-header:hover { background: #f8f9fa; }
.bom-name { font-weight: 600; font-size: 1.05rem; }
.bom-meta { font-size: 0.85rem; margin-top: 0.15rem; }
.bom-detail { padding: 0 1.25rem 1.25rem; border-top: 1px solid #e9ecef; padding-top: 1rem; }
.bom-chevron { transition: transform 0.2s; color: #adb5bd; }
.bom-chevron.rotated { transform: rotate(180deg); }
.sk-modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.4);
  display: flex; align-items: center; justify-content: center; z-index: 1050;
}
.sk-modal {
  background: #fff; border-radius: 10px; padding: 1.5rem;
  width: 100%; max-width: 520px; box-shadow: 0 8px 30px rgba(0,0,0,0.15);
}
.sk-modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
</style>
