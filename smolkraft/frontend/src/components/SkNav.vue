<template>
  <nav class="sk-nav mb-4">
    <div class="sk-nav-inner">
      <span class="sk-nav-brand">
        <i class="fa-solid fa-flask me-2"></i>Smolkraft
      </span>
      <div class="sk-nav-links">
        <router-link :to="{ name: 'dashboard' }" active-class="active">
          <i class="fa-solid fa-gauge-high me-1"></i>Dashboard
        </router-link>
        <router-link :to="{ name: 'materials' }" active-class="active">
          <i class="fa-solid fa-boxes-stacked me-1"></i>Materials
        </router-link>
        <router-link :to="{ name: 'boms' }" active-class="active">
          <i class="fa-solid fa-list-check me-1"></i>Recipes
        </router-link>
        <router-link :to="{ name: 'production-orders' }" active-class="active">
          <i class="fa-solid fa-industry me-1"></i>Production
        </router-link>
        <router-link :to="{ name: 'inventory' }" active-class="active">
          <i class="fa-solid fa-warehouse me-1"></i>Inventory
        </router-link>
      </div>
    </div>
  </nav>
</template>

<style scoped>
.sk-nav {
  background: #fff;
  border-bottom: 2px solid #e9ecef;
  padding: 0.5rem 0;
}
.sk-nav-inner {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  flex-wrap: wrap;
}
.sk-nav-brand {
  font-weight: 700;
  font-size: 1.1rem;
  color: #333;
  white-space: nowrap;
}
.sk-nav-links {
  display: flex;
  gap: 0.25rem;
  flex-wrap: wrap;
}
.sk-nav-links a {
  padding: 0.4rem 0.85rem;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 500;
  color: #555;
  text-decoration: none;
  transition: background 0.15s, color 0.15s;
}
.sk-nav-links a:hover {
  background: #f1f3f5;
  color: #333;
}
.sk-nav-links a.active {
  background: #c0392b;
  color: #fff;
}
</style>
