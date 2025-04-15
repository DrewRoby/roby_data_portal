// storycraft/static/storycraft/js/app.js

// Import the StoryGraph component
import StoryGraph from './components/StoryGraph.vue';

// Initialize Vue when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Check if the story graph container exists
    const storyGraphContainer = document.getElementById('story-graph-app');
    
    if (storyGraphContainer) {
        // Get data attributes
        const storyId = storyGraphContainer.dataset.storyId;
        const apiUrl = storyGraphContainer.dataset.apiUrl;
        
        // Create Vue instance
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
});