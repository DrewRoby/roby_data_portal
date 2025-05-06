/**
 * Main JavaScript file for Roby Data Services
 * This file handles global site functionality and loads app-specific modules
 */

// Import Vue if not already available globally
import { Vue } from 'https://unpkg.com/vue@3.3.4/dist/vue.global.js';


document.addEventListener('DOMContentLoaded', function() {
    // Check for app-specific initializations
    checkAppInitializations();
});

/**
 * Check if any app-specific modules need to be initialized
 * This serves as a bridge between the main.js and app-specific JS files
 */
function checkAppInitializations() {
    // Check if we're on a Storycraft page
    if (document.querySelector('[data-app="storycraft"]')) {
        console.log('Storycraft app detected');
        // The storycraft/js/app.js module will handle initialization via type="module"
    }
    
    // Check for other apps
    if (document.querySelector('[data-app="schemascope"]')) {
        console.log('Schemascope app detected');
        // Initialize Schemascope-specific functionality if needed
    }
    
    if (document.querySelector('[data-app="todo"]')) {
        console.log('Todo app detected');
        // Initialize Todo-specific functionality if needed
    }
}