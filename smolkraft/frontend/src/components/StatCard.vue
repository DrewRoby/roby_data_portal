<template>
  <div class="stat-card" :class="variant">
    <div class="stat-icon"><i :class="icon"></i></div>
    <div class="stat-body">
      <div class="stat-value">{{ value }}</div>
      <div class="stat-label">{{ label }}</div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  icon:    { type: String, required: true },
  value:   { type: [String, Number], required: true },
  label:   { type: String, required: true },
  variant: { type: String, default: 'default' },  // default | warning | danger | success
})
</script>

<style scoped>
.stat-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: #fff;
  border: 1px solid #e9ecef;
  border-radius: 10px;
  padding: 1.25rem 1.5rem;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.stat-icon {
  font-size: 2rem;
  width: 2.5rem;
  text-align: center;
  color: #adb5bd;
}
.stat-card.warning .stat-icon { color: #f0a500; }
.stat-card.danger  .stat-icon { color: #c0392b; }
.stat-card.success .stat-icon { color: #27ae60; }
.stat-value {
  font-size: 2rem;
  font-weight: 700;
  line-height: 1;
  color: #212529;
}
.stat-label {
  font-size: 0.85rem;
  color: #6c757d;
  margin-top: 0.2rem;
}
</style>
