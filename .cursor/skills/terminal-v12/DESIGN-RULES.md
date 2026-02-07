# DOCUMATICA V12.0 - MANDATORY DESIGN RULES

> **CRITICAL**: These rules MUST be followed in every iteration, every component, every file.

## � SINGLE SOURCE OF TRUTH

### Component Development Workflow

**GOLDEN RULE**: Components are created ONCE in CSS, used EVERYWHERE in HTML.

```
1. CREATE component in core.css (or modular CSS file)
2. USE component in HTML pages through classes
3. NEVER duplicate CSS code
4. NEVER create page-specific styles
5. EDIT component = automatically changes everywhere
```

**Example:**
```css
/* ✅ CORRECT - Define ONCE in core.css */
.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 0.75rem;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px -5px rgba(102, 126, 234, 0.4);
}
```

```html
<!-- ✅ CORRECT - Use EVERYWHERE -->
<button class="btn btn-primary btn-lg">Click Me</button>
```

```html
<!-- ❌ FORBIDDEN - Creating new styles in page -->
<style>
  .my-custom-button {
    background: purple;
  }
</style>
<button class="my-custom-button">Wrong</button>
```

**Workflow Steps:**
1. **Creating New Component**: Add to `core.css` → Test on demo page → Component now available globally
2. **Editing Component**: Edit in `core.css` → All pages update automatically
3. **Using Component**: Just add class name to HTML, NO additional CSS needed

**Benefits:**
- ✅ Change button style once → All buttons update
- ✅ Consistency guaranteed across all pages
- ✅ Easier maintenance and debugging
- ✅ Smaller CSS file size (no duplication)
- ✅ True design system approach

### Demonstration Pages Rule

**CRITICAL RULE**: Demo pages can ONLY use components that exist in `core.css`.

```
✅ Component exists in core.css → Can be used in demo pages
❌ Component NOT in core.css → CANNOT be used anywhere
```

**Why This Matters:**
- Demo pages demonstrate the ACTUAL design system
- If component appears in demo → it MUST work (have real styles)
- Prevents "phantom components" (used but not styled)
- Ensures core.css is the true source of truth

**Example:**
```html
<!-- ❌ WRONG - Using .file-upload when it doesn't exist in core.css -->
<div class="file-upload">...</div>

<!-- ✅ CORRECT - Using .dropzone that exists in core.css -->
<div class="dropzone dropzone--compact">...</div>
```

**Workflow:**
1. Need new component in demo? → First create in `core.css`
2. Component exists in core.css? → Now can use in demos
3. Found component in demo but not in core.css? → BUG! Replace or create styles

---

## 🔄 COMPONENT REUSE MANDATE

### Always Reuse Before Creating

**GOLDEN RULE**: Before creating ANY new component, CHECK if similar component already exists in `core.css`.

**Process:**
1. **Search First**: Look through `core.css` for existing similar components
2. **Reuse & Extend**: Use existing component with modifier classes if needed
3. **Only Then Create**: Create new component ONLY if nothing similar exists

**Examples:**

```html
<!-- ❌ WRONG - Creating new button when .btn exists -->
<style>
.my-special-button {
  padding: 0.75rem 1.5rem;
  border-radius: 0.75rem;
  /* ... duplicating .btn styles */
}
</style>

<!-- ✅ CORRECT - Reusing .btn with modifier -->
<button class="btn btn-primary btn-lg">Click Me</button>
```

**Why This Matters:**
- ✅ Prevents duplicate code
- ✅ Maintains consistency across project
- ✅ Reduces CSS file size
- ✅ Makes future updates easier

---

## 📝 TYPOGRAPHY SYSTEM MANDATE

### Always Use Typography Classes

**GOLDEN RULE**: NEVER write font-size, font-weight, letter-spacing manually. Use existing typography classes from `core.css`.

**Available Typography Classes:**
```css
/* Headings */
.subsection-title
.type-h1, .type-h2, .type-h3, .type-h4, .type-h5

/* Text Styles */
.type-body
.type-small
.type-caption
.type-link
.type-highlight
```

**Font Weights:**
- 400 (regular) - body text
- 500 (medium) - subtle emphasis
- 700 (bold) - strong emphasis
- 900 (black) - headings, buttons

**Examples:**

```html
<!-- ❌ WRONG - Manual typography -->
<h2 style="font-size: 24px; font-weight: 900; text-transform: uppercase;">Title</h2>

<!-- ✅ CORRECT - Using typography class -->
<h2 class="subsection-title">Title</h2>
```

**Why This Matters:**
- ✅ Consistent typography across entire project
- ✅ Easier to update typography globally
- ✅ Proper Inter font usage with correct weights

---

## 📏 SPACING SCALE MANDATE

### Always Use Spacing Scale Classes

**GOLDEN RULE**: NEVER use random spacing values. ALWAYS use spacing scale classes (1-24).

**Spacing Scale:**
```css
--spacing-1: 0.25rem;  /* 4px */   → .gap-1, .p-1, .m-1
--spacing-2: 0.5rem;   /* 8px */   → .gap-2, .p-2, .m-2
--spacing-3: 0.75rem;  /* 12px */  → .gap-3, .p-3, .m-3
--spacing-4: 1rem;     /* 16px */  → .gap-4, .p-4, .m-4
--spacing-5: 1.25rem;  /* 20px */  → .gap-5, .p-5, .m-5
--spacing-6: 1.5rem;   /* 24px */  → .gap-6, .p-6, .m-6
--spacing-8: 2rem;     /* 32px */  → .gap-8, .p-8, .m-8
--spacing-10: 2.5rem;  /* 40px */  → .gap-10, .p-10, .m-10
--spacing-12: 3rem;    /* 48px */  → .gap-12, .p-12, .m-12
--spacing-16: 4rem;    /* 64px */  → .gap-16, .p-16, .m-16
--spacing-20: 5rem;    /* 80px */  → .gap-20, .p-20, .m-20
--spacing-24: 6rem;    /* 96px */  → .gap-24, .p-24, .m-24
```

**Usage Classes:**
```css
/* Padding */
.p-4    /* padding: 1rem (all sides) */
.px-4   /* padding-left & padding-right */
.py-4   /* padding-top & padding-bottom */
.pt-4   /* padding-top only */
.pb-4   /* padding-bottom only */

/* Margin */
.m-4    /* margin: 1rem (all sides) */
.mx-4   /* margin-left & margin-right */
.my-4   /* margin-top & margin-bottom */
.mt-4   /* margin-top only */
.mb-4   /* margin-bottom only */

/* Gap (flexbox/grid) */
.gap-1  /* gap: 0.25rem */
.gap-4  /* gap: 1rem */
.gap-8  /* gap: 2rem */
```

**Examples:**

```html
<!-- ❌ WRONG - Random spacing value -->
<div style="padding: 15px; margin: 23px; gap: 18px;">Bad</div>

<!-- ✅ CORRECT - Using spacing scale -->
<div class="p-4 m-6 gap-4">Good</div>
```

**Why This Matters:**
- ✅ Consistent spacing rhythm across entire project
- ✅ Visual harmony and professional look
- ✅ Easier to maintain and update spacing globally
- ✅ Prevents random pixel values

---

## �🚫 ABSOLUTE PROHIBITIONS

### 1. NO INLINE STYLES
```html
<!-- ❌ FORBIDDEN -->
<div style="color: red; margin: 10px;">Bad</div>

<!-- ✅ CORRECT -->
<div class="text-error m-4">Good</div>
```

**Rule**: All styling MUST be done through CSS classes. Zero exceptions.

---

### 2. NO INLINE JAVASCRIPT
```html
<!-- ❌ FORBIDDEN -->
<script>
  function initAccordion() {
    // JavaScript code in HTML file
  }
</script>

<!-- ✅ CORRECT - Use main.js -->
<script src="../js/main.js"></script>
```

**Rule**: All JavaScript MUST be in `src/js/main.js`. NO `<script>` tags in HTML pages.

**Why This Matters:**
- ✅ Single source of truth for all functionality
- ✅ Easier debugging and maintenance
- ✅ Better code organization
- ✅ Prevents duplicate logic across pages
- ✅ Consistent initialization patterns

---

### 3. MINIMIZE !important
```css
/* ❌ FORBIDDEN (except extreme edge cases) */
.button {
  color: blue !important;
}

/* ✅ CORRECT */
.button {
  color: var(--color-primary);
}
```

**Rule**: Use `!important` only in extreme necessity. Prefer proper CSS specificity.

---

## 🎨 BRAND COLORS - ONLY THESE

### Official Color Palette

```css
/* PRIMARY COLORS */
--color-brand-blue: #3b82f6;    /* Core Blue - main actions */
--color-brand-gold: #fbbf24;    /* Smart Gold - AI features */

/* NEUTRAL SCALE */
--color-slate-50: #f8fafc;
--color-slate-100: #f1f5f9;
--color-slate-200: #e2e8f0;     /* Soft Grey */
--color-slate-300: #cbd5e1;
--color-slate-400: #94a3b8;
--color-slate-500: #64748b;
--color-slate-600: #475569;
--color-slate-700: #334155;
--color-slate-800: #1e293b;
--color-slate-900: #0f172a;     /* Dark Slate */

/* SEMANTIC COLORS */
--color-success: #10b981;       /* Green for success */
--color-warning: #f59e0b;       /* Orange for warnings */
--color-error: #ef4444;         /* Red for errors */
--color-info: #3b82f6;          /* Blue for info */
```

**Rule**: Use ONLY colors from this palette. No random colors (#ff0000, #123456, etc.).

---

## 📱 RESPONSIVE - 4 BREAKPOINTS MANDATORY

### Breakpoint System

```css
/* MOBILE (Default) */
/* 320px - 767px */
/* Base styles - no media query needed */

/* TABLET */
@media (min-width: 768px) {
  /* 768px - 1023px */
}

/* DESKTOP */
@media (min-width: 1024px) {
  /* 1024px - 1919px */
}

/* 4K */
@media (min-width: 1920px) {
  /* 1920px+ */
}
```

**Rule**: EVERY component MUST work on all 4 resolutions. Mobile-first approach mandatory.

---

## ⚡ "THE V12.0 SPRING" PHYSICS

### Animation Standard

```css
/* MANDATORY TRANSITION */
transition: all 400ms cubic-bezier(0.34, 1.56, 0.64, 1);

/* OR use CSS variable */
transition: all var(--transition-spring);
```

**Rule**: All interactive elements (buttons, cards, inputs) MUST use spring physics animation.

### Interaction States

```css
/* HOVER - Lift up */
.interactive:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

/* ACTIVE - Press down */
.interactive:active {
  transform: translateY(1px) scale(0.96);
}

/* DISABLED - Grayscale */
.interactive:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  filter: grayscale(100%);
}
```

**Rule**: Follow these exact interaction patterns for consistency.

**IMPORTANT**: DO NOT use `rotate()` in hover states for icons or UI elements. Only use `scale()` and `translateY()` for consistency.

```css
/* ❌ FORBIDDEN */
.icon:hover {
  transform: rotate(5deg);
}

/* ✅ CORRECT */
.icon:hover {
  transform: scale(1.05);
}
```

---

## 🎯 CSS ARCHITECTURE RULES

### 1. Use CSS Custom Properties (Design Tokens)

```css
/* ✅ CORRECT */
.button {
  background-color: var(--color-primary);
  padding: var(--spacing-4) var(--spacing-6);
  border-radius: var(--radius-lg);
}

/* ❌ FORBIDDEN */
.button {
  background-color: #3b82f6;
  padding: 16px 24px;
  border-radius: 12px;
}
```

**Rule**: Always use CSS variables from `variables.css`. No hardcoded values.

---

### 2. Modular File Structure

```
styles/
├── core/           # Foundation (variables, reset, layout)
├── components/     # UI components (buttons, cards, etc.)
└── utilities/      # Helper classes (spacing, typography)
```

**Rule**: Keep modular architecture. One component = one file.

---

### 3. Naming Conventions

```css
/* Component Classes - use BEM-like approach */
.card { }
.card-header { }
.card-title { }
.card-body { }

/* Modifiers - use double dash */
.btn-primary { }
.btn-lg { }
.card-dark { }

/* State Classes */
.is-active { }
.is-disabled { }
.has-error { }
```

**Rule**: Consistent, semantic class names in English.

---

### 4. Hub Navigation Structure

```
src/
├── hub.html           # Main hub page with all component links
└── pages/
    ├── colors.html    # Each page has link back to hub
    ├── buttons.html   # Each page has link back to hub
    └── forms.html     # Each page has link back to hub
```

**Rule**: Every new component page MUST:
1. Be added to hub.html navigation menu
2. Include link back to hub.html in its navbar
3. Have consistent navigation structure across all pages

```html
<!-- Hub.html must include ALL pages -->
<a href="pages/new-component.html" class="kit-card">...</a>

<!-- Each page must link back to hub -->
<div class="navbar-menu">
  <a href="../hub.html" class="nav-link">Hub</a>
  <!-- other links -->
</div>
```

**Rule**: Hub is the central navigation point. Never create orphan pages.

---

## 📐 TYPOGRAPHY STANDARDS

### Font Settings

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

**Rule**: Buttons are ALWAYS uppercase, black weight, wide letter-spacing.

---

### Two-Color Headings

**Rule**: Use two colors ONLY for multi-word headings (2+ words). NEVER split single words.

```html
<!-- ✅ CORRECT - Multi-word headings (light background) -->
<h1>Document <span class="text-primary-light">Management</span></h1>
<h1>Intelligent <span class="text-primary-light">Processing</span></h1>

<!-- ✅ CORRECT - Multi-word headings (dark background) -->
<section class="pattern-dots-dark">
  <h1 class="text-white">Security <span class="text-primary-light">Enterprise</span></h1>
  <h1 class="text-white">Documatica <span class="text-primary-light">Platform</span></h1>
</section>

<!-- ✅ CORRECT - Single word headings stay one color -->
<h1>LAYOUT</h1>
<h1>CARDS</h1>
<h1>BUTTONS</h1>

<!-- ❌ FORBIDDEN - Never split one word -->
<h1>КНО<span class="text-primary-light">ПКИ</span></h1>
<h1>LA<span class="text-primary-light">YOUT</span></h1>
```

**Pattern (Light Backgrounds)**:
- First word: default dark color (no class needed)
- Second+ word: `.text-primary-light` (#60a5fa - light blue)
- Only for compound headings with 2+ separate words
- Logo pattern: `docu<span class="brand-light">matica</span>`

**Pattern (Dark Backgrounds)**:
- First word: `.text-white` (#ffffff - white)
- Second+ word: `.text-primary-light` (#60a5fa - light blue)
- Always wrap first word in `.text-white` on dark backgrounds
- Works with: `.bg-dark`, `.pattern-dots-dark`, other dark patterns

---

## 🔧 ACCESSIBILITY REQUIREMENTS

### 1. ARIA Labels

```html
<!-- ✅ CORRECT -->
<button aria-label="Close menu">×</button>
<input type="search" aria-label="Search products">
```

**Rule**: All interactive elements need proper ARIA labels.

---

### 2. Keyboard Navigation

```css
/* Focus states mandatory */
.btn:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
```

**Rule**: All interactive elements must be keyboard accessible.

---

### 3. Screen Reader Support

```css
/* Screen reader only class */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}
```

**Rule**: Provide screen reader context where needed.

---

## 📝 CODE QUALITY STANDARDS

### 1. All Code AND Content in English

```css
/* ✅ CORRECT - Code in English */
.button-primary { }
.card-header { }

/* ❌ FORBIDDEN - Russian code */
.кнопка-основная { }
.заголовок-карточки { }
```

```html
<!-- ✅ CORRECT - Content in English -->
<h1>Design System</h1>
<p>Professional design system components</p>
<button>Start Now</button>

<!-- ❌ FORBIDDEN - Russian content -->
<h1>Система дизайна</h1>
<p>Профессиональная система дизайна</p>
<button>Начать работу</button>
```

**Rule**: Classes, comments, documentation, AND all user-facing content - everything in English. Russian is allowed ONLY in examples/demonstrations where you're specifically showing localization features.

---

### 2. Component Documentation

```css
/* ==============================================
   DOCUMATICA V12.0 DESIGN SYSTEM
   Button Components
   Version: 1.0.0
   ============================================== */
```

**Rule**: Every component file starts with header comment.

---

## 🎨 BORDER RADIUS SCALE

```css
--radius-sm: 0.375rem;    /* 6px */
--radius-md: 0.5rem;      /* 8px */
--radius-lg: 0.75rem;     /* 12px */
--radius-xl: 1rem;        /* 16px */
--radius-2xl: 1.5rem;     /* 24px */
--radius-3xl: 2rem;       /* 32px */
--radius-full: 9999px;    /* Fully rounded */
```

**Rule**: Use only these border radius values. No custom values.

---

## 📏 SPACING SCALE

```css
--spacing-1: 0.25rem;   /* 4px */
--spacing-2: 0.5rem;    /* 8px */
--spacing-3: 0.75rem;   /* 12px */
--spacing-4: 1rem;      /* 16px */
--spacing-5: 1.25rem;   /* 20px */
--spacing-6: 1.5rem;    /* 24px */
--spacing-8: 2rem;      /* 32px */
--spacing-10: 2.5rem;   /* 40px */
--spacing-12: 3rem;     /* 48px */
--spacing-16: 4rem;     /* 64px */
--spacing-20: 5rem;     /* 80px */
--spacing-24: 6rem;     /* 96px */
```

**Rule**: Use spacing scale for margins, padding. No arbitrary values like `margin: 15px`.

---

## 📦 SPACING UTILITIES - MARGIN & PADDING

### Utility Class Pattern

```css
/* MARGIN */
.m-4    { margin: var(--spacing-4); }          /* All sides */
.mt-4   { margin-top: var(--spacing-4); }      /* Top */
.mb-4   { margin-bottom: var(--spacing-4); }   /* Bottom */
.ml-4   { margin-left: var(--spacing-4); }     /* Left */
.mr-4   { margin-right: var(--spacing-4); }    /* Right */
.mx-4   { margin-left: var(--spacing-4); margin-right: var(--spacing-4); }  /* X-axis */
.my-4   { margin-top: var(--spacing-4); margin-bottom: var(--spacing-4); }  /* Y-axis */

/* PADDING */
.p-4    { padding: var(--spacing-4); }         /* All sides */
.pt-4   { padding-top: var(--spacing-4); }     /* Top */
.pb-4   { padding-bottom: var(--spacing-4); }  /* Bottom */
.pl-4   { padding-left: var(--spacing-4); }    /* Left */
.pr-4   { padding-right: var(--spacing-4); }   /* Right */
.px-4   { padding-left: var(--spacing-4); padding-right: var(--spacing-4); }  /* X-axis */
.py-4   { padding-top: var(--spacing-4); padding-bottom: var(--spacing-4); }  /* Y-axis */
```

### Usage Rules

**1. Margin vs Padding**
```html
<!-- ✅ CORRECT - Use margin for spacing BETWEEN elements -->
<div class="card mb-6">First card</div>
<div class="card">Second card</div>

<!-- ✅ CORRECT - Use padding for spacing INSIDE elements -->
<div class="card p-6">
  <h3>Card content</h3>
</div>

<!-- ❌ FORBIDDEN - Arbitrary values -->
<div style="margin: 15px; padding: 23px;">Bad</div>
```

**2. Gap for Grid & Flexbox**
```css
/* ✅ CORRECT - Use gap for grid/flex children spacing */
.grid {
  display: grid;
  gap: var(--spacing-4);
}

.flex-row {
  display: flex;
  gap: var(--spacing-3);
}

/* ❌ FORBIDDEN - Using margins on grid/flex children instead of gap */
.grid-item {
  margin: 10px;
}
```

**3. Directional Spacing Naming**
```
m  = margin
p  = padding
t  = top
b  = bottom
l  = left
r  = right
x  = left + right (horizontal)
y  = top + bottom (vertical)

Numbers = spacing scale values (1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24)
```

**4. Common Patterns**
```html
<!-- Section spacing -->
<section class="py-12">...</section>

<!-- Card spacing -->
<div class="card p-6 mb-4">...</div>

<!-- Button spacing -->
<button class="btn px-6 py-3">Click</button>

<!-- Text spacing -->
<h2 class="mb-2">Title</h2>
<p class="mb-4">Paragraph</p>
```

**5. Responsive Spacing**
```css
/* ✅ CORRECT - Adjust spacing for different screens */
.section {
  padding: var(--spacing-8);
}

@media (min-width: 1024px) {
  .section {
    padding: var(--spacing-12);
  }
}

@media (min-width: 1920px) {
  .section {
    padding: var(--spacing-16);
  }
}
```

### Spacing Scale Reference

| Class | Value | Pixels | Use Case |
|-------|-------|--------|----------|
| `.m-1` / `.p-1` | 0.25rem | 4px | Tiny gaps, icon spacing |
| `.m-2` / `.p-2` | 0.5rem | 8px | Tight spacing, badges |
| `.m-3` / `.p-3` | 0.75rem | 12px | Button padding, small gaps |
| `.m-4` / `.p-4` | 1rem | 16px | **Default spacing**, card padding |
| `.m-6` / `.p-6` | 1.5rem | 24px | Card padding, section gaps |
| `.m-8` / `.p-8` | 2rem | 32px | Large spacing, section padding |
| `.m-12` / `.p-12` | 3rem | 48px | Section padding, hero spacing |
| `.m-16` / `.p-16` | 4rem | 64px | Major sections, hero padding |

**GOLDEN RULES**:
- ✅ Use `.m-4` as default spacing between components
- ✅ Use `.p-6` as default card/container padding
- ✅ Use `gap` for grid/flex instead of margins on children
- ✅ Use only spacing scale values (1, 2, 3, 4, 6, 8, 12, 16, 20, 24)
- ❌ NEVER use arbitrary values like `margin: 15px` or `padding: 27px`
- ❌ NEVER use negative margins (except extreme cases)

---

## ✅ VALIDATION CHECKLIST

Before committing ANY code, verify:

- [ ] **SINGLE SOURCE OF TRUTH**: Component defined in core.css, not duplicated
- [ ] **NO PAGE-SPECIFIC STYLES**: All styles in core.css, never in `<style>` tags
- [ ] No inline styles (`style=""`)
- [ ] No `!important` (except extreme cases)
- [ ] Only brand colors used
- [ ] Works on all 4 breakpoints (mobile, tablet, desktop, 4K)
- [ ] Uses "v12.0 Spring" animation (`cubic-bezier(0.34, 1.56, 0.64, 1)`)
- [ ] Uses CSS custom properties (no hardcoded values)
- [ ] All text in English (classes, comments, docs)
- [ ] Proper ARIA labels for accessibility
- [ ] Follows naming conventions
- [ ] Component documented with header comment
- [ ] New page added to hub.html navigation
- [ ] Page has link back to hub.html in navbar
- [ ] **REUSABILITY CHECK**: Can this component be used on other pages?

---

## 🚀 QUICK REFERENCE

### Color Usage
- Main actions → `var(--color-brand-blue)`
- AI features → `var(--color-brand-gold)`
- Dark backgrounds → `var(--color-slate-900)`
- Light backgrounds → `var(--color-slate-50)`

### Responsive Pattern
```css
.component {
  /* Mobile (default) */
  padding: var(--spacing-4);
}

@media (min-width: 768px) {
  .component {
    /* Tablet */
    padding: var(--spacing-6);
  }
}

@media (min-width: 1024px) {
  .component {
    /* Desktop */
    padding: var(--spacing-8);
  }
}

@media (min-width: 1920px) {
  .component {
    /* 4K */
    padding: var(--spacing-12);
  }
}
```

### Animation Pattern
```css
.interactive {
  transition: all var(--transition-spring);
}

.interactive:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.interactive:active {
  transform: translateY(1px) scale(0.96);
}
```

---

## 📋 SUMMARY

**NEVER**:
- Inline styles
- Random colors outside palette
- Skip responsive breakpoints
- Use `!important` carelessly
- Use Russian in code (classes, comments, variables) or content (headings, text, buttons)

**ALWAYS**:
- 4 breakpoints (mobile, tablet, desktop, 4K)
- Brand colors only
- CSS custom properties
- "v12.0 Spring" physics
- English language
- Accessibility features

---

**This document is LAW for Documatica v12.0 Design System.**

Last Updated: January 2026
