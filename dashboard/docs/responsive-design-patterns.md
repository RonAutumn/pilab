# CinePi Dashboard - Responsive Design Patterns

## Overview
This document outlines the responsive design patterns, CSS architecture, and best practices used in the CinePi Dashboard to ensure consistent, accessible, and touch-optimized user experiences across all devices.

## CSS Architecture

### Mobile-First Approach
The dashboard uses a mobile-first CSS architecture with progressive enhancement:

```css
/* Base styles (mobile) */
.component {
    /* Mobile-first styles */
}

/* Tablet and up */
@media (min-width: 768px) {
    .component {
        /* Tablet enhancements */
    }
}

/* Desktop and up */
@media (min-width: 1024px) {
    .component {
        /* Desktop enhancements */
    }
}
```

### CSS File Structure
```
dashboard/static/css/
├── mobile-first.css          # Base styles and variables
├── mobile-components.css     # Touch-friendly components
├── mobile-navigation.css     # Navigation and layout
├── orientation-optimization.css # Device-specific optimizations
├── touch-gestures.css        # Touch feedback and gestures
└── accessibility.css         # Accessibility and standards
```

## Design System

### CSS Custom Properties (Variables)
```css
:root {
    /* Colors */
    --primary-color: #00d4ff;
    --secondary-color: #ff6b35;
    --success-color: #28a745;
    --danger-color: #dc3545;
    --warning-color: #ffc107;
    
    /* Backgrounds */
    --dark-bg: #1a1a1a;
    --darker-bg: #0f0f0f;
    --card-bg: #2a2a2a;
    
    /* Text */
    --text-primary: #ffffff;
    --text-secondary: #b0b0b0;
    
    /* Spacing */
    --spacing-xs: 0.25rem;
    --spacing-sm: 0.5rem;
    --spacing-md: 1rem;
    --spacing-lg: 1.5rem;
    --spacing-xl: 2rem;
    --spacing-2xl: 3rem;
    
    /* Touch Targets */
    --touch-target: 48px;
    --touch-spacing: 8px;
    
    /* Breakpoints */
    --breakpoint-sm: 576px;
    --breakpoint-md: 768px;
    --breakpoint-lg: 992px;
    --breakpoint-xl: 1200px;
    --breakpoint-2xl: 1400px;
}
```

## Responsive Patterns

### 1. Container Pattern
```css
.container {
    width: 100%;
    padding: var(--spacing-md);
    margin: 0 auto;
    max-width: 100%;
}

@media (min-width: 576px) {
    .container {
        max-width: 540px;
    }
}

@media (min-width: 768px) {
    .container {
        max-width: 720px;
    }
}

@media (min-width: 992px) {
    .container {
        max-width: 960px;
    }
}

@media (min-width: 1200px) {
    .container {
        max-width: 1140px;
    }
}
```

### 2. Grid Pattern
```css
.status-grid {
    display: grid;
    gap: var(--spacing-md);
    grid-template-columns: 1fr;
}

@media (min-width: 768px) {
    .status-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (min-width: 992px) {
    .status-grid {
        grid-template-columns: repeat(3, 1fr);
    }
}

@media (min-width: 1200px) {
    .status-grid {
        grid-template-columns: repeat(4, 1fr);
    }
}
```

### 3. Flexbox Pattern
```css
.button-group {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
}

@media (min-width: 768px) {
    .button-group {
        flex-direction: row;
        gap: var(--spacing-md);
    }
}
```

### 4. Form Pattern
```css
.form-row {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
}

@media (min-width: 768px) {
    .form-row {
        flex-direction: row;
    }
    
    .form-row > * {
        flex: 1;
    }
}
```

## Touch-Optimized Patterns

### 1. Touch Target Pattern
```css
.button,
.nav-item,
.quick-action,
.form-control {
    min-height: var(--touch-target);
    min-width: var(--touch-target);
    padding: var(--spacing-sm) var(--spacing-md);
}
```

### 2. Touch Feedback Pattern
```css
.button:active,
.nav-item:active,
.quick-action:active {
    transform: scale(0.98);
    transition: transform 0.1s ease;
}

.touch-feedback {
    position: absolute;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.3);
    pointer-events: none;
    animation: touchRipple 0.6s ease-out;
}
```

### 3. Slider Pattern
```css
.slider {
    -webkit-appearance: none;
    appearance: none;
    height: var(--touch-target);
    background: var(--darker-bg);
    border-radius: var(--touch-target);
    outline: none;
}

.slider::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: var(--touch-target);
    height: var(--touch-target);
    border-radius: 50%;
    background: var(--primary-color);
    cursor: pointer;
}
```

## Navigation Patterns

### 1. Mobile Navigation Pattern
```css
.mobile-nav {
    position: fixed;
    top: 0;
    left: -100%;
    width: 280px;
    height: 100vh;
    background: var(--card-bg);
    transition: left 0.3s ease;
    z-index: 1000;
}

.mobile-nav.active {
    left: 0;
}

@media (min-width: 768px) {
    .mobile-nav {
        display: none;
    }
}
```

### 2. Quick Actions Pattern
```css
.quick-actions {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: var(--card-bg);
    border-top: 1px solid var(--border-color);
    display: flex;
    justify-content: space-around;
    padding: var(--spacing-sm);
    z-index: 100;
}

@media (min-width: 768px) {
    .quick-actions {
        display: none;
    }
}
```

## Accessibility Patterns

### 1. Focus Management Pattern
```css
*:focus {
    outline: 3px solid var(--primary-color);
    outline-offset: 2px;
}

*:focus:not(:focus-visible) {
    outline: none;
}

*:focus-visible {
    outline: 3px solid var(--primary-color);
    outline-offset: 2px;
}
```

### 2. Screen Reader Pattern
```css
.sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
}
```

### 3. ARIA Live Pattern
```css
[aria-live="polite"] {
    position: absolute;
    left: -10000px;
    width: 1px;
    height: 1px;
    overflow: hidden;
}
```

## Performance Patterns

### 1. Reduced Motion Pattern
```css
@media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
        scroll-behavior: auto !important;
    }
}
```

### 2. High DPI Pattern
```css
@media (-webkit-min-device-pixel-ratio: 2), (min-resolution: 192dpi) {
    .icon {
        background-image: url('icon@2x.png');
        background-size: contain;
    }
}
```

## Device-Specific Patterns

### 1. Raspberry Pi 5 Pattern
```css
/* Specific resolutions for Pi 5 touchscreen */
@media (width: 800px) and (height: 480px) {
    .container {
        padding: var(--spacing-sm);
    }
    
    .button {
        min-height: 56px;
        font-size: 1.1rem;
    }
}

@media (width: 1024px) and (height: 768px) {
    .status-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (width: 1280px) and (height: 720px) {
    .status-grid {
        grid-template-columns: repeat(3, 1fr);
    }
}
```

### 2. Touch Device Pattern
```css
@media (hover: none) and (pointer: coarse) {
    .button:hover {
        /* Remove hover effects on touch devices */
    }
    
    .button:active {
        /* Add active states for touch feedback */
    }
}
```

### 3. Orientation Pattern
```css
@media (orientation: portrait) {
    .editor-main {
        flex-direction: column;
    }
    
    .editor-sidebar {
        width: 100%;
        height: 200px;
    }
}

@media (orientation: landscape) {
    .editor-main {
        flex-direction: row;
    }
    
    .editor-sidebar {
        width: 300px;
        height: 100%;
    }
}
```

## Component Patterns

### 1. Card Pattern
```css
.status-card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: var(--spacing-lg);
    box-shadow: var(--shadow);
    transition: box-shadow 0.3s ease;
}

.status-card:hover {
    box-shadow: var(--shadow-hover);
}
```

### 2. Button Pattern
```css
.button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-sm) var(--spacing-md);
    background: var(--primary-color);
    color: #ffffff;
    border: 2px solid var(--primary-color);
    border-radius: 8px;
    font-weight: 600;
    text-decoration: none;
    cursor: pointer;
    transition: all 0.3s ease;
    min-height: var(--touch-target);
}

.button:hover,
.button:focus {
    background: #ffffff;
    color: var(--primary-color);
    border-color: #ffffff;
}
```

### 3. Form Control Pattern
```css
.form-control {
    width: 100%;
    padding: var(--spacing-sm) var(--spacing-md);
    background: var(--darker-bg);
    color: var(--text-primary);
    border: 2px solid var(--border-color);
    border-radius: 6px;
    font-size: 1rem;
    transition: border-color 0.3s ease;
    min-height: var(--touch-target);
}

.form-control:focus {
    border-color: var(--primary-color);
    background: var(--dark-bg);
    outline: none;
}
```

## Best Practices

### 1. Mobile-First Development
- Start with mobile styles as the base
- Use `min-width` media queries for progressive enhancement
- Test on real mobile devices frequently

### 2. Touch Optimization
- Ensure all interactive elements are at least 48x48px
- Provide immediate visual feedback for touch interactions
- Disable hover effects on touch devices

### 3. Performance
- Use CSS transforms and opacity for animations
- Minimize layout thrashing
- Optimize for 60fps animations

### 4. Accessibility
- Maintain proper color contrast ratios
- Ensure keyboard navigation works
- Provide screen reader support
- Test with accessibility tools

### 5. Cross-Browser Compatibility
- Test on multiple browsers
- Use vendor prefixes where necessary
- Provide fallbacks for older browsers

## Testing Guidelines

### 1. Device Testing
- Test on actual devices, not just emulators
- Test in different orientations
- Test with different screen densities

### 2. Performance Testing
- Use browser developer tools
- Monitor frame rates
- Check for layout thrashing

### 3. Accessibility Testing
- Use screen readers
- Test keyboard navigation
- Verify color contrast

### 4. User Testing
- Test with real users
- Gather feedback on usability
- Iterate based on findings

## Maintenance

### 1. Code Organization
- Keep CSS files modular
- Use consistent naming conventions
- Document complex patterns

### 2. Version Control
- Commit changes frequently
- Use descriptive commit messages
- Tag releases appropriately

### 3. Documentation
- Keep patterns up to date
- Document new components
- Maintain testing guides

This responsive design system ensures the CinePi Dashboard provides an excellent user experience across all devices while maintaining accessibility, performance, and usability standards. 