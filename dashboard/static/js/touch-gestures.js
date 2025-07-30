/**
 * CinePi Dashboard - Touch Gesture Support
 * Implements touch-friendly interactions for mobile and tablet devices
 */

class TouchGestureManager {
    constructor() {
        this.touchStartX = 0;
        this.touchStartY = 0;
        this.touchEndX = 0;
        this.touchEndY = 0;
        this.touchStartTime = 0;
        this.touchEndTime = 0;
        this.isTouchDevice = this.detectTouchDevice();
        this.gestureThreshold = 50; // Minimum distance for swipe
        this.tapThreshold = 300; // Maximum time for tap (ms)
        this.longPressThreshold = 500; // Time for long press (ms)
        this.longPressTimer = null;
        this.activeGestures = new Set();
        
        this.init();
    }
    
    /**
     * Detect if device supports touch
     */
    detectTouchDevice() {
        return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    }
    
    /**
     * Initialize touch gesture support
     */
    init() {
        if (!this.isTouchDevice) {
            return;
        }
        
        this.setupTouchEvents();
        this.setupScrollOptimization();
        this.setupZoomSupport();
        this.setupHapticFeedback();
        this.setupGestureIndicators();
    }
    
    /**
     * Setup touch event listeners
     */
    setupTouchEvents() {
        // Global touch events for navigation
        document.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: false });
        document.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: false });
        document.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
        
        // Prevent zoom on double tap
        document.addEventListener('touchend', this.preventDoubleTapZoom.bind(this), { passive: false });
        
        // Setup specific gesture areas
        this.setupSwipeGestures();
        this.setupTapGestures();
        this.setupLongPressGestures();
    }
    
    /**
     * Handle touch start events
     */
    handleTouchStart(event) {
        const touch = event.touches[0];
        this.touchStartX = touch.clientX;
        this.touchStartY = touch.clientY;
        this.touchStartTime = Date.now();
        
        // Start long press timer
        this.longPressTimer = setTimeout(() => {
            this.handleLongPress(event);
        }, this.longPressThreshold);
        
        // Add touch feedback
        this.addTouchFeedback(touch.target);
    }
    
    /**
     * Handle touch end events
     */
    handleTouchEnd(event) {
        const touch = event.changedTouches[0];
        this.touchEndX = touch.clientX;
        this.touchEndY = touch.clientY;
        this.touchEndTime = Date.now();
        
        // Clear long press timer
        if (this.longPressTimer) {
            clearTimeout(this.longPressTimer);
            this.longPressTimer = null;
        }
        
        // Calculate gesture
        const duration = this.touchEndTime - this.touchStartTime;
        const distanceX = this.touchEndX - this.touchStartX;
        const distanceY = this.touchEndY - this.touchStartY;
        const distance = Math.sqrt(distanceX * distanceX + distanceY * distanceY);
        
        // Determine gesture type
        if (distance < this.gestureThreshold && duration < this.tapThreshold) {
            this.handleTap(event);
        } else if (distance > this.gestureThreshold) {
            this.handleSwipe(event, distanceX, distanceY, distance);
        }
        
        // Remove touch feedback
        this.removeTouchFeedback(touch.target);
    }
    
    /**
     * Handle touch move events
     */
    handleTouchMove(event) {
        // Cancel long press if user moves finger
        if (this.longPressTimer) {
            clearTimeout(this.longPressTimer);
            this.longPressTimer = null;
        }
        
        // Prevent default scroll on certain elements
        const target = event.target;
        if (target.closest('.slider') || target.closest('.toggle-switch')) {
            event.preventDefault();
        }
    }
    
    /**
     * Handle tap gestures
     */
    handleTap(event) {
        const target = event.target;
        
        // Handle different tap targets
        if (target.closest('.button')) {
            this.handleButtonTap(target.closest('.button'));
        } else if (target.closest('.nav-item')) {
            this.handleNavigationTap(target.closest('.nav-item'));
        } else if (target.closest('.quick-action')) {
            this.handleQuickActionTap(target.closest('.quick-action'));
        } else if (target.closest('.status-card')) {
            this.handleStatusCardTap(target.closest('.status-card'));
        }
        
        // Provide haptic feedback
        this.triggerHapticFeedback('light');
    }
    
    /**
     * Handle swipe gestures
     */
    handleSwipe(event, distanceX, distanceY, distance) {
        const target = event.target;
        const absX = Math.abs(distanceX);
        const absY = Math.abs(distanceY);
        
        // Determine swipe direction
        if (absX > absY) {
            // Horizontal swipe
            if (distanceX > this.gestureThreshold) {
                this.handleSwipeRight(event);
            } else if (distanceX < -this.gestureThreshold) {
                this.handleSwipeLeft(event);
            }
        } else {
            // Vertical swipe
            if (distanceY > this.gestureThreshold) {
                this.handleSwipeDown(event);
            } else if (distanceY < -this.gestureThreshold) {
                this.handleSwipeUp(event);
            }
        }
        
        // Provide haptic feedback
        this.triggerHapticFeedback('medium');
    }
    
    /**
     * Handle long press gestures
     */
    handleLongPress(event) {
        const target = event.target;
        
        if (target.closest('.button')) {
            this.handleButtonLongPress(target.closest('.button'));
        } else if (target.closest('.status-card')) {
            this.handleStatusCardLongPress(target.closest('.status-card'));
        }
        
        // Provide haptic feedback
        this.triggerHapticFeedback('heavy');
    }
    
    /**
     * Setup swipe gestures for specific areas
     */
    setupSwipeGestures() {
        // Navigation swipe from left edge
        document.addEventListener('touchstart', (e) => {
            if (e.touches[0].clientX < 50) {
                this.activeGestures.add('edge-swipe');
            }
        });
        
        // Status card swipe gestures
        document.querySelectorAll('.status-card').forEach(card => {
            card.addEventListener('touchstart', this.handleCardTouchStart.bind(this));
            card.addEventListener('touchend', this.handleCardTouchEnd.bind(this));
        });
        
        // Slider swipe gestures
        document.querySelectorAll('.slider').forEach(slider => {
            slider.addEventListener('touchstart', this.handleSliderTouchStart.bind(this));
            slider.addEventListener('touchmove', this.handleSliderTouchMove.bind(this));
        });
    }
    
    /**
     * Setup tap gestures
     */
    setupTapGestures() {
        // Double tap to zoom prevention
        document.addEventListener('touchend', (e) => {
            const target = e.target;
            if (target.closest('.stream-container') || target.closest('.stream-placeholder')) {
                e.preventDefault();
            }
        });
        
        // Tap to focus for form controls
        document.querySelectorAll('.form-control').forEach(control => {
            control.addEventListener('touchstart', this.handleFormControlTap.bind(this));
        });
    }
    
    /**
     * Setup long press gestures
     */
    setupLongPressGestures() {
        // Long press for context menus
        document.querySelectorAll('.status-card, .capture-item').forEach(item => {
            item.addEventListener('contextmenu', (e) => {
                e.preventDefault();
                this.showContextMenu(e);
            });
        });
    }
    
    /**
     * Handle button tap with feedback
     */
    handleButtonTap(button) {
        // Add visual feedback
        button.classList.add('touch-active');
        setTimeout(() => {
            button.classList.remove('touch-active');
        }, 150);
        
        // Trigger haptic feedback
        this.triggerHapticFeedback('light');
    }
    
    /**
     * Handle button long press
     */
    handleButtonLongPress(button) {
        // Show button options or help
        this.showButtonHelp(button);
    }
    
    /**
     * Handle navigation tap
     */
    handleNavigationTap(navItem) {
        // Smooth scroll to section
        const section = navItem.getAttribute('data-section');
        const targetElement = document.getElementById(section);
        
        if (targetElement) {
            targetElement.scrollIntoView({ 
                behavior: 'smooth',
                block: 'start'
            });
        }
        
        // Close mobile nav if open
        if (window.innerWidth <= 767) {
            closeMobileNav();
        }
    }
    
    /**
     * Handle quick action tap
     */
    handleQuickActionTap(quickAction) {
        // Same as navigation tap
        this.handleNavigationTap(quickAction);
    }
    
    /**
     * Handle status card tap
     */
    handleStatusCardTap(card) {
        // Expand/collapse card details
        card.classList.toggle('expanded');
        
        // Show more details
        this.showCardDetails(card);
    }
    
    /**
     * Handle status card long press
     */
    handleStatusCardLongPress(card) {
        // Show card options menu
        this.showCardOptions(card);
    }
    
    /**
     * Handle swipe right (open navigation)
     */
    handleSwipeRight(event) {
        if (this.activeGestures.has('edge-swipe')) {
            openMobileNav();
            this.activeGestures.delete('edge-swipe');
        }
    }
    
    /**
     * Handle swipe left (close navigation)
     */
    handleSwipeLeft(event) {
        if (document.getElementById('mobileNav').classList.contains('active')) {
            closeMobileNav();
        }
    }
    
    /**
     * Handle swipe up (scroll up)
     */
    handleSwipeUp(event) {
        window.scrollBy({
            top: -100,
            behavior: 'smooth'
        });
    }
    
    /**
     * Handle swipe down (scroll down)
     */
    handleSwipeDown(event) {
        window.scrollBy({
            top: 100,
            behavior: 'smooth'
        });
    }
    
    /**
     * Handle card touch start
     */
    handleCardTouchStart(event) {
        const card = event.currentTarget;
        card.classList.add('touch-active');
    }
    
    /**
     * Handle card touch end
     */
    handleCardTouchEnd(event) {
        const card = event.currentTarget;
        card.classList.remove('touch-active');
    }
    
    /**
     * Handle slider touch start
     */
    handleSliderTouchStart(event) {
        const slider = event.currentTarget;
        slider.classList.add('slider-active');
    }
    
    /**
     * Handle slider touch move
     */
    handleSliderTouchMove(event) {
        const slider = event.currentTarget;
        const touch = event.touches[0];
        const rect = slider.getBoundingClientRect();
        const percent = (touch.clientX - rect.left) / rect.width;
        
        // Update slider value
        const min = parseFloat(slider.min);
        const max = parseFloat(slider.max);
        const value = min + (max - min) * Math.max(0, Math.min(1, percent));
        
        slider.value = value;
        slider.dispatchEvent(new Event('input', { bubbles: true }));
    }
    
    /**
     * Handle form control tap
     */
    handleFormControlTap(event) {
        const control = event.currentTarget;
        
        // Add focus with delay for better UX
        setTimeout(() => {
            control.focus();
        }, 100);
    }
    
    /**
     * Setup scroll optimization
     */
    setupScrollOptimization() {
        // Smooth scrolling for touch devices
        document.documentElement.style.scrollBehavior = 'smooth';
        
        // Optimize scroll performance
        document.addEventListener('scroll', this.throttle(() => {
            // Update scroll indicators
            this.updateScrollIndicators();
        }, 16), { passive: true });
    }
    
    /**
     * Setup zoom support
     */
    setupZoomSupport() {
        // Prevent zoom on double tap
        document.addEventListener('touchend', (e) => {
            const target = e.target;
            if (target.closest('.stream-container') || target.closest('.stream-placeholder')) {
                e.preventDefault();
            }
        });
        
        // Allow pinch to zoom on images
        document.querySelectorAll('img').forEach(img => {
            img.addEventListener('gesturestart', (e) => e.preventDefault());
            img.addEventListener('gesturechange', (e) => e.preventDefault());
            img.addEventListener('gestureend', (e) => e.preventDefault());
        });
    }
    
    /**
     * Setup haptic feedback
     */
    setupHapticFeedback() {
        // Check if device supports haptic feedback
        if ('vibrate' in navigator) {
            this.hapticSupported = true;
        }
    }
    
    /**
     * Setup gesture indicators
     */
    setupGestureIndicators() {
        // Add gesture hint elements
        this.addGestureHints();
    }
    
    /**
     * Add touch feedback
     */
    addTouchFeedback(element) {
        element.classList.add('touch-feedback');
    }
    
    /**
     * Remove touch feedback
     */
    removeTouchFeedback(element) {
        element.classList.remove('touch-feedback');
    }
    
    /**
     * Trigger haptic feedback
     */
    triggerHapticFeedback(type) {
        if (!this.hapticSupported) return;
        
        const patterns = {
            light: [10],
            medium: [20],
            heavy: [30]
        };
        
        navigator.vibrate(patterns[type] || patterns.light);
    }
    
    /**
     * Prevent double tap zoom
     */
    preventDoubleTapZoom(event) {
        const target = event.target;
        if (target.closest('.button') || target.closest('.nav-item') || target.closest('.quick-action')) {
            event.preventDefault();
        }
    }
    
    /**
     * Show context menu
     */
    showContextMenu(event) {
        const target = event.target.closest('.status-card, .capture-item');
        if (!target) return;
        
        // Create context menu
        const menu = this.createContextMenu(target);
        document.body.appendChild(menu);
        
        // Position menu
        menu.style.left = event.clientX + 'px';
        menu.style.top = event.clientY + 'px';
        
        // Remove menu on outside click
        setTimeout(() => {
            document.addEventListener('click', () => {
                menu.remove();
            }, { once: true });
        }, 100);
    }
    
    /**
     * Create context menu
     */
    createContextMenu(target) {
        const menu = document.createElement('div');
        menu.className = 'context-menu';
        menu.innerHTML = `
            <div class="context-menu-item" data-action="refresh">Refresh</div>
            <div class="context-menu-item" data-action="details">Details</div>
            <div class="context-menu-item" data-action="settings">Settings</div>
        `;
        
        menu.addEventListener('click', (e) => {
            const action = e.target.getAttribute('data-action');
            this.handleContextMenuAction(action, target);
            menu.remove();
        });
        
        return menu;
    }
    
    /**
     * Handle context menu action
     */
    handleContextMenuAction(action, target) {
        switch (action) {
            case 'refresh':
                this.refreshElement(target);
                break;
            case 'details':
                this.showElementDetails(target);
                break;
            case 'settings':
                this.showElementSettings(target);
                break;
        }
    }
    
    /**
     * Show button help
     */
    showButtonHelp(button) {
        const tooltip = document.createElement('div');
        tooltip.className = 'button-help-tooltip';
        tooltip.textContent = button.getAttribute('title') || 'Button help';
        
        document.body.appendChild(tooltip);
        
        const rect = button.getBoundingClientRect();
        tooltip.style.left = rect.left + 'px';
        tooltip.style.top = (rect.bottom + 10) + 'px';
        
        setTimeout(() => tooltip.remove(), 2000);
    }
    
    /**
     * Show card details
     */
    showCardDetails(card) {
        // Implementation for showing card details
        console.log('Show card details:', card);
    }
    
    /**
     * Show card options
     */
    showCardOptions(card) {
        // Implementation for showing card options
        console.log('Show card options:', card);
    }
    
    /**
     * Update scroll indicators
     */
    updateScrollIndicators() {
        const scrollTop = window.pageYOffset;
        const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
        const scrollPercent = (scrollTop / scrollHeight) * 100;
        
        // Update scroll progress indicator
        const indicator = document.querySelector('.scroll-indicator');
        if (indicator) {
            indicator.style.width = scrollPercent + '%';
        }
    }
    
    /**
     * Add gesture hints
     */
    addGestureHints() {
        // Add swipe hints for first-time users
        if (!localStorage.getItem('gesture-hints-shown')) {
            this.showGestureHints();
            localStorage.setItem('gesture-hints-shown', 'true');
        }
    }
    
    /**
     * Show gesture hints
     */
    showGestureHints() {
        const hints = document.createElement('div');
        hints.className = 'gesture-hints';
        hints.innerHTML = `
            <div class="gesture-hint">
                <div class="gesture-icon">👆</div>
                <div class="gesture-text">Tap to interact</div>
            </div>
            <div class="gesture-hint">
                <div class="gesture-icon">👈</div>
                <div class="gesture-text">Swipe from left edge to open menu</div>
            </div>
            <div class="gesture-hint">
                <div class="gesture-icon">👆</div>
                <div class="gesture-text">Long press for more options</div>
            </div>
        `;
        
        document.body.appendChild(hints);
        
        setTimeout(() => {
            hints.remove();
        }, 5000);
    }
    
    /**
     * Utility function to throttle events
     */
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
    
    /**
     * Refresh element
     */
    refreshElement(element) {
        // Implementation for refreshing element
        console.log('Refresh element:', element);
    }
    
    /**
     * Show element details
     */
    showElementDetails(element) {
        // Implementation for showing element details
        console.log('Show element details:', element);
    }
    
    /**
     * Show element settings
     */
    showElementSettings(element) {
        // Implementation for showing element settings
        console.log('Show element settings:', element);
    }
}

// Initialize touch gesture manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.touchGestures = new TouchGestureManager();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TouchGestureManager;
} 