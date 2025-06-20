/**
 * Character Motivation Handler for Scene Forms
 * Handles dynamic creation and management of character motivation fields
 * Works with both create and edit scene forms
 */

class CharacterMotivationHandler {
    constructor(options = {}) {
        // Configuration options
        this.characterSelectId = options.characterSelectId || null;
        this.motivationsContainerId = options.motivationsContainerId || 'character-motivations-container';
        this.motivationSectionId = options.motivationSectionId || 'character-motivation-section';
        this.existingMotivations = options.existingMotivations || {};
        this.colorChoices = options.colorChoices || ['#FFD3B6', '#A8E6CF', '#DCEDC2', '#FFD3B4', '#FF8C94'];
        
        // DOM elements
        this.characterSelect = null;
        this.motivationsContainer = null;
        this.motivationSection = null;
        
        // Initialize when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }
    
    init() {
        // Find DOM elements
        this.characterSelect = document.getElementById(this.characterSelectId);
        this.motivationsContainer = document.getElementById(this.motivationsContainerId);
        this.motivationSection = document.getElementById(this.motivationSectionId);
        
        // Validate required elements exist
        if (!this.characterSelect) {
            console.error(`Character select element not found: ${this.characterSelectId}`);
            return;
        }
        
        if (!this.motivationsContainer) {
            console.error(`Motivations container not found: ${this.motivationsContainerId}`);
            return;
        }
        
        if (!this.motivationSection) {
            console.error(`Motivation section not found: ${this.motivationSectionId}`);
            return;
        }
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Initialize fields on page load
        this.updateMotivationFields();
    }
    
    setupEventListeners() {
        // Handle both select multiple and checkbox changes
        if (this.characterSelect.tagName.toLowerCase() === 'select') {
            // Multiple select dropdown
            this.characterSelect.addEventListener('change', () => this.updateMotivationFields());
        } else {
            // Individual checkboxes (for alternative implementations)
            const checkboxes = this.characterSelect.querySelectorAll('input[type="checkbox"]');
            checkboxes.forEach(checkbox => {
                checkbox.addEventListener('change', () => this.updateMotivationFields());
            });
        }
    }
    
    createMotivationFields(characterId, characterName) {
        // Get existing motivation data if available
        const motivation = this.existingMotivations[characterId] || { 
            desire: '', 
            obstacle: '', 
            action: '' 
        };
        
        // Choose a random color for the character avatar
        const colorIndex = Math.floor(Math.random() * this.colorChoices.length);
        const backgroundColor = this.colorChoices[colorIndex];
        
        // Create container element
        const container = document.createElement('div');
        container.className = 'character-motivation-container';
        container.id = `motivation-${characterId}`;
        container.style.display = 'block';
        
        // Build the HTML content
        container.innerHTML = `
            <div class="character-motivation-header">
                <div class="character-avatar" style="background-color: ${backgroundColor}">
                    <span>${characterName.charAt(0)}</span>
                </div>
                <h4>${characterName}</h4>
            </div>
            <div class="motivation-fields">
                <div class="motivation-field">
                    <label for="desire_${characterId}">What do they want? (Desire)</label>
                    <textarea name="desire_${characterId}" id="desire_${characterId}" rows="3" 
                              placeholder="What does the character want?">${motivation.desire}</textarea>
                </div>
                <div class="motivation-field">
                    <label for="obstacle_${characterId}">Why can't they have it? (Obstacle)</label>
                    <textarea name="obstacle_${characterId}" id="obstacle_${characterId}" rows="3" 
                              placeholder="Why can't they have it?">${motivation.obstacle}</textarea>
                </div>
                <div class="motivation-field">
                    <label for="action_${characterId}">What do they do about it? (Action)</label>
                    <textarea name="action_${characterId}" id="action_${characterId}" rows="3" 
                              placeholder="What do they do about it?">${motivation.action}</textarea>
                </div>
            </div>
        `;
        
        return container;
    }
    
    getSelectedCharacters() {
        const selected = [];
        
        if (this.characterSelect.tagName.toLowerCase() === 'select') {
            // Multiple select dropdown
            const selectedOptions = Array.from(this.characterSelect.selectedOptions);
            selectedOptions.forEach(option => {
                selected.push({
                    id: option.value,
                    name: option.text
                });
            });
        } else {
            // Individual checkboxes (for alternative implementations)
            const checkboxes = this.characterSelect.querySelectorAll('input[type="checkbox"]:checked');
            checkboxes.forEach(checkbox => {
                selected.push({
                    id: checkbox.value,
                    name: checkbox.nextElementSibling.textContent.trim()
                });
            });
        }
        
        return selected;
    }
    
    updateMotivationFields() {
        // Clear the container
        this.motivationsContainer.innerHTML = '';
        
        // Get selected characters
        const selectedCharacters = this.getSelectedCharacters();
        
        // Add fields for each selected character
        selectedCharacters.forEach(character => {
            const motivationFields = this.createMotivationFields(character.id, character.name);
            this.motivationsContainer.appendChild(motivationFields);
        });
        
        // Show/hide the motivation section based on whether any characters are selected
        if (selectedCharacters.length > 0) {
            this.motivationSection.style.display = 'block';
        } else {
            this.motivationSection.style.display = 'none';
        }
    }
    
    // Public method to add existing motivations (useful for edit forms)
    setExistingMotivations(motivations) {
        this.existingMotivations = motivations;
        this.updateMotivationFields();
    }
    
    // Public method to get current motivation data from form
    getMotivationData() {
        const data = {};
        const selectedCharacters = this.getSelectedCharacters();
        
        selectedCharacters.forEach(character => {
            const desireField = document.getElementById(`desire_${character.id}`);
            const obstacleField = document.getElementById(`obstacle_${character.id}`);
            const actionField = document.getElementById(`action_${character.id}`);
            
            if (desireField && obstacleField && actionField) {
                data[character.id] = {
                    desire: desireField.value,
                    obstacle: obstacleField.value,
                    action: actionField.value
                };
            }
        });
        
        return data;
    }
}

// Factory function for easy initialization
function initCharacterMotivations(options) {
    return new CharacterMotivationHandler(options);
}

// Auto-initialize if config is provided via window object
document.addEventListener('DOMContentLoaded', function() {
    if (window.characterMotivationConfig) {
        window.characterMotivationHandler = new CharacterMotivationHandler(window.characterMotivationConfig);
    }
});

// Export for use in other contexts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CharacterMotivationHandler, initCharacterMotivations };
}