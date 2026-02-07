# Documatica v12.0 Design System

A professional, scalable UI/UX design system built for reuse across multiple projects. Features physics-based animations ("The v12.0 Spring"), comprehensive component library, and responsive design for mobile, tablet, desktop, and 4K screens.

## Features

- ✨ **Physics-Based Animations**: "The v12.0 Spring" interaction model using `cubic-bezier(0.34, 1.56, 0.64, 1)`
- 📱 **Responsive Design**: 4 breakpoints (Mobile, Tablet, Desktop, 4K)
- 🎨 **Design Tokens**: Complete CSS custom properties system
- 🧩 **Modular Architecture**: Organized into core, components, and utilities
- 🚀 **Performance**: Zero inline styles, minimal !important usage
- 🌍 **International**: All code, comments, and documentation in English
- ⚛️ **Framework Ready**: Prepared for React.js and Vue.js versions

## Design Philosophy

### Brand Colors
- **Core Blue** `#3B82F6` - Primary brand color for main actions
- **Smart Gold** `#FBBF24` - AI-powered features and premium accents
- **Dark Slate** `#0F172A` - Professional backgrounds and navigation
- **Soft Grey** `#E2E8F0` - Subtle backgrounds and form inputs

### Typography
- **Font Family**: Inter (300-900 weights)
- **Button Style**: Uppercase with wide letter-spacing (0.2em-0.3em)
- **Headings**: Black weight (900) with gradient options

### The v12.0 Spring
All interactive elements use physics-based spring animations:
```css
transition: all 400ms cubic-bezier(0.34, 1.56, 0.64, 1);
```

Hover states lift elements with `translateY(-2px)`, active states compress with `scale(0.96)`.

## Installation

1. Clone or download this repository
2. Link to the compiled CSS in your HTML:

```html
<link rel="stylesheet" href="./styles/index.css">
```

Or import individual modules:

```css
@import './styles/core/variables.css';
@import './styles/core/reset.css';
@import './styles/core/layout.css';
@import './styles/components/buttons.css';
/* ... etc */
```

## Project Structure

```
v12Design/
├── src/
│   ├── styles/
│   │   ├── core/              # Foundation
│   │   │   ├── variables.css  # Design tokens
│   │   │   ├── reset.css      # CSS reset
│   │   │   └── layout.css     # Grid/flex/container
│   │   ├── components/        # UI Components
│   │   │   ├── buttons.css
│   │   │   ├── forms.css
│   │   │   ├── cards.css
│   │   │   ├── navbar.css
│   │   │   ├── footer.css
│   │   │   └── preloader.css
│   │   ├── utilities/         # Utility Classes
│   │   │   ├── spacing.css
│   │   │   ├── typography.css
│   │   │   ├── colors.css
│   │   │   └── borders.css
│   │   └── index.css          # Main import file
│   ├── js/
│   │   └── main.js            # Preloader & utilities
│   └── index.html             # Component showcase
└── README.md
```

## Responsive Breakpoints

```css
/* Mobile: 320px - 767px (default) */
/* Tablet: 768px - 1023px */
@media (min-width: 768px) { }

/* Desktop: 1024px - 1919px */
@media (min-width: 1024px) { }

/* 4K: 1920px+ */
@media (min-width: 1920px) { }
```

## Components

### Buttons

5 variants with 4 sizes:

```html
<!-- Variants -->
<button class="btn btn-primary">Primary</button>
<button class="btn btn-gold">AI/Gold</button>
<button class="btn btn-outline">Outline</button>
<button class="btn btn-ghost">Ghost</button>
<button class="btn btn-link">Link</button>

<!-- Sizes -->
<button class="btn btn-sm">Small</button>
<button class="btn btn-md">Medium (default)</button>
<button class="btn btn-lg">Large</button>
<button class="btn btn-massive">Massive</button>
```

### Forms

Complete form controls:

```html
<!-- Text Input -->
<div class="form-group">
  <label class="form-label">Label</label>
  <input type="text" class="input" placeholder="Placeholder">
</div>

<!-- AI Input -->
<div class="input-ai-wrapper">
  <div class="ai-indicator"></div>
  <input type="text" class="input input-ai" placeholder="Ask AI...">
</div>

<!-- Textarea -->
<textarea class="textarea" placeholder="Message..."></textarea>

<!-- Select -->
<select class="select">
  <option>Choose option</option>
</select>

<!-- Toggle Switch -->
<label class="toggle-label">
  <input type="checkbox" class="toggle-input">
  <div class="toggle-switch"></div>
  <span class="toggle-text">Enable feature</span>
</label>

<!-- Checkbox -->
<label class="checkbox-label">
  <input type="checkbox" class="checkbox-input">
  <div class="checkbox-box">
    <svg><!-- checkmark icon --></svg>
  </div>
  <span class="checkbox-text">Label</span>
</label>

<!-- Radio Button -->
<label class="radio-label">
  <input type="radio" class="radio-input" name="group">
  <div class="radio-circle"></div>
  <span class="radio-text">Option</span>
</label>
```

### Cards

Multiple card variants:

```html
<!-- Base Card -->
<div class="card">
  <div class="card-header">
    <h3 class="card-title">Title</h3>
    <p class="card-subtitle">Subtitle</p>
  </div>
  <div class="card-body">
    <p class="card-text">Content</p>
  </div>
  <div class="card-footer">
    <button class="btn btn-sm btn-primary">Action</button>
  </div>
</div>

<!-- Variants -->
<div class="card card-dark">Dark theme</div>
<div class="card card-blue">Blue gradient</div>
<div class="card card-gold">Gold gradient</div>
<div class="card card-outlined">Outlined</div>

<!-- Feature Card -->
<div class="card card-feature">
  <div class="card-feature-icon">
    <svg><!-- icon --></svg>
  </div>
  <!-- ... -->
</div>

<!-- Stat Card -->
<div class="card card-stat">
  <div class="card-stat-value">1.2M+</div>
  <div class="card-stat-label">Users</div>
  <div class="card-stat-trend up">↑ 23%</div>
</div>
```

### Layout

Responsive container and grid:

```html
<!-- Container -->
<div class="container">
  <!-- Max-width responsive container -->
</div>

<!-- Grid System -->
<div class="grid-1-col">1 column</div>
<div class="grid-2-col">2 columns (tablet+)</div>
<div class="grid-3-col">3 columns (desktop+)</div>
<div class="grid-4-col">4 columns (desktop+)</div>

<!-- Flex Utilities -->
<div class="flex">Basic flex</div>
<div class="flex items-center justify-between">
  Centered and spaced
</div>
```

### Navbar

Sticky responsive navigation:

```html
<nav class="navbar">
  <div class="navbar-content">
    <a href="#" class="navbar-brand">
      <svg class="navbar-logo"><!-- logo --></svg>
      <span>BRAND</span>
    </a>
    
    <ul class="navbar-nav">
      <li class="navbar-nav-item">
        <a href="#" class="navbar-nav-link active">Link</a>
      </li>
    </ul>
    
    <div class="navbar-actions">
      <button class="btn btn-sm btn-primary">CTA</button>
    </div>
  </div>
</nav>
```

### Footer

Professional footer with multiple columns:

```html
<footer class="footer">
  <div class="footer-content">
    <div class="footer-grid">
      <div class="footer-brand"><!-- Brand info --></div>
      <div class="footer-column"><!-- Links --></div>
    </div>
    <div class="footer-bottom">
      <p class="footer-copyright">© 2024</p>
      <ul class="footer-legal"><!-- Legal links --></ul>
    </div>
  </div>
</footer>
```

### Preloader

Animated loading screen:

```html
<div class="preloader" id="preloader">
  <div class="preloader-logo">
    <svg class="preloader-logo-svg">
      <path class="preloader-logo-path" d="..."/>
    </svg>
  </div>
  <p class="preloader-text">Loading</p>
  <div class="preloader-progress">
    <div class="preloader-progress-bar"></div>
  </div>
  <div class="preloader-dots">
    <div class="preloader-dot"></div>
    <div class="preloader-dot"></div>
    <div class="preloader-dot"></div>
  </div>
</div>
```

## Utility Classes

### Spacing

```html
<!-- Margin -->
<div class="m-4">Margin all sides</div>
<div class="mt-6">Margin top</div>
<div class="mb-8">Margin bottom</div>
<div class="mx-auto">Center horizontally</div>
<div class="my-12">Margin Y (top + bottom)</div>

<!-- Padding -->
<div class="p-6">Padding all sides</div>
<div class="px-8">Padding X (left + right)</div>
<div class="py-10">Padding Y (top + bottom)</div>

<!-- Gap (for flex/grid) -->
<div class="flex gap-4">Items with gap</div>
```

### Typography

```html
<!-- Font Size -->
<p class="text-xs">Extra small</p>
<p class="text-sm">Small</p>
<p class="text-base">Base</p>
<p class="text-xl">Extra large</p>
<p class="text-6xl">6XL</p>

<!-- Font Weight -->
<p class="font-light">Light (300)</p>
<p class="font-normal">Normal (400)</p>
<p class="font-bold">Bold (700)</p>
<p class="font-black">Black (900)</p>

<!-- Text Alignment -->
<p class="text-left">Left</p>
<p class="text-center">Center</p>
<p class="text-right">Right</p>

<!-- Text Transform -->
<p class="uppercase">UPPERCASE</p>
<p class="lowercase">lowercase</p>
<p class="capitalize">Capitalize</p>

<!-- Text Color -->
<p class="text-primary">Primary text</p>
<p class="text-secondary">Secondary text</p>
<p class="text-brand-blue">Brand blue</p>
<p class="text-gradient">Gradient text</p>

<!-- Letter Spacing -->
<p class="tracking-wide">Wide spacing</p>
<p class="tracking-widest">Widest spacing</p>

<!-- Line Height -->
<p class="leading-tight">Tight line height</p>
<p class="leading-relaxed">Relaxed</p>
```

### Colors

```html
<!-- Background -->
<div class="bg-primary">Primary background</div>
<div class="bg-slate-900">Dark background</div>
<div class="bg-gradient-blue">Blue gradient</div>

<!-- Border -->
<div class="border border-slate-200">Border</div>
<div class="border-2 border-primary">Thick primary</div>

<!-- Opacity -->
<div class="opacity-50">50% opacity</div>
<div class="hover-opacity-80">Hover effect</div>
```

### Borders

```html
<!-- Border Radius -->
<div class="rounded">Medium radius</div>
<div class="rounded-lg">Large radius</div>
<div class="rounded-full">Fully rounded</div>

<!-- Shadow -->
<div class="shadow">Medium shadow</div>
<div class="shadow-xl">Extra large shadow</div>
<div class="shadow-none">No shadow</div>
```

## Design Tokens (CSS Variables)

All customizable via CSS custom properties:

```css
:root {
  /* Colors */
  --color-primary: #3b82f6;
  --color-brand-blue: #3b82f6;
  --color-brand-gold: #fbbf24;
  
  /* Spacing Scale */
  --spacing-1: 0.25rem;  /* 4px */
  --spacing-2: 0.5rem;   /* 8px */
  --spacing-4: 1rem;     /* 16px */
  --spacing-8: 2rem;     /* 32px */
  
  /* Typography */
  --font-size-base: 1rem;
  --font-weight-black: 900;
  --letter-spacing-wide: 0.2em;
  
  /* Border Radius */
  --radius-lg: 12px;
  --radius-2xl: 24px;
  --radius-full: 9999px;
  
  /* Transitions */
  --transition-spring: 400ms cubic-bezier(0.34, 1.56, 0.64, 1);
  
  /* Shadows */
  --shadow-lg: 0 10px 30px rgba(0, 0, 0, 0.15);
}
```

## Code Standards

- ✅ **No Inline Styles**: All styling via CSS classes
- ✅ **Minimal !important**: Only used in extreme edge cases
- ✅ **Mobile-First**: Base styles for mobile, media queries for larger screens
- ✅ **Semantic HTML**: Proper use of HTML5 elements
- ✅ **Accessibility**: ARIA labels, keyboard navigation, screen reader support
- ✅ **English Only**: All code, comments, and documentation in English

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Roadmap

- [x] Core CSS design system
- [x] Complete component library
- [x] Responsive design (4 breakpoints)
- [x] Utility class system
- [x] Documentation
- [ ] React.js version
- [ ] Vue.js version
- [ ] Additional components (modals, dropdowns, tooltips)
- [ ] Animation library expansion
- [ ] Dark mode variant

## Contributing

This design system is built for large-scale reuse across multiple projects. When adding components:

1. Follow the established naming conventions
2. Use design tokens (CSS custom properties)
3. Maintain "The v12.0 Spring" animation standard
4. Ensure responsive design across all 4 breakpoints
5. Document all new components and utilities
6. Write all code and comments in English

## License

Proprietary - All rights reserved

## Version

**v12.0** - Professional Design System with "The v12.0 Spring" physics
