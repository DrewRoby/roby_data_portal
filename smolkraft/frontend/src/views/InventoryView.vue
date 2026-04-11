<template>
  <div>
    <h2 class="mb-4">Inventory</h2>

    <!-- Tabs -->
    <ul class="nav nav-tabs mb-4">
      <li class="nav-item" v-for="tab in tabs" :key="tab.id">
        <button
          class="nav-link"
          :class="{ active: activeTab === tab.id }"
          @click="switchTab(tab.id)"
        >{{ tab.label }}</button>
      </li>
    </ul>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-secondary" role="status"></div>
    </div>

    <template v-else>

      <!-- Tab: Current Lots -->
      <div v-if="activeTab === 'lots'">
        <div class="d-flex justify-content-end mb-3">
          <button class="btn btn-danger btn-sm" @click="openNew">
            <i class="fa-solid fa-plus me-1"></i>Add Lot
          </button>
        </div>
        <div class="card">
          <div class="table-responsive">
            <table class="table table-hover mb-0">
              <thead class="table-light">
                <tr>
                  <th>Lot #</th>
                  <th>Product</th>
                  <th class="text-end">Quantity</th>
                  <th>UOM</th>
                  <th>Expires</th>
                  <th>Location</th>
                  <th style="width:60px"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="store.currentInventory.length === 0">
                  <td colspan="7" class="text-center text-muted py-4">No inventory on hand.</td>
                </tr>
                <tr v-for="lot in store.currentInventory" :key="lot.id">
                  <td><span class="badge bg-light text-dark">{{ lot.lot_number ?? '—' }}</span></td>
                  <td class="fw-semibold">{{ lot.product_name }}</td>
                  <td class="text-end">{{ formatQty(lot.quantity) }}</td>
                  <td>{{ lot.uom }}</td>
                  <td :class="isExpired(lot.expiration_date) ? 'text-danger fw-semibold' : ''">
                    {{ lot.expiration_date ?? '—' }}
                    <span v-if="isExpired(lot.expiration_date)" class="badge bg-danger ms-1">Expired</span>
                  </td>
                  <td>{{ lot.location || '—' }}</td>
                  <td class="text-end">
                    <button class="btn btn-sm btn-outline-danger" @click="confirmDelete(lot.id)">
                      <i class="fa-solid fa-trash"></i>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Tab: Shortfall -->
      <div v-if="activeTab === 'shortfall'">
        <div v-if="store.shortfall.length === 0" class="text-center text-muted py-5">
          <i class="fa-solid fa-circle-check fa-2x text-success mb-2 d-block"></i>
          No shortfalls detected.
        </div>
        <div v-else class="card">
          <div class="table-responsive">
            <table class="table table-hover mb-0">
              <thead class="table-light">
                <tr>
                  <th>Material</th>
                  <th class="text-end">Available</th>
                  <th class="text-end">Needed</th>
                  <th class="text-end">Shortfall</th>
                  <th>UOM</th>
                  <th>Oldest Order</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="row in store.shortfall"
                  :key="row.product_id"
                  :class="Number(row.shortfall) > 0 ? 'table-warning' : ''"
                >
                  <td class="fw-semibold">{{ row.product_name }}</td>
                  <td class="text-end">{{ formatQty(row.available_quantity) }}</td>
                  <td class="text-end">{{ formatQty(row.needed_quantity) }}</td>
                  <td class="text-end" :class="Number(row.shortfall) > 0 ? 'text-danger fw-bold' : 'text-success'">
                    {{ formatQty(row.shortfall) }}
                  </td>
                  <td>{{ row.uom }}</td>
                  <td>{{ row.oldest_order_date ?? '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Tab: Production Possibilities -->
      <div v-if="activeTab === 'possibilities'">
        <div v-if="store.productionPossibilities.length === 0" class="text-center text-muted py-5">
          No recipes defined yet.
        </div>
        <div v-else class="pp-grid">
          <div v-for="pp in store.productionPossibilities" :key="pp.product_id" class="card pp-card">
            <div class="card-body">
              <div class="d-flex justify-content-between align-items-start mb-2">
                <h6 class="card-title mb-0">{{ pp.product_name }}</h6>
                <span
                  class="badge fs-6"
                  :class="pp.batches_possible > 0 ? 'bg-success' : 'bg-danger'"
                >{{ pp.batches_possible }} batch{{ pp.batches_possible === 1 ? '' : 'es' }}</span>
              </div>
              <p v-if="pp.limiting_component" class="text-muted small mb-2">
                <i class="fa-solid fa-link-slash me-1"></i>
                Limited by: {{ pp.limiting_component }}
              </p>
              <p class="text-muted small mb-3">Est. cost: ${{ Number(pp.unit_cost).toFixed(2) }} / batch</p>
              <table class="table table-sm table-bordered mb-0">
                <thead class="table-light">
                  <tr><th>Component</th><th>Available</th><th>Required</th><th>Max Batches</th></tr>
                </thead>
                <tbody>
                  <tr v-for="c in pp.component_materials" :key="c.material_id">
                    <td>{{ c.material_name }}</td>
                    <td>{{ formatQty(c.available) }}</td>
                    <td>{{ formatQty(c.required_per_batch) }}</td>
                    <td :class="c.max_batches === pp.batches_possible && pp.batches_possible < 9999 ? 'text-danger fw-semibold' : ''">
                      {{ c.max_batches >= 9999 ? '∞' : c.max_batches }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

    </template>

    <!-- Add lot modal -->
    <div v-if="showModal" class="sk-modal-overlay" @click.self="closeModal">
      <div class="sk-modal">
        <div class="sk-modal-header">
          <h5>Add Inventory Lot</h5>
          <button class="btn-close" @click="closeModal"></button>
        </div>
        <form @submit.prevent="saveLot">
          <div class="mb-3">
            <label class="form-label">Material</label>
            <select v-model="form.material" class="form-select" required>
              <option disabled value="">Select material…</option>
              <option v-for="m in store.materials" :key="m.id" :value="m.id">{{ m.short_name }}</option>
            </select>
          </div>
          <div class="row g-2 mb-3">
            <div class="col">
              <label class="form-label">Quantity</label>
              <input v-model="form.quantity" type="number" step="0.000001" class="form-control" required />
            </div>
            <div class="col">
              <label class="form-label">UOM</label>
              <select v-model="form.uom" class="form-select" required>
                <option v-for="uom in uoms" :key="uom" :value="uom">{{ uom }}</option>
              </select>
            </div>
          </div>
          <div class="mb-3">
            <label class="form-label">Location</label>
            <input v-model="form.location" class="form-control" maxlength="50" />
          </div>
          <p v-if="saveError" class="text-danger small">{{ saveError }}</p>
          <div class="d-flex justify-content-end gap-2">
            <button type="button" class="btn btn-outline-secondary btn-sm" @click="closeModal">Cancel</button>
            <button type="submit" class="btn btn-danger btn-sm" :disabled="saving">
              {{ saving ? 'Saving…' : 'Add Lot' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Delete confirm -->
    <div v-if="deleteId" class="sk-modal-overlay" @click.self="deleteId = null">
      <div class="sk-modal">
        <div class="sk-modal-header">
          <h5>Remove Lot</h5>
          <button class="btn-close" @click="deleteId = null"></button>
        </div>
        <p>Remove this inventory lot? This cannot be undone.</p>
        <div class="d-flex justify-content-end gap-2">
          <button class="btn btn-outline-secondary btn-sm" @click="deleteId = null">Cancel</button>
          <button class="btn btn-danger btn-sm" @click="doDelete">Remove</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useSmolkraftStore } from '../stores/smolkraft'

const store = useSmolkraftStore()

const tabs = [
  { id: 'lots',          label: 'Current Lots' },
  { id: 'shortfall',     label: 'Shortfall' },
  { id: 'possibilities', label: 'Production Possibilities' },
]
const activeTab = ref('lots')
const loading   = computed(() => store.loading.analytics || store.loading.inventory)

const showModal = ref(false)
const saving    = ref(false)
const saveError = ref('')
const deleteId  = ref(null)

const uoms = ['C','CL','CM','DL','FLOZ','G','IN','KG','L','LB','M','MG','ML','MM','OZ','PC','TBSP','THOU','TSP','UNIT','YD']
const form = reactive({ material: '', quantity: '', uom: 'UNIT', location: '' })

onMounted(async () => {
  await Promise.all([
    store.fetchAnalytics(),
    store.fetchInventory(),
    store.fetchMaterials(),
  ])
})

async function switchTab(id) {
  activeTab.value = id
  if (id !== 'lots') await store.fetchAnalytics()
}

function openNew() {
  form.material = ''; form.quantity = ''; form.uom = 'UNIT'; form.location = ''
  saveError.value = ''; showModal.value = true
}
function closeModal() { showModal.value = false }

async function saveLot() {
  saving.value = true; saveError.value = ''
  try {
    await store.createInventoryLot({ ...form })
    await store.fetchAnalytics()
    closeModal()
  } catch (e) {
    saveError.value = JSON.stringify(e.response?.data ?? e.message)
  } finally {
    saving.value = false
  }
}

function confirmDelete(id) { deleteId.value = id }
async function doDelete() {
  await store.deleteInventoryLot(deleteId.value)
  await store.fetchAnalytics()
  deleteId.value = null
}

function isExpired(dateStr) {
  return dateStr && new Date(dateStr) < new Date()
}
function formatQty(val) {
  return Number(val).toLocaleString(undefined, { maximumFractionDigits: 2 })
}
</script>

<style scoped>
.pp-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 1rem; }
.pp-card { border-radius: 8px; }
.sk-modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.4);
  display: flex; align-items: center; justify-content: center; z-index: 1050;
}
.sk-modal {
  background: #fff; border-radius: 10px; padding: 1.5rem;
  width: 100%; max-width: 480px; box-shadow: 0 8px 30px rgba(0,0,0,0.15);
}
.sk-modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
</style>
