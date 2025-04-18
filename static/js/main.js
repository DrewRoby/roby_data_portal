/**
 * Main JavaScript file for Roby Data Services
 * This file handles global site functionality and loads app-specific modules
 */

// Import Vue if not already available globally
import { vue } from 'https://unpkg.com/vue@3.3.4/dist/vue.global.js';


document.addEventListener('DOMContentLoaded', function() {
    // Initialize the mobile navigation
    initMobileNav();
    
    // Initialize header animations
    initHeaderAnimation();
    
    // Check for app-specific initializations
    checkAppInitializations();
});

/**
 * Initialize mobile navigation functionality
 */
function initMobileNav() {
    const header = document.querySelector('header');
    const logo = document.querySelector('.logo');
    const mobileNav = document.querySelector('.mobile-nav');
    const closeBtn = document.querySelector('.close-btn');
    
    // Get authentication status from data attribute
    const isAuthenticated = document.body.dataset.authenticated === 'true';
    
    // Function to toggle the side menu
    function toggleMenu(e) {
        // If user is not authenticated, redirect to login page
        if (!isAuthenticated) {
            // Don't prevent default - let the link navigate normally
            return;
        }
        
        // For authenticated users, toggle the menu
        e.preventDefault();
        
        // Toggle the sidebar menu
        if (mobileNav) {
            mobileNav.classList.toggle('active');
        }
        
        // Toggle header gradient
        if (header) {
            header.classList.toggle('menu-active');
        }
    }
    
    // Toggle sidebar when logo is clicked
    if (logo) {
        logo.addEventListener('click', toggleMenu);
    }
    
    // Close mobile navigation when close button is clicked
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            if (mobileNav) {
                mobileNav.classList.remove('active');
            }
            if (header) {
                header.classList.remove('menu-active');
            }
        });
    }
    
    // Close mobile navigation when clicking outside
    document.addEventListener('click', function(e) {
        if (mobileNav && 
            mobileNav.classList.contains('active') && 
            !mobileNav.contains(e.target) && 
            (!logo || !logo.contains(e.target))) {
            
            mobileNav.classList.remove('active');
            if (header) {
                header.classList.remove('menu-active');
            }
        }
    });
}

/**
 * Initialize header animation effect
 */
function initHeaderAnimation() {
    const header = document.querySelector('header');
    
    if (header) {
        // Add scroll listener for header effects
        window.addEventListener('scroll', function() {
            if (window.scrollY > 50) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }
        });
    }
}

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