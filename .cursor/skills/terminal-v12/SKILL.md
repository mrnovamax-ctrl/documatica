---
name: terminal-v12
description: "Terminal v12.0 Design System - Professional, scalable UI/UX design system with physics-based animations. Features: 'The v12.0 Spring' interaction model, comprehensive component library with 40+ components, responsive design (4 breakpoints), design tokens, modular architecture. Use for all UI/UX tasks requiring professional design system. English-only codebase. Brand colors: Core Blue (#3B82F6), Smart Gold (#FBBF24)."
---

# Terminal v12.0 Design System

Professional, scalable UI/UX design system built for reuse across multiple projects. Features physics-based animations ("The v12.0 Spring"), comprehensive component library, and responsive design for mobile, tablet, desktop, and 4K screens.

## 🎯 When to Use This Skill

Use this skill for:
- Creating new UI components with professional design
- Building responsive layouts (mobile, tablet, desktop, 4K)
- Implementing forms, buttons, cards, navigation, and other UI elements
- Ensuring consistent design across the project
- Adding physics-based animations to interactive elements

## 🚨 CRITICAL RULES - MUST FOLLOW

### 1. SINGLE SOURCE OF TRUTH
**Components are created ONCE in CSS, used EVERYWHERE in HTML.**

```
✅ CORRECT WORKFLOW:
1. CREATE component in core.css (or modular CSS file)
2. USE component in HTML pages through classes
3. NEVER duplicate CSS code
4. NEVER create page-specific styles
5. EDIT component = automatically changes everywhere
```

### 2. ABSOLUTE PROHIBITIONS
- ❌ **NO INLINE STYLES** - All styling MUST be done through CSS classes
- ❌ **MINIMIZE !important** - Use only in extreme necessity
- ❌ **NO RANDOM COLORS** - Use ONLY colors from the official palette
- ❌ **NO RUSSIAN IN CODE** - All classes, comments, variables in English
- ❌ **NO ROTATE IN HOVER** - Only use `scale()` and `translateY()` for consistency

### 3. ALL CODE AND CONTENT IN ENGLISH
```html
<!-- ✅ CORRECT -->
<h1>Design System</h1>
<button class="btn-primary">Start Now</button>

<!-- ❌ FORBIDDEN -->
<h1>Система дизайна</h1>
<button class="кнопка-основная">Начать</button>
```

**Rule**: Classes, comments, documentation, AND all user-facing content - everything in English.

## 🎨 Brand Colors - ONLY THESE

```css
/* PRIMARY COLORS */
--color-brand-blue: #3b82f6;    /* Core Blue - main actions */
--color-brand-gold: #fbbf24;    /* Smart Gold - AI features */

/* NEUTRAL SCALE */
--color-slate-50: #f8fafc;
--color-slate-100: #f1f5f9;
--color-slate-200: #e2e8f0;     /* Soft Grey */
--color-slate-900: #0f172a;     /* Dark Slate */

/* SEMANTIC COLORS */
--color-success: #10b981;
--color-warning: #f59e0b;
--color-error: #ef4444;
--color-info: #3b82f6;
```

## ⚡ "The v12.0 Spring" Physics

All interactive elements MUST use spring physics animation:

```css
/* MANDATORY TRANSITION */
transition: all 400ms cubic-bezier(0.34, 1.56, 0.64, 1);

/* OR use CSS variable */
transition: all var(--transition-spring);

/* HOVER - Lift up */
.interactive:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

/* ACTIVE - Press down */
.interactive:active {
  transform: translateY(1px) scale(0.96);
}
```

## 📱 Responsive - 4 BREAKPOINTS MANDATORY

```css
/* MOBILE (Default) - 320px - 767px */
/* Base styles - no media query needed */

/* TABLET - 768px - 1023px */
@media (min-width: 768px) { }

/* DESKTOP - 1024px - 1919px */
@media (min-width: 1024px) { }

/* 4K - 1920px+ */
@media (min-width: 1920px) { }
```

**Rule**: EVERY component MUST work on all 4 resolutions. Mobile-first approach mandatory.

## 📚 Component Library (40+ Components)

All components available in `refs/v12 design/` directory. Before creating a component, READ the corresponding reference files:

| Component | HTML | CSS |
|-----------|------|-----|
| **Design Tokens** | - | [tokens.css](refs/v12 design/tokens.css) |
| **Buttons** | [buttons.html](refs/v12 design/buttons.html) | [buttons.css](refs/v12 design/buttons.css) |
| **Inputs** | [inputs.html](refs/v12 design/inputs.html) | [inputs.css](refs/v12 design/inputs.css) |
| **Cards** | [cards.html](refs/v12 design/cards.html) | [cards.css](refs/v12 design/cards.css) |
| **Tables** | [tables.html](refs/v12 design/tables.html) | [tables.css](refs/v12 design/tables.css) |
| **Modals** | [modals.html](refs/v12 design/modals.html) | [modals.css](refs/v12 design/modals.css) |
| **Navigation** | [navigation.html](refs/v12 design/navigation.html) | [navigation.css](refs/v12 design/navigation.css) |
| **Footer** | [footer.html](refs/v12 design/footer.html) | [footer.css](refs/v12 design/footer.css) |
| **Hero** | [hero.html](refs/v12 design/hero.html) | [hero.css](refs/v12 design/hero.css) |
| **Pricing** | [pricing.html](refs/v12 design/pricing.html) | [pricing.css](refs/v12 design/pricing.css) |
| **Forms** | [inputs.html](refs/v12 design/inputs.html) | [inputs.css](refs/v12 design/inputs.css) |
| **Alerts** | [alerts.html](refs/v12 design/alerts.html) | [alerts.css](refs/v12 design/alerts.css) |
| **Badges** | [badges.html](refs/v12 design/badges.html) | [badges.css](refs/v12 design/badges.css) |
| **Avatars** | [avatars.html](refs/v12 design/avatars.html) | [avatars.css](refs/v12 design/avatars.css) |
| **Checkboxes** | [checkboxes.html](refs/v12 design/checkboxes.html) | [checkboxes.css](refs/v12 design/checkboxes.css) |
| **Selects** | [selects.html](refs/v12 design/selects.html) | [selects.css](refs/v12 design/selects.css) |
| **Tabs** | [tabs.html](refs/v12 design/tabs.html) | [tabs.css](refs/v12 design/tabs.css) |
| **Accordion** | [accordion.html](refs/v12 design/accordion.html) | [accordion.css](refs/v12 design/accordion.css) |
| **Pagination** | [pagination.html](refs/v12 design/pagination.html) | [pagination.css](refs/v12 design/pagination.css) |
| **Progress** | [progress.html](refs/v12 design/progress.html) | [progress.css](refs/v12 design/progress.css) |
| **Timeline** | [timeline.html](refs/v12 design/timeline.html) | [timeline.css](refs/v12 design/timeline.css) |
| **Empty States** | [empty-states.html](refs/v12 design/empty-states.html) | [empty-states.css](refs/v12 design/empty-states.css) |
| **Error Pages** | [error-pages.html](refs/v12 design/error-pages.html) | [error-pages.css](refs/v12 design/error-pages.css) |
| **File Upload** | [file-upload.html](refs/v12 design/file-upload.html) | [file-upload.css](refs/v12 design/file-upload.css) |
| **Gallery** | [gallery.html](refs/v12 design/gallery.html) | [gallery.css](refs/v12 design/gallery.css) |
| **Sidebar** | [sidebar.html](refs/v12 design/sidebar.html) | [sidebar.css](refs/v12 design/sidebar.css) |
| **Chat** | [chat.html](refs/v12 design/chat.html) | [chat.css](refs/v12 design/chat.css) |
| **Profile** | [profile.html](refs/v12 design/profile.html) | [profile.css](refs/v12 design/profile.css) |
| **Product** | [product.html](refs/v12 design/product.html) | [product.css](refs/v12 design/product.css) |
| **Cart** | [cart.html](refs/v12 design/cart.html) | [cart.css](refs/v12 design/cart.css) |
| **Checkout** | [checkout.html](refs/v12 design/checkout.html) | [checkout.css](refs/v12 design/checkout.css) |
| **Typography** | [typography.html](refs/v12 design/typography.html) | [typography.css](refs/v12 design/typography.css) |
| **Colors** | [colors.html](refs/v12 design/colors.html) | [colors.css](refs/v12 design/colors.css) |
| **Icons** | [icons.html](refs/v12 design/icons.html) | [icons.css](refs/v12 design/icons.css) |
| **Grid** | [grid.html](refs/v12 design/grid.html) | [grid.css](refs/v12 design/grid.css) |

## 🔧 Workflow: How to Use This Skill

### When creating a new component:

1. **Find the component** in the table above
2. **Read HTML and CSS files** from `refs/v12 design/`
3. **Copy structure and classes** from reference
4. **Adapt for your task**, maintaining v12.0 style

### Example:

If you need to create a button:
```
1. Read: refs/v12 design/buttons.html and refs/v12 design/buttons.css
2. Choose needed type: btn-primary, btn-gold, btn-outline
3. Use ready structure with correct classes
```

## 📐 Typography Standards

```css
/* Font Family */
font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;

/* Button Typography */
font-weight: 900;              /* Black weight */
text-transform: uppercase;      /* Always uppercase */
letter-spacing: 0.2em;         /* Wide spacing */
font-size: 9px - 11px;         /* Small, bold */

/* Heading Typography */
font-weight: 900;              /* Black weight */
line-height: 1.2;              /* Tight line height */
```

### Two-Color Headings

**Rule**: Use two colors ONLY for multi-word headings (2+ words). NEVER split single words.

```html
<!-- ✅ CORRECT - Multi-word headings -->
<h1>Document <span class="text-primary-light">Management</span></h1>
<h1>Intelligent <span class="text-primary-light">Processing</span></h1>

<!-- ✅ CORRECT - Single word headings stay one color -->
<h1>LAYOUT</h1>
<h1>BUTTONS</h1>

<!-- ❌ FORBIDDEN - Never split one word -->
<h1>LA<span class="text-primary-light">YOUT</span></h1>
```

## 📏 Spacing Scale

```css
--spacing-1: 0.25rem;   /* 4px */
--spacing-2: 0.5rem;    /* 8px */
--spacing-3: 0.75rem;   /* 12px */
--spacing-4: 1rem;      /* 16px - Default */
--spacing-6: 1.5rem;    /* 24px */
--spacing-8: 2rem;      /* 32px */
--spacing-12: 3rem;     /* 48px */
--spacing-16: 4rem;     /* 64px */
--spacing-20: 5rem;     /* 80px */
```

**Usage:**
```html
<!-- Margin utilities -->
<div class="m-4">Margin all sides</div>
<div class="mt-6">Margin top</div>
<div class="mb-8">Margin bottom</div>
<div class="mx-auto">Center horizontally</div>

<!-- Padding utilities -->
<div class="p-6">Padding all sides</div>
<div class="px-8">Padding X (left + right)</div>
<div class="py-10">Padding Y (top + bottom)</div>

<!-- Gap for flex/grid -->
<div class="flex gap-4">Items with gap</div>
```

## 🎨 Border Radius Scale

```css
--radius-sm: 0.375rem;    /* 6px */
--radius-md: 0.5rem;      /* 8px */
--radius-lg: 0.75rem;     /* 12px */
--radius-xl: 1rem;        /* 16px */
--radius-2xl: 1.5rem;     /* 24px */
--radius-3xl: 2rem;       /* 32px */
--radius-full: 9999px;    /* Fully rounded */
```

## ✅ Pre-Delivery Checklist

Before committing ANY code, verify:

- [ ] **SINGLE SOURCE OF TRUTH**: Component defined in core CSS, not duplicated
- [ ] **NO PAGE-SPECIFIC STYLES**: All styles in core CSS, never in `<style>` tags
- [ ] No inline styles (`style=""`)
- [ ] No `!important` (except extreme cases)
- [ ] Only brand colors used
- [ ] Works on all 4 breakpoints (mobile, tablet, desktop, 4K)
- [ ] Uses "v12.0 Spring" animation (`cubic-bezier(0.34, 1.56, 0.64, 1)`)
- [ ] Uses CSS custom properties (no hardcoded values)
- [ ] All text in English (classes, comments, docs, content)
- [ ] Proper ARIA labels for accessibility
- [ ] Follows naming conventions
- [ ] Component documented with header comment
- [ ] **REUSABILITY CHECK**: Can this component be used on other pages?

## 📖 Additional Documentation

- [README.md](README.md) - Full design system documentation
- [DESIGN-RULES.md](DESIGN-RULES.md) - Complete mandatory design rules
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide

## 🚀 Quick Component Examples

### Button
```html
<button class="btn btn-primary">Primary</button>
<button class="btn btn-gold btn-lg">AI Action</button>
<button class="btn btn-outline">Outline</button>
```

### Form Input
```html
<div class="form-group">
  <label class="form-label">Email</label>
  <input type="email" class="input" placeholder="your@email.com">
</div>
```

### Card
```html
<div class="card">
  <div class="card-header">
    <h3 class="card-title">Title</h3>
  </div>
  <div class="card-body">
    <p class="card-text">Content here</p>
  </div>
</div>
```

### Grid Layout
```html
<div class="container">
  <div class="grid-3-col gap-6">
    <div class="card">Card 1</div>
    <div class="card">Card 2</div>
    <div class="card">Card 3</div>
  </div>
</div>
```

## 🎯 Key Features

- ✨ **"The v12.0 Spring"** - Physics-based animations on all interactions
- 🎨 **Design Tokens** - CSS custom properties for easy theming
- 📱 **Fully Responsive** - Mobile-first with 4 breakpoints
- 🚀 **Zero Inline Styles** - Professional, maintainable code
- 🌍 **International** - All code and docs in English
- ♿ **Accessible** - ARIA labels, keyboard navigation, screen reader support
- 🧩 **40+ Components** - Complete UI component library

---

**Version**: v12.0  
**Status**: Production Ready ✅  
**License**: Proprietary - All rights reserved
