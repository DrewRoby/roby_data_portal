import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '../views/DashboardView.vue'
import MaterialsView from '../views/MaterialsView.vue'
import BOMsView from '../views/BOMsView.vue'
import ProductionOrdersView from '../views/ProductionOrdersView.vue'
import InventoryView from '../views/InventoryView.vue'

// Base is /smolkraft/ — routes below are relative to that.
const routes = [
  { path: '/',                  name: 'dashboard',          component: DashboardView },
  { path: '/materials/',        name: 'materials',          component: MaterialsView },
  { path: '/boms/',             name: 'boms',               component: BOMsView },
  { path: '/production-orders/', name: 'production-orders', component: ProductionOrdersView },
  { path: '/inventory/',        name: 'inventory',          component: InventoryView },
]

export default createRouter({
  history: createWebHistory('/smolkraft/'),
  routes,
})
