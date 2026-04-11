<template>
  <div>
    <h2 class="mb-4">Dashboard</h2>

    <div v-if="store.loading.analytics" class="text-center py-5">
      <div class="spinner-border text-secondary" role="status"></div>
    </div>

    <template v-else>
      <!-- Stat cards -->
      <div class="stat-grid mb-5">
        <StatCard
          icon="fa-solid fa-boxes-stacked"
          :value="store.currentInventory.length"
          label="Inventory Lots"
        />
        <StatCard
          icon="fa-solid fa-triangle-exclamation"
          :value="activeShortfalls.length"
          label="Active Shortfalls"
          :variant="activeShortfalls.length > 0 ? 'warning' : 'default'"
        />
        <StatCard
          icon="fa-solid fa-industry"
          :value="totalBatchesPossible"
          label="Batches Possible"
          variant="success"
        />
        <StatCard
          icon="fa-solid fa-list-check"
          :value="openOrders.length"
          label="Open Production Orders"
        />
      </div>

      <!-- Shortfall warnings -->
      <div v-if="activeShortfalls.length > 0" class="card mb-4">
        <div class="card-header d-flex align-items-center gap-2">
          <i class="fa-solid fa-triangle-exclamation text-warning"></i>
          <strong>Inventory Shortfalls</strong>
        </div>
        <div class="table-responsive">
          <table class="table table-sm table-hover mb-0">
            <thead class="table-light">
              <tr>
                <th>Material</th>
                <th class="text-end">Available</th>
                <th class="text-end">Needed</th>
                <th class="text-end">Shortfall</th>
                <th>UOM</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in activeShortfalls" :key="row.product_id">
                <td>{{ row.product_name }}</td>
                <td class="text-end">{{ formatQty(row.available_quantity) }}</td>
                <td class="text-end">{{ formatQty(row.needed_quantity) }}</td>
                <td class="text-end text-danger fw-semibold">{{ formatQty(row.shortfall) }}</td>
                <td>{{ row.uom }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Production possibilities -->
      <div class="card">
        <div class="card-header d-flex align-items-center gap-2">
          <i class="fa-solid fa-industry text-success"></i>
          <strong>Production Possibilities</strong>
        </div>
        <div class="table-responsive">
          <table class="table table-sm table-hover mb-0">
            <thead class="table-light">
              <tr>
                <th>Product</th>
                <th class="text-end">Batches Possible</th>
                <th>Limiting Component</th>
                <th class="text-end">Est. Cost / Batch</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="store.productionPossibilities.length === 0">
                <td colspan="4" class="text-center text-muted py-3">No recipes defined yet.</td>
              </tr>
              <tr v-for="row in store.productionPossibilities" :key="row.product_id">
                <td>{{ row.product_name }}</td>
                <td class="text-end">
                  <span :class="row.batches_possible > 0 ? 'text-success fw-semibold' : 'text-danger'">
                    {{ row.batches_possible }}
                  </span>
                </td>
                <td>{{ row.limiting_component ?? '—' }}</td>
                <td class="text-end">${{ Number(row.unit_cost).toFixed(2) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useSmolkraftStore } from '../stores/smolkraft'
import StatCard from '../components/StatCard.vue'

const store = useSmolkraftStore()

onMounted(async () => {
  await Promise.all([store.fetchAnalytics(), store.fetchProductionOrders()])
})

const activeShortfalls = computed(() =>
  store.shortfall.filter(s => Number(s.shortfall) > 0)
)

const totalBatchesPossible = computed(() =>
  store.productionPossibilities.reduce((sum, p) => sum + p.batches_possible, 0)
)

const openOrders = computed(() =>
  store.productionOrders.filter(o => ['planned', 'in_progress'].includes(o.status))
)

function formatQty(val) {
  return Number(val).toLocaleString(undefined, { maximumFractionDigits: 2 })
}
</script>

<style scoped>
.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}
</style>
