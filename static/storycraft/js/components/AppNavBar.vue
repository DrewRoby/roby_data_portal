<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
    <div class="container-fluid">
      <a class="navbar-brand" href="/">
        <i class="fas fa-book me-2"></i>
        Storycraft
      </a>
      <button class="navbar-toggler" type="button" data-bs-toggle="collapse" 
              data-bs-target="#navbarNav" aria-controls="navbarNav" 
              aria-expanded="false" aria-label="Toggle navigation">
        <span class="navbar-toggler-icon"></span>
      </button>
      
      <div class="collapse navbar-collapse" id="navbarNav">
        <ul class="navbar-nav me-auto">
          <li class="nav-item">
            <a class="nav-link" href="/storycraft">
              <i class="fas fa-home me-1"></i> Dashboard
            </a>
          </li>
          <li class="nav-item">
            <a class="nav-link" href="/storycraft/stories">
              <i class="fas fa-book-open me-1"></i> My Stories
            </a>
          </li>
        </ul>
        
        <div class="d-flex">
          <div class="dropdown">
            <button class="btn btn-primary dropdown-toggle" type="button" 
                    id="appDropdown" data-bs-toggle="dropdown" 
                    aria-expanded="false">
              <i class="fas fa-th me-1"></i> Apps
            </button>
            <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="appDropdown">
              <li v-if="loadingApps" class="dropdown-item text-center">
                <div class="spinner-border spinner-border-sm" role="status">
                  <span class="visually-hidden">Loading...</span>
                </div>
                Loading...
              </li>
              <li v-if="errorMessage" class="dropdown-item text-danger">
                {{ errorMessage }}
              </li>
              <li v-for="app in apps" :key="app.app_id">
                <a class="dropdown-item" :href="app.link">
                  <i :class="['fas', app.icon, 'me-2']" 
                     :style="{ color: app.background_color }"></i>
                  {{ app.name }}
                </a>
              </li>
            </ul>
          </div>
          
          <div class="dropdown ms-2">
            <button class="btn btn-primary dropdown-toggle" type="button" 
                    id="userDropdown" data-bs-toggle="dropdown" 
                    aria-expanded="false">
              <i class="fas fa-user me-1"></i>
            </button>
            <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="userDropdown">
              <li>
                <span class="dropdown-item-text fw-bold">{{ username }}</span>
              </li>
              <li><hr class="dropdown-divider"></li>
              <li>
                <a class="dropdown-item" href="/logout">
                  <i class="fas fa-sign-out-alt me-2"></i> Logout
                </a>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>

<script>
export default {
  name: 'AppNavbar',
  
  props: {
    username: {
      type: String,
      default: 'User'
    }
  },
  
  data() {
    return {
      apps: [],
      loadingApps: true,
      errorMessage: ''
    }
  },
  
  mounted() {
    this.fetchApps();
  },
  
  methods: {
    fetchApps() {
      this.loadingApps = true;
      this.errorMessage = '';
      
      fetch('/api/user/apps/', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCookie('csrftoken')
        },
        credentials: 'same-origin'
      })
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to fetch apps');
        }
        return response.json();
      })
      .then(data => {
        if (data.status === 'success') {
          this.apps = data.apps;
        } else {
          throw new Error(data.error || 'Failed to fetch apps');
        }
      })
      .catch(error => {
        console.error('Error fetching apps:', error);
        this.errorMessage = 'Could not load applications';
      })
      .finally(() => {
        this.loadingApps = false;
      });
    },
    
    getCookie(name) {
      let cookieValue = null;
      if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
          const cookie = cookies[i].trim();
          if (cookie.substring(0, name.length + 1) === (name + '=')) {
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            break;
          }
        }
      }
      return cookieValue;
    }
  }
}
</script>

<style scoped>
.dropdown-item {
  display: flex;
  align-items: center;
}
</style>