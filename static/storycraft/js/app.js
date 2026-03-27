// static/storycraft/js/app.js
// This needs to be included as a module script in your HTML
// Add type="module" to the script tag loading this file

import { createApp } from 'vue';

// Initialize Vue when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Register the character view component
    const characterViewComponent = {
        props: {
            character: {
                type: Object,
                required: true
            },
            storyData: {
                type: Object,
                required: true
            },
            showDeleteButton: {
                type: Boolean,
                default: true
            }
        },
        // Include the template string from CharacterView.vue
        template: `
<template>
  <div class="character-view-container">
    <div class="character-header" :style="{ backgroundColor: characterColor }">
      <div class="character-avatar">
        <div class="avatar-placeholder">
          <span>{{ characterInitials }}</span>
        </div>
      </div>
      <div class="character-info">
        <h2>{{ character.name }}</h2>
        <div class="character-meta">
          <span v-if="character.age" class="meta-item">
            <i class="fas fa-birthday-cake"></i> Age: {{ character.age }}
          </span>
          <span v-if="character.archetype" class="meta-item">
            <i class="fas fa-theater-masks"></i> {{ character.archetype }}
          </span>
        </div>
      </div>
      <div class="view-actions">
        <button @click="editCharacter" class="action-btn">
          <i class="fas fa-edit"></i> Edit
        </button>
        <button v-if="showDeleteButton" @click="confirmDelete" class="action-btn danger">
          <i class="fas fa-trash"></i> Delete
        </button>
      </div>
    </div>
    
    <div class="character-tabs">
      <button 
        v-for="tab in tabs" 
        :key="tab.id"
        :class="['tab-btn', { active: activeTab === tab.id }]"
        @click="activeTab = tab.id"
      >
        <i :class="tab.icon"></i> {{ tab.label }}
      </button>
    </div>
    
    <div class="character-content">
      <!-- Profile Tab -->
      <div v-if="activeTab === 'profile'" class="tab-content">
        <div class="profile-section">
          <h3>Description</h3>
          <p v-if="character.description">{{ character.description }}</p>
          <p v-else class="empty-state">No description available.</p>
        </div>

        <div v-if="hasAttributes" class="profile-section">
          <h3>Attributes</h3>
          <div class="attributes-grid">
            <div v-if="character.attributes.personality" class="attribute-card">
              <div class="attribute-header">
                <i class="fas fa-brain"></i>
                <h4>Personality</h4>
              </div>
              <p>{{ character.attributes.personality }}</p>
            </div>
            
            <div v-if="character.attributes.appearance" class="attribute-card">
              <div class="attribute-header">
                <i class="fas fa-user"></i>
                <h4>Appearance</h4>
              </div>
              <p>{{ character.attributes.appearance }}</p>
            </div>
            
            <div v-if="character.attributes.goals" class="attribute-card">
              <div class="attribute-header">
                <i class="fas fa-bullseye"></i>
                <h4>Goals</h4>
              </div>
              <p>{{ character.attributes.goals }}</p>
            </div>
            
            <div v-for="(value, key) in customAttributes" :key="key" class="attribute-card">
              <div class="attribute-header">
                <i class="fas fa-clipboard-list"></i>
                <h4>{{ formatAttributeName(key) }}</h4>
              </div>
              <p>{{ value }}</p>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Relationships Tab -->
      <div v-else-if="activeTab === 'relationships'" class="tab-content">
        <div class="relationships-container">
          <div class="section-header">
            <h3>Character Relationships</h3>
            <button @click="addRelationship" class="add-btn">
              <i class="fas fa-plus"></i> Add
            </button>
          </div>
          
          <div v-if="relationships.length === 0" class="empty-state">
            <p>No relationships defined yet.</p>
            <button @click="addRelationship" class="action-btn">
              <i class="fas fa-plus"></i> Add Relationship
            </button>
          </div>
          
          <div v-else class="relationships-list">
            <div v-for="relationship in relationships" :key="relationship.id" class="relationship-card">
              <div class="relationship-character">
                <div class="mini-avatar">
                  <span>{{ getCharacterInitials(relationship.otherCharacter) }}</span>
                </div>
                <h4>{{ relationship.otherCharacter.name }}</h4>
              </div>
              
              <div class="relationship-type">
                <div class="relationship-arrow">
                  <div class="arrow-label">{{ relationship.relationship }}</div>
                  <div class="arrow-line"></div>
                </div>
              </div>
              
              <div class="relationship-actions">
                <button @click="editRelationship(relationship)" class="icon-btn">
                  <i class="fas fa-edit"></i>
                </button>
                <button @click="deleteRelationship(relationship)" class="icon-btn danger">
                  <i class="fas fa-trash"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Scenes Tab -->
      <div v-else-if="activeTab === 'scenes'" class="tab-content">
        <div class="scenes-container">
          <h3>Scenes featuring {{ character.name }}</h3>
          
          <div v-if="characterScenes.length === 0" class="empty-state">
            <p>This character doesn't appear in any scenes yet.</p>
          </div>
          
          <div v-else class="scenes-timeline">
            <div v-for="scene in characterScenes" :key="scene.id" class="scene-card">
              <div class="scene-number">
                <div class="scene-sequence">{{ scene.sequence_number }}</div>
              </div>
              
              <div class="scene-content">
                <h4>{{ scene.name }}</h4>
                <p class="scene-description">{{ scene.description }}</p>
                
                <div class="scene-meta">
                  <span class="meta-item">
                    <i class="fas fa-map-marker-alt"></i> {{ getSettingName(scene.setting_id) }}
                  </span>
                  <span class="meta-item">
                    <i class="fas fa-project-diagram"></i> {{ getPlotName(scene.plot_id) }}
                  </span>
                </div>
                
                <div class="scene-actions">
                  <button @click="viewScene(scene)" class="scene-action-btn">
                    <i class="fas fa-eye"></i> View
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Arc Tab -->
      <div v-else-if="activeTab === 'arc'" class="tab-content">
        <div class="arc-container">
          <h3>Character Arc</h3>
          
          <div class="arc-visualization">
            <!-- Arc visualization would go here -->
            <div class="arc-chart-placeholder">
              <span>Character arc visualization will be displayed here</span>
            </div>
          </div>
          
          <div class="arc-points">
            <h4>Key Development Points</h4>
            <div class="empty-state">
              <p>No character arc points defined yet.</p>
              <button class="action-btn">
                <i class="fas fa-plus"></i> Add Development Point
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Delete confirmation modal -->
    <div v-if="showDeleteModal" class="modal-overlay">
      <div class="modal-container">
        <div class="modal-header danger">
          <h3>Delete Character</h3>
          <button @click="showDeleteModal = false" class="close-btn">×</button>
        </div>
        <div class="modal-content">
          <p>Are you sure you want to delete <strong>{{ character.name }}</strong>?</p>
          <p class="warning-text">This action cannot be undone. This will remove the character from all scenes.</p>
        </div>
        <div class="modal-footer">
          <button @click="showDeleteModal = false" class="btn-secondary">Cancel</button>
          <button @click="deleteCharacter" class="btn-danger">Delete Character</button>
        </div>
      </div>
    </div>
    
    <!-- Add/Edit relationship modal -->
    <div v-if="showRelationshipModal" class="modal-overlay">
      <div class="modal-container">
        <div class="modal-header">
          <h3>{{ editingRelationship ? 'Edit' : 'Add' }} Relationship</h3>
          <button @click="cancelRelationshipEdit" class="close-btn">×</button>
        </div>
        <div class="modal-content">
          <div class="form-group">
            <label>Related Character</label>
            <select v-model="relationshipForm.targetId" class="form-control">
              <option value="">Select a character</option>
              <option v-for="char in otherCharacters" :key="char.id" :value="char.id">
                {{ char.name }}
              </option>
            </select>
          </div>
          
          <div class="form-group">
            <label>Relationship Type</label>
            <input 
              type="text" 
              v-model="relationshipForm.relationship" 
              class="form-control"
              placeholder="e.g. Friend, Enemy, Mentor, etc."
            >
          </div>
          
          <div class="form-group">
            <label>Description</label>
            <textarea 
              v-model="relationshipForm.description" 
              class="form-control"
              placeholder="Describe the nature of their relationship"
              rows="3"
            ></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="cancelRelationshipEdit" class="btn-secondary">Cancel</button>
          <button @click="saveRelationship" class="btn-primary">
            {{ editingRelationship ? 'Update' : 'Create' }} Relationship
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'CharacterView',
  props: {
    character: {
      type: Object,
      required: true
    },
    storyData: {
      type: Object,
      required: true
    },
    showDeleteButton: {
      type: Boolean,
      default: true
    }
  },
  data() {
    return {
      activeTab: 'profile',
      tabs: [
        { id: 'profile', label: 'Profile', icon: 'fas fa-user' },
        { id: 'relationships', label: 'Relationships', icon: 'fas fa-users' },
        { id: 'scenes', label: 'Scenes', icon: 'fas fa-film' },
        { id: 'arc', label: 'Character Arc', icon: 'fas fa-chart-line' }
      ],
      showDeleteModal: false,
      showRelationshipModal: false,
      editingRelationship: null,
      relationshipForm: {
        targetId: '',
        relationship: '',
        description: ''
      }
    };
  },
  computed: {
    characterInitials() {
      if (!this.character.name) return '?';
      
      return this.character.name
        .split(' ')
        .map(word => word.charAt(0).toUpperCase())
        .slice(0, 2)
        .join('');
    },
    characterColor() {
      // Generate a consistent color based on character name
      const hash = this.character.name.split('').reduce((acc, char) => {
        return char.charCodeAt(0) + ((acc << 5) - acc);
      }, 0);
      
      // Use pastel colors for better aesthetics
      const h = Math.abs(hash) % 360;
      return \`hsl(${h}, 70%, 85%)\`;
    },
    hasAttributes() {
      return this.character.attributes && Object.keys(this.character.attributes).length > 0;
    },
    customAttributes() {
      if (!this.character.attributes) return {};
      
      // Return all attributes except the standard ones
      const { personality, appearance, goals, ...others } = this.character.attributes;
      return others;
    },
    relationships() {
      if (!this.storyData.relationships) return [];
      
      // Find all relationships involving this character
      return this.storyData.relationships
        .filter(rel => 
          rel.source_id === this.character.id || 
          rel.target_id === this.character.id
        )
        .map(rel => {
          // Determine the "other" character in the relationship
          const isSource = rel.source_id === this.character.id;
          const otherId = isSource ? rel.target_id : rel.source_id;
          const otherCharacter = this.storyData.characters.find(c => c.id === otherId);
          
          return {
            id: rel.id,
            relationship: rel.relationship,
            description: rel.description,
            isSource,
            otherCharacter
          };
        });
    },
    characterScenes() {
      if (!this.storyData.scenes) return [];
      
      // Find all scenes where this character appears
      return this.storyData.scenes
        .filter(scene => scene.characters.includes(this.character.id))
        .sort((a, b) => (a.sequence_number || 0) - (b.sequence_number || 0));
    },
    otherCharacters() {
      if (!this.storyData.characters) return [];
      
      // All characters except this one
      return this.storyData.characters.filter(char => 
        char.id !== this.character.id
      );
    }
  },
  methods: {
    formatAttributeName(key) {
      // Convert camelCase or snake_case to Title Case
      return key
        .replace(/_/g, ' ')
        .replace(/([A-Z])/g, ' $1')
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
        .join(' ');
    },
    getCharacterInitials(character) {
      if (!character || !character.name) return '?';
      
      return character.name
        .split(' ')
        .map(word => word.charAt(0).toUpperCase())
        .slice(0, 2)
        .join('');
    },
    getSettingName(settingId) {
      if (!settingId) return 'Unknown';
      
      const setting = this.storyData.settings.find(s => s.id === settingId);
      return setting ? setting.name : 'Unknown';
    },
    getPlotName(plotId) {
      if (!plotId) return 'Unknown';
      
      const plot = this.storyData.plots.find(p => p.id === plotId);
      return plot ? plot.name : 'Unknown';
    },
    editCharacter() {
      this.$emit('edit-character', this.character);
    },
    confirmDelete() {
      this.showDeleteModal = true;
    },
    deleteCharacter() {
      this.$emit('delete-character', this.character);
      this.showDeleteModal = false;
    },
    addRelationship() {
      this.editingRelationship = null;
      this.relationshipForm = {
        targetId: '',
        relationship: '',
        description: ''
      };
      this.showRelationshipModal = true;
    },
    editRelationship(relationship) {
      this.editingRelationship = relationship;
      this.relationshipForm = {
        targetId: relationship.otherCharacter.id,
        relationship: relationship.relationship,
        description: relationship.description || ''
      };
      this.showRelationshipModal = true;
    },
    saveRelationship() {
      if (!this.relationshipForm.targetId || !this.relationshipForm.relationship) {
        // Validate form
        alert('Please select a character and enter a relationship type');
        return;
      }
      
      if (this.editingRelationship) {
        // Update existing relationship
        this.$emit('update-relationship', {
          id: this.editingRelationship.id,
          source_id: this.editingRelationship.isSource ? this.character.id : this.relationshipForm.targetId,
          target_id: this.editingRelationship.isSource ? this.relationshipForm.targetId : this.character.id,
          relationship: this.relationshipForm.relationship,
          description: this.relationshipForm.description
        });
      } else {
        // Create new relationship
        this.$emit('create-relationship', {
          source_id: this.character.id,
          target_id: this.relationshipForm.targetId,
          relationship: this.relationshipForm.relationship,
          description: this.relationshipForm.description
        });
      }
      
      this.showRelationshipModal = false;
    },
    cancelRelationshipEdit() {
      this.showRelationshipModal = false;
    },
    deleteRelationship(relationship) {
      if (confirm(\`Are you sure you want to delete the relationship with ${relationship.otherCharacter.name}?\`)) {
        this.$emit('delete-relationship', relationship.id);
      }
    },
    viewScene(scene) {
      this.$emit('view-scene', scene);
    }
  }
};
</script>

<style scoped>
.character-view-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #f9f9f9;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.character-header {
  display: flex;
  align-items: center;
  padding: 20px;
  background-color: #e0e0e0;
  color: #333;
}

.character-avatar {
  margin-right: 20px;
}

.avatar-placeholder {
  width: 80px;
  height: 80px;
  background-color: rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.5);
}

.character-info {
  flex-grow: 1;
}

.character-info h2 {
  margin: 0 0 5px 0;
  font-size: 1.8rem;
}

.character-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.9rem;
  color: rgba(0, 0, 0, 0.6);
}

.view-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 8px 12px;
  border: none;
  border-radius: 4px;
  background-color: rgba(0, 0, 0, 0.1);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  color: #333;
  font-size: 0.9rem;
}

.action-btn:hover {
  background-color: rgba(0, 0, 0, 0.2);
}

.action-btn.danger {
  color: #e53935;
}

.action-btn.danger:hover {
  background-color: rgba(229, 57, 53, 0.1);
}

.character-tabs {
  display: flex;
  background-color: #fff;
  border-bottom: 1px solid #e0e0e0;
}

.tab-btn {
  padding: 12px 16px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 6px;
  border-bottom: 2px solid transparent;
  color: #666;
}

.tab-btn:hover {
  background-color: #f5f5f5;
}

.tab-btn.active {
  border-bottom-color: #2196F3;
  color: #2196F3;
  font-weight: 500;
}

.character-content {
  flex-grow: 1;
  overflow-y: auto;
  background-color: #fff;
}

.tab-content {
  padding: 20px;
}

.profile-section {
  margin-bottom: 24px;
}

.profile-section h3 {
  font-size: 1.2rem;
  margin: 0 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid #eee;
  color: #444;
}

.attributes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 16px;
}

.attribute-card {
  background-color: #f9f9f9;
  border-radius: 6px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.attribute-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.attribute-header i {
  color: #666;
}

.attribute-header h4 {
  margin: 0;
  font-size: 1rem;
  color: #444;
}

.attribute-card p {
  margin: 0;
  font-size: 0.95rem;
  line-height: 1.4;
}

.empty-state {
  text-align: center;
  padding: 24px;
  background-color: #f9f9f9;
  border-radius: 6px;
  color: #666;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h3 {
  margin: 0;
  font-size: 1.2rem;
  color: #444;
}

.add-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  background-color: #e3f2fd;
  color: #2196F3;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.9rem;
}

.add-btn:hover {
  background-color: #bbdefb;
}

.relationships-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.relationship-card {
  display: flex;
  align-items: center;
  background-color: #fff;
  border-radius: 6px;
  padding: 12px 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.relationship-character {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 160px;
}

.mini-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: #e0e0e0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  font-weight: 600;
  color: #666;
}

.relationship-character h4 {
  margin: 0;
  font-size: 1rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.relationship-type {
  flex-grow: 1;
  padding: 0 16px;
}

.relationship-arrow {
  position: relative;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.arrow-label {
  background-color: #f5f5f5;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.85rem;
  z-index: 1;
}

.arrow-line {
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background-color: #ddd;
  z-index: 0;
}

.relationship-actions {
  display: flex;
  gap: 8px;
}

.icon-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 4px;
  background-color: #f5f5f5;
  color: #666;
  cursor: pointer;
}

.icon-btn:hover {
  background-color: #e0e0e0;
}

.icon-btn.danger {
  color: #e53935;
}

.icon-btn.danger:hover {
  background-color: #ffebee;
}

.scenes-timeline {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.scene-card {
  display: flex;
  background-color: #fff;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.scene-number {
  width: 40px;
  background-color: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
}

.scene-sequence {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background-color: #e0e0e0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 600;
}

.scene-content {
  flex-grow: 1;
  padding: 12px 16px;
}

.scene-content h4 {
  margin: 0 0 4px 0;
  font-size: 1rem;
}

.scene-description {
  margin: 0 0 8px 0;
  font-size: 0.9rem;
  color: #666;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.scene-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 8px;
}

.scene-actions {
  display: flex;
  justify-content: flex-end;
}

.scene-action-btn {
  padding: 4px 8px;
  border: none;
  border-radius: 4px;
  background-color: #f5f5f5;
  cursor: pointer;
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  gap: 4px;
}

.scene-action-btn:hover {
  background-color: #e0e0e0;
}

.arc-chart-placeholder {
  height: 200px;
  background-color: #f5f5f5;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  margin-bottom: 24px;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-container {
  width: 500px;
  max-width: 90%;
  background-color: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.modal-header {
  padding: 16px;
  background-color: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e0e0e0;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.2rem;
  color: #333;
}

.modal-header.danger {
  background-color: #ffebee;
  color: #e53935;
}

.modal-content {
  padding: 16px;
}

.modal-footer {
  padding: 16px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  border-top: 1px solid #e0e0e0;
}

.btn-secondary {
  padding: 8px 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background-color: #fff;
  color: #666;
  cursor: pointer;
}

.btn-secondary:hover {
  background-color: #f5f5f5;
}

.btn-primary {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  background-color: #2196F3;
  color: #fff;
  cursor: pointer;
}

.btn-primary:hover {
  background-color: #1976D2;
}

.btn-danger {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  background-color: #e53935;
  color: #fff;
  cursor: pointer;
}

.btn-danger:hover {
  background-color: #c62828;
}

.warning-text {
  color: #e53935;
  font-size: 0.9rem;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
  color: #444;
}

.form-control {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.95rem;
}

.form-control:focus {
  outline: none;
  border-color: #2196F3;
  box-shadow: 0 0 0 2px rgba(33, 150, 243, 0.2);
}

textarea.form-control {
  min-height: 80px;
  resize: vertical;
}
`,
        data() {
            return {
                activeTab: 'profile',
                tabs: [
                    { id: 'profile', label: 'Profile', icon: 'fas fa-user' },
                    { id: 'relationships', label: 'Relationships', icon: 'fas fa-users' },
                    { id: 'scenes', label: 'Scenes', icon: 'fas fa-film' },
                    { id: 'arc', label: 'Character Arc', icon: 'fas fa-chart-line' }
                ],
                showDeleteModal: false,
                showRelationshipModal: false,
                editingRelationship: null,
                relationshipForm: {
                    targetId: '',
                    relationship: '',
                    description: ''
                }
            };
        },
        computed: {
            characterInitials() {
                if (!this.character.name) return '?';
                
                return this.character.name
                    .split(' ')
                    .map(word => word.charAt(0).toUpperCase())
                    .slice(0, 2)
                    .join('');
            },
            characterColor() {
                // Generate a consistent color based on character name
                const hash = this.character.name.split('').reduce((acc, char) => {
                    return char.charCodeAt(0) + ((acc << 5) - acc);
                }, 0);
                
                // Use pastel colors for better aesthetics
                const h = Math.abs(hash) % 360;
                return `hsl(${h}, 70%, 85%)`;
            },
            hasAttributes() {
                return this.character.attributes && Object.keys(this.character.attributes).length > 0;
            },
            customAttributes() {
                if (!this.character.attributes) return {};
                
                // Return all attributes except the standard ones
                const { personality, appearance, goals, ...others } = this.character.attributes;
                return others;
            },
            relationships() {
                if (!this.storyData.relationships) return [];
                
                // Find all relationships involving this character
                return this.storyData.relationships
                    .filter(rel => 
                        rel.source_id === this.character.id || 
                        rel.target_id === this.character.id
                    )
                    .map(rel => {
                        // Determine the "other" character in the relationship
                        const isSource = rel.source_id === this.character.id;
                        const otherId = isSource ? rel.target_id : rel.source_id;
                        const otherCharacter = this.storyData.characters.find(c => c.id === otherId);
                        
                        return {
                            id: rel.id,
                            relationship: rel.relationship,
                            description: rel.description,
                            isSource,
                            otherCharacter
                        };
                    });
            },
            characterScenes() {
                if (!this.storyData.scenes) return [];
                
                // Find all scenes where this character appears
                return this.storyData.scenes
                    .filter(scene => scene.characters.includes(this.character.id))
                    .sort((a, b) => (a.sequence_number || 0) - (b.sequence_number || 0));
            },
            otherCharacters() {
                if (!this.storyData.characters) return [];
                
                // All characters except this one
                return this.storyData.characters.filter(char => 
                    char.id !== this.character.id
                );
            }
        },
        methods: {
            formatAttributeName(key) {
                // Convert camelCase or snake_case to Title Case
                return key
                    .replace(/_/g, ' ')
                    .replace(/([A-Z])/g, ' $1')
                    .split(' ')
                    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
                    .join(' ');
            },
            getCharacterInitials(character) {
                if (!character || !character.name) return '?';
                
                return character.name
                    .split(' ')
                    .map(word => word.charAt(0).toUpperCase())
                    .slice(0, 2)
                    .join('');
            },
            getSettingName(settingId) {
                if (!settingId) return 'Unknown';
                
                const setting = this.storyData.settings.find(s => s.id === settingId);
                return setting ? setting.name : 'Unknown';
            },
            getPlotName(plotId) {
                if (!plotId) return 'Unknown';
                
                const plot = this.storyData.plots.find(p => p.id === plotId);
                return plot ? plot.name : 'Unknown';
            },
            editCharacter() {
                this.$emit('edit-character', this.character);
            },
            confirmDelete() {
                this.showDeleteModal = true;
            },
            deleteCharacter() {
                this.$emit('delete-character', this.character);
                this.showDeleteModal = false;
            },
            addRelationship() {
                this.editingRelationship = null;
                this.relationshipForm = {
                    targetId: '',
                    relationship: '',
                    description: ''
                };
                this.showRelationshipModal = true;
            },
            editRelationship(relationship) {
                this.editingRelationship = relationship;
                this.relationshipForm = {
                    targetId: relationship.otherCharacter.id,
                    relationship: relationship.relationship,
                    description: relationship.description || ''
                };
                this.showRelationshipModal = true;
            },
            saveRelationship() {
                if (!this.relationshipForm.targetId || !this.relationshipForm.relationship) {
                    // Validate form
                    alert('Please select a character and enter a relationship type');
                    return;
                }
                
                if (this.editingRelationship) {
                    // Update existing relationship
                    this.$emit('update-relationship', {
                        id: this.editingRelationship.id,
                        source_id: this.editingRelationship.isSource ? this.character.id : this.relationshipForm.targetId,
                        target_id: this.editingRelationship.isSource ? this.relationshipForm.targetId : this.character.id,
                        relationship: this.relationshipForm.relationship,
                        description: this.relationshipForm.description
                    });
                } else {
                    // Create new relationship
                    this.$emit('create-relationship', {
                        source_id: this.character.id,
                        target_id: this.relationshipForm.targetId,
                        relationship: this.relationshipForm.relationship,
                        description: this.relationshipForm.description
                    });
                }
                
                this.showRelationshipModal = false;
            },
            cancelRelationshipEdit() {
                this.showRelationshipModal = false;
            },
            deleteRelationship(relationship) {
                if (confirm(`Are you sure you want to delete the relationship with ${relationship.otherCharacter.name}?`)) {
                    this.$emit('delete-relationship', relationship.id);
                }
            },
            viewScene(scene) {
                this.$emit('view-scene', scene);
            }
        }
        }
    });

    // Check if the character view container exists
    const characterViewContainer = document.getElementById('character-view-app');
    
    if (characterViewContainer) {
        // Get data attributes
        const characterData = JSON.parse(characterViewContainer.dataset.character);
        const storyData = JSON.parse(characterViewContainer.dataset.storyData);
        const showDeleteButton = characterViewContainer.dataset.showDeleteButton === 'true';
        
        // Create Vue instance for character view - Vue 3 syntax
        const app = createApp({
            data() {
                return {
                    character: characterData,
                    storyData: storyData,
                    showDeleteButton: showDeleteButton
                }
            },
            methods: {
                editCharacter(character) {
                    window.location.href = `/storycraft/character/${character.id}/edit/`;
                },
                deleteCharacter(character) {
                    if (confirm(`Are you sure you want to delete ${character.name}?`)) {
                        window.location.href = `/storycraft/character/${character.id}/delete/`;
                    }
                },
                createRelationship(relationshipData) {
                    // Submit relationship data via AJAX
                    fetch('/api/relationships/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': this.getCsrfToken()
                        },
                        body: JSON.stringify(relationshipData)
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            // Reload the page to show the new relationship
                            window.location.reload();
                        } else {
                            alert('Error creating relationship: ' + data.error);
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('An error occurred. Please try again.');
                    });
                },
                updateRelationship(relationshipData) {
                    // Submit relationship data via AJAX
                    fetch(`/api/relationships/${relationshipData.id}/update/`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': this.getCsrfToken()
                        },
                        body: JSON.stringify(relationshipData)
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            // Reload the page to show the updated relationship
                            window.location.reload();
                        } else {
                            alert('Error updating relationship: ' + data.error);
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('An error occurred. Please try again.');
                    });
                },
                deleteRelationship(relationshipId) {
                    // Submit delete request via AJAX
                    fetch(`/api/relationships/${relationshipId}/delete/`, {
                        method: 'DELETE',
                        headers: {
                            'X-CSRFToken': this.getCsrfToken()
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            // Reload the page to update the relationships
                            window.location.reload();
                        } else {
                            alert('Error deleting relationship: ' + data.error);
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('An error occurred. Please try again.');
                    });
                },
                viewScene(scene) {
                    window.location.href = `/storycraft/scene/${scene.id}/`;
                },
                getCsrfToken() {
                    // Get CSRF token from cookies
                    const name = 'csrftoken';
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
        });
        
        // Register the component globally
        app.component('character-view', characterViewComponent);
        
        // Mount the app
        app.mount('#character-view-app');
    }

    // Similar implementation for StoryGraph and StoryTimeline would go here
;