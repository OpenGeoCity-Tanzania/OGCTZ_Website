# Interactive Effects & Animations Documentation

## Overview
This website includes comprehensive modern interactive effects used by top websites like Netflix, Airbnb, Stripe, etc.

## Available Effects

### 1. **Scroll-Triggered Animations**
Elements automatically animate when they come into view while scrolling.

**Usage:**
```html
<!-- Element will fade in and slide up when scrolled into view -->
<div data-scroll-animate>Your content</div>

<!-- Or use regular elements - they animate automatically -->
<h2>Heading</h2>
<p>Paragraph</p>
```

### 2. **Theme Toggle**
Switch between light and dark mode with automatic system detection.

**Features:**
- Sun/Moon icon button in navigation
- Saves preference to localStorage
- Favicon changes with theme
- Automatic system preference detection
- Smooth color transitions (300ms)

### 3. **Smooth Scrolling**
All anchor links smoothly scroll to their targets.

**Usage:**
```html
<a href="#section">Jump to section</a>
<div id="section">Section content</div>
```

### 4. **Button Effects**
Buttons have ripple effects and lift animations.

**Features:**
- Ripple effect on click
- Lift animation on hover (translateY -2px)
- Smooth transitions

### 5. **Card Hover Effects**
Cards scale, lift, and enhance shadows on hover.

**Features:**
- Scale: 1.01x
- Lift: -5px translateY
- Shadow enhancement
- Smooth cubic-bezier easing

**Usage:**
```html
<div data-card>
  Card content
</div>

<!-- Or use any of these classes -->
<div class="card">Card content</div>
<article>Article content</article>
```

### 6. **Parallax Effect**
Background elements move slower than foreground on scroll.

**Usage:**
```html
<div data-parallax="0.5">
  This moves at 50% of scroll speed
</div>
<div data-parallax="0.3">
  This moves at 30% of scroll speed
</div>
```

### 7. **Scroll Progress Bar**
Shows reading progress at the top of the page.

**Features:**
- Gradient from sky-blue to emerald
- 3px height
- Automatically updates on scroll

### 8. **Cursor Glow Effect**
Custom cursor glow follows mouse movement.

**Features:**
- Cyan glow circle
- Smooth tracking with easing
- Mix-blend-mode for glow effect

---

## Animation Classes

Add these classes to any element for instant animations:

### Fade Animations
- `.animate-fade-in` - Basic fade in (0.6s)
- `.animate-fade-in-up` - Fade in with slide up (0.8s)

### Slide Animations
- `.animate-slide-in-down` - Slide down (0.5s)
- `.animate-slide-in-up` - Slide up (0.5s)
- `.animate-slide-in-left` - Slide from left (0.5s)
- `.animate-slide-in-right` - Slide from right (0.5s)

### Scale Animations
- `.animate-zoom-in` - Scale from 0.9 to 1 (0.5s)

### Special Animations
- `.animate-pulse` - Pulsing opacity (2s, repeating)
- `.animate-bounce` - Bouncing up and down (2s, repeating)
- `.animate-glow` - Glowing box-shadow (2s, repeating)
- `.animate-float` - Gentle floating (3s, repeating)
- `.animate-rotate-in` - Rotate and scale in (0.6s)
- `.animate-heart-beat` - Heart beating (1.3s)

**Usage:**
```html
<h1 class="animate-fade-in-up">Animated Heading</h1>
<p class="animate-slide-in-right">Animated paragraph</p>
<button class="animate-bounce">Click me</button>
```

---

## Hover Classes

Add these classes for smooth hover effects:

### Scale Effects
- `.hover-scale` - Scales to 1.05x on hover

### Lift Effects
- `.hover-lift` - Lifts up and adds shadow on hover

### Glow Effects
- `.hover-glow` - Adds blue glow on hover

### Text Effects
- `.hover-color-shift` - Text color changes to sky-blue on hover
- `.hover-underline` - Animated underline appears on hover

**Usage:**
```html
<button class="hover-lift">Lift Button</button>
<div class="hover-scale">Scalable Card</div>
<a class="hover-underline">Link with animated underline</a>
<span class="hover-color-shift">Color shifting text</span>
```

---

## Utility Effects

### Gradient Text
```html
<h1 class="gradient-text">
  Gradient Text Effect
</h1>
```

### Gradient Background
```html
<div class="gradient-bg">
  Animated gradient background
</div>
```

### Loading Spinner
```html
<div class="spinner"></div>
```

### Skeleton Loading (placeholder)
```html
<div class="skeleton" style="width: 200px; height: 100px;"></div>
```

---

## Advanced Usage

### JavaScript API

You can programmatically animate elements:

```javascript
// Access the effects manager (if needed)
// Use data attributes for automatic behavior

// Example: Create staggered animations
const elements = document.querySelectorAll('.item');
InteractiveEffects.staggerElements(elements, 150); // 150ms delay between each
```

### Custom Animation Delays

```html
<!-- Stagger animations with CSS delay -->
<div style="animation-delay: 0.2s" class="animate-fade-in-up">Item 1</div>
<div style="animation-delay: 0.4s" class="animate-fade-in-up">Item 2</div>
<div style="animation-delay: 0.6s" class="animate-fade-in-up">Item 3</div>
```

---

## Dark Mode Compatibility

All animations and effects automatically adapt to dark mode:
- Scrollbars change color
- Text colors adjust for visibility
- Glow effects remain visible
- Hover shadows adjust opacity

---

## Performance Optimization

### Disabled Animations
Respect user's motion preferences:
```css
@media (prefers-reduced-motion: reduce) {
    /* Animations are nearly instant */
    * {
        animation-duration: 0.01ms !important;
    }
}
```

### Mobile Optimization
- Glow cursor hidden on mobile
- Parallax disabled on smaller screens
- Simplified hover effects

---

## Browser Support

- ✅ Chrome 88+
- ✅ Firefox 85+  
- ✅ Safari 14+
- ✅ Edge 88+
- ✅ Mobile browsers

---

## Examples

### Complete Card Component
```html
<article data-card class="hover-lift">
    <h3 class="animate-fade-in-up">Project Title</h3>
    <p class="animate-slide-in-up" style="animation-delay: 0.2s">
        Project description
    </p>
    <button class="hover-scale">Learn More</button>
</article>
```

### Animated Section
```html
<section>
    <h2 data-scroll-animate>Section Heading</h2>
    <p data-scroll-animate>Content paragraph</p>
    <ul>
        <li class="animate-fade-in-up" style="animation-delay: 0s">Item 1</li>
        <li class="animate-fade-in-up" style="animation-delay: 0.2s">Item 2</li>
        <li class="animate-fade-in-up" style="animation-delay: 0.4s">Item 3</li>
    </ul>
</section>
```

---

## Tips & Best Practices

1. **Don't overuse animations** - Keep it subtle, 0.3-0.8s duration
2. **Use cubic-bezier for smoothness** - `cubic-bezier(0.23, 1, 0.320, 1)` is perfect
3. **Respect reduced motion** - Automatically handled by CSS
4. **Test on mobile** - Ensure animations don't lag
5. **Use hardware acceleration** - `transform` and `opacity` for best performance
6. **Stagger animations** - Makes sequential items feel cohesive

---

## Files

- `static/js/effects.js` - Main effects library
- `static/css/style.css` - All animations and hover effects
- `static/js/theme.js` - Dark/light theme toggle
