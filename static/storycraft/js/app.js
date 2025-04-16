// This needs to be included as a module script in your HTML
// Add type="module" to the script tag loading this file

// Import Vue if not already available globally
import Vue from 'https://cdn.jsdelivr.net/npm/vue@2.6.14/dist/vue.esm.browser.js';

// We'll define the components directly instead of importing .vue files
// which browsers can't handle natively

// Initialize Vue when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Register the character view component
    Vue.component('character-view', {
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
    });

    // Check if the character view container exists
    const characterViewContainer = document.getElementById('character-view-app');
    
    if (characterViewContainer) {
        // Get data attributes
        const characterData = JSON.parse(characterViewContainer.dataset.character);
        const storyData = JSON.parse(characterViewContainer.dataset.storyData);
        const showDeleteButton = characterViewContainer.dataset.showDeleteButton === 'true';
        
        // Create Vue instance for character view
        new Vue({
            el: '#character-view-app',
            data: {
                character: characterData,
                storyData: storyData,
                showDeleteButton: showDeleteButton
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
    }

    // Similar implementation for StoryGraph and StoryTimeline would go here
});