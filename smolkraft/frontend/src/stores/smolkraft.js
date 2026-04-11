import { defineStore } from 'pinia'
import client from '../api/client'

export const useSmolkraftStore = defineStore('smolkraft', {
  state: () => ({
    materials: [],
    boms: [],
    productionOrders: [],
    inventory: [],
    currentInventory: [],
    shortfall: [],
    productionPossibilities: [],
    loading: {
      materials: false,
      boms: false,
      productionOrders: false,
      inventory: false,
      analytics: false,
    },
    error: null,
  }),

  actions: {
    // ── Materials ──────────────────────────────────────────────────────────

    async fetchMaterials() {
      this.loading.materials = true
      try {
        const { data } = await client.get('/materials/')
        this.materials = data
      } catch (e) {
        this.error = e.response?.data || e.message
      } finally {
        this.loading.materials = false
      }
    },

    async createMaterial(payload) {
      const { data } = await client.post('/materials/', payload)
      this.materials.push(data)
      return data
    },

    async updateMaterial(id, payload) {
      const { data } = await client.patch(`/materials/${id}/`, payload)
      const idx = this.materials.findIndex(m => m.id === id)
      if (idx !== -1) this.materials[idx] = data
      return data
    },

    async deleteMaterial(id) {
      await client.delete(`/materials/${id}/`)
      this.materials = this.materials.filter(m => m.id !== id)
    },

    // ── BOMs ───────────────────────────────────────────────────────────────

    async fetchBOMs() {
      this.loading.boms = true
      try {
        const { data } = await client.get('/boms/')
        this.boms = data
      } catch (e) {
        this.error = e.response?.data || e.message
      } finally {
        this.loading.boms = false
      }
    },

    async createBOM(payload) {
      const { data } = await client.post('/boms/', payload)
      this.boms.push(data)
      return data
    },

    async deleteBOM(id) {
      await client.delete(`/boms/${id}/`)
      this.boms = this.boms.filter(b => b.id !== id)
    },

    // ── Production Orders ──────────────────────────────────────────────────

    async fetchProductionOrders() {
      this.loading.productionOrders = true
      try {
        const { data } = await client.get('/production-orders/')
        this.productionOrders = data
      } catch (e) {
        this.error = e.response?.data || e.message
      } finally {
        this.loading.productionOrders = false
      }
    },

    async createProductionOrder(payload) {
      const { data } = await client.post('/production-orders/', payload)
      this.productionOrders.push(data)
      return data
    },

    async updateProductionOrderStatus(id, status) {
      const { data } = await client.patch(`/production-orders/${id}/`, { status })
      const idx = this.productionOrders.findIndex(o => o.id === id)
      if (idx !== -1) this.productionOrders[idx] = data
      return data
    },

    async fetchProductionOrderDetail(id) {
      const { data } = await client.get(`/production-orders/${id}/`)
      return data
    },

    // ── Inventory ──────────────────────────────────────────────────────────

    async fetchInventory() {
      this.loading.inventory = true
      try {
        const { data } = await client.get('/inventory/')
        this.inventory = data
      } catch (e) {
        this.error = e.response?.data || e.message
      } finally {
        this.loading.inventory = false
      }
    },

    async createInventoryLot(payload) {
      const { data } = await client.post('/inventory/', payload)
      this.inventory.push(data)
      return data
    },

    async deleteInventoryLot(id) {
      await client.delete(`/inventory/${id}/`)
      this.inventory = this.inventory.filter(i => i.id !== id)
    },

    // ── Analytics ──────────────────────────────────────────────────────────

    async fetchAnalytics() {
      this.loading.analytics = true
      try {
        const [ci, sf, pp] = await Promise.all([
          client.get('/current-inventory/'),
          client.get('/inventory-shortfall/'),
          client.get('/production-possibilities/'),
        ])
        this.currentInventory = ci.data
        this.shortfall = sf.data
        this.productionPossibilities = pp.data
      } catch (e) {
        this.error = e.response?.data || e.message
      } finally {
        this.loading.analytics = false
      }
    },
  },
})
