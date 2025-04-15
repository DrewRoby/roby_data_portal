// static/js/app.js

// Import Vue components
import StoryGraph from './components/StoryGraph.vue';
import StoryTimeline from './components/StoryTimeline.vue';
import CharacterView from './components/CharacterView.vue';

// Initialize Vue when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Check if the story graph container exists
    const storyGraphContainer = document.getElementById('story-graph-app');
    
    if (storyGraphContainer) {
        // Get data attributes
        const storyId = storyGraphContainer.dataset.storyId;
        const apiUrl = storyGraphContainer.dataset.apiUrl;
        
        // Create Vue instance for the network graph
        new Vue({
            el: '#story-graph-app',
            template: '<story-graph :story-id="storyId" :api-url="apiUrl"></story-graph>',
            components: {
                'story-graph': StoryGraph
            },
            data: {
                storyId: parseInt(storyId),
                apiUrl: apiUrl
            }
        });
    }
    
    // Check if the story timeline container exists
    const storyTimelineContainer = document.getElementById('story-timeline-app');
    
    if (storyTimelineContainer) {
        // Get data attributes
        const storyId = storyTimelineContainer.dataset.storyId;
        const apiUrl = storyTimelineContainer.dataset.apiUrl;
        
        // Create Vue instance for the timeline
        new Vue({
            el: '#story-timeline-app',
            template: '<story-timeline :story-id="storyId" :api-url="apiUrl"></story-timeline>',
            components: {
                'story-timeline': StoryTimeline
            },
            data: {
                storyId: parseInt(storyId),
                apiUrl: apiUrl
            }
        });
    }
    
    // Check if we have a character view container
    const characterViewContainer = document.getElementById('character-view-app');
    
    if (characterViewContainer) {
        // Get data attributes
        const characterData = JSON.parse(characterViewContainer.dataset.character);
        const storyData = JSON.parse(characterViewContainer.dataset.storyData);
        const showDeleteButton = characterViewContainer.dataset.showDeleteButton === 'true';
        
        // Create Vue instance for character view
        new Vue({
            el: '#character-view-app',
            template: `
                <character-view 
                    :character="character" 
                    :story-data="storyData"
                    :show-delete-button="showDeleteButton"
                    @edit-character="editCharacter"
                    @delete-character="deleteCharacter"
                    @create-relationship="createRelationship"
                    @update-relationship="updateRelationship"
                    @delete-relationship="deleteRelationship"
                    @view-scene="viewScene"
                ></character-view>
            `,
            components: {
                'character-view': CharacterView
            },
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
});