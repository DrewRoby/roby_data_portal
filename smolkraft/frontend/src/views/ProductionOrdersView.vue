<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2 class="mb-0">Production Orders</h2>
      <button class="btn btn-danger btn-sm" @click="openNew">
        <i class="fa-solid fa-plus me-1"></i>New Order
      </button>
    </div>

    <!-- Status filter -->
    <div class="status-tabs mb-3">
      <button
        v-for="s in statusOptions"
        :key="s.value"
        class="status-tab"
        :class="{ active: statusFilter === s.value }"
        @click="statusFilter = s.value"
      >
        {{ s.label }}
        <span class="badge ms-1 rounded-pill" :class="s.badgeClass">
          {{ countByStatus(s.value) }}
        </span>
      </button>
    </div>

    <div v-if="store.loading.productionOrders" class="text-center py-5">
      <div class="spinner-border text-secondary" role="status"></div>
    </div>

    <div v-else class="card">
      <div class="table-responsive">
        <table class="table table-hover mb-0">
          <thead class="table-light">
            <tr>
              <th>Product</th>
              <th>Date</th>
              <th class="text-center">Batches</th>
              <th>Status</th>
              <th style="width:160px"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="filteredOrders.length === 0">
              <td colspan="5" class="text-center text-muted py-4">No orders found.</td>
            </tr>
            <tr v-for="o in filteredOrders" :key="o.id">
              <td class="fw-semibold">{{ o.product_name }}</td>
              <td>{{ o.production_date }}</td>
              <td class="text-center">{{ o.quantity }}</td>
              <td><span class="badge" :class="statusBadge(o.status)">{{ o.status }}</span></td>
              <td class="text-end">
                <div class="btn-group btn-group-sm">
                  <button
                    v-if="o.status === 'planned'"
                    class="btn btn-outline-primary"
                    @click="advanceStatus(o, 'in_progress')"
                  >Start</button>
                  <button
                    v-if="o.status === 'in_progress'"
                    class="btn btn-outline-success"
                    @click="advanceStatus(o, 'completed')"
                  >Complete</button>
                  <button
                    v-if="['planned','in_progress'].includes(o.status)"
                    class="btn btn-outline-secondary"
                    @click="advanceStatus(o, 'cancelled')"
                  >Cancel</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- New order modal -->
    <div v-if="showModal" class="sk-modal-overlay" @click.self="closeModal">
      <div class="sk-modal">
        <div class="sk-modal-header">
          <h5>New Production Order</h5>
          <button class="btn-close" @click="closeModal"></button>
        </div>
        <form @submit.prevent="save">
          <div class="mb-3">
            <label class="form-label">Recipe (BOM)</label>
            <select v-model="form.bom_header" class="form-select" required>
              <option disabled value="">Select a recipe…</option>
              <option v-for="b in store.boms" :key="b.id" :value="b.id">
                {{ b.product_name }}
              </option>
            </select>
          </div>
          <div class="row g-2 mb-3">
            <div class="col">
              <label class="form-label">Production Date</label>
              <input v-model="form.production_date" type="date" class="form-control" required />
            </div>
            <div class="col">
              <label class="form-label">Batches</label>
              <input v-model="form.quantity" type="number" min="1" class="form-control" required />
            </div>
          </div>
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
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useSmolkraftStore } from '../stores/smolkraft'

const store = useSmolkraftStore()

onMounted(async () => {
  await Promise.all([store.fetchProductionOrders(), store.fetchBOMs()])
})

const statusFilter = ref('all')
const showModal    = ref(false)
const saving       = ref(false)
const saveError    = ref('')

const statusOptions = [
  { value: 'all',         label: 'All',         badgeClass: 'bg-secondary' },
  { value: 'planned',     label: 'Planned',     badgeClass: 'bg-info text-dark' },
  { value: 'in_progress', label: 'In Progress', badgeClass: 'bg-primary' },
  { value: 'completed',   label: 'Completed',   badgeClass: 'bg-success' },
  { value: 'cancelled',   label: 'Cancelled',   badgeClass: 'bg-secondary' },
]

const form = reactive({ bom_header: '', production_date: '', quantity: 1 })

const filteredOrders = computed(() =>
  statusFilter.value === 'all'
    ? store.productionOrders
    : store.productionOrders.filter(o => o.status === statusFilter.value)
)

function countByStatus(status) {
  return status === 'all'
    ? store.productionOrders.length
    : store.productionOrders.filter(o => o.status === status).length
}

function statusBadge(status) {
  return {
    planned:     'bg-info text-dark',
    in_progress: 'bg-primary',
    completed:   'bg-success',
    cancelled:   'bg-secondary',
  }[status] ?? 'bg-secondary'
}

function openNew() {
  form.bom_header = ''; form.production_date = ''; form.quantity = 1
  saveError.value = ''; showModal.value = true
}
function closeModal() { showModal.value = false }

async function save() {
  saving.value = true; saveError.value = ''
  try {
    await store.createProductionOrder({ ...form })
    closeModal()
  } catch (e) {
    saveError.value = JSON.stringify(e.response?.data ?? e.message)
  } finally {
    saving.value = false
  }
}

async function advanceStatus(order, newStatus) {
  await store.updateProductionOrderStatus(order.id, newStatus)
}
</script>

<style scoped>
.status-tabs { display: flex; gap: 0.4rem; flex-wrap: wrap; }
.status-tab {
  padding: 0.35rem 0.9rem; border-radius: 20px; border: 1px solid #dee2e6;
  background: #fff; cursor: pointer; font-size: 0.9rem; transition: all 0.15s;
}
.status-tab.active { background: #c0392b; color: #fff; border-color: #c0392b; }
.status-tab:hover:not(.active) { background: #f1f3f5; }
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
