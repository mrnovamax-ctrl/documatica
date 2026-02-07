# GitHub Copilot Instructions for Documatica v12.0

## 🚨 PRE-FLIGHT CHECKLIST (MANDATORY BEFORE EVERY EDIT)

**STOP! Check BEFORE writing code:**
- [ ] No `style=""` attributes? (use classes from core.css)
- [ ] No inline `<script>` tags? (use main.js)
- [ ] All text in English? (no Russian)
- [ ] Colors from palette only? (no random hex)
- [ ] Using CSS variables? (not hardcoded values)
- [ ] Component exists in core.css? (check first!)
- [ ] Responsive on all 4 breakpoints?
- [ ] Using v12.0 Spring easing?
- [ ] Using existing components? (reuse before creating new)
- [ ] Using typography from rules? (Inter font, proper weights)
- [ ] Spacing follows scale? (gap-1, p-4, m-8, etc.)

**If ANY checkbox is NO → DO NOT PROCEED. Fix approach first.**

---

## Core Principles

**SINGLE SOURCE OF TRUTH**: All components defined ONCE in `core.css`, used everywhere through classes. Never duplicate CSS.

**DEMO PAGES RULE**: Demo pages can ONLY use components that exist in `core.css`. If component not in core.css → cannot be used in demos.

## Absolute Rules

### ❌ FORBIDDEN (NEVER ALLOWED)
- Inline styles (`style=""` in HTML or JS innerHTML)
- Inline JavaScript (`<script>` tags in HTML pages)
- Russian language in code/content (English only)
- Random colors outside palette
- Using `!important` (except extreme cases)
- Hardcoded values instead of CSS variables
- Page-specific styles
- Splitting single-word headings into two colors

### ✅ MANDATORY (ALWAYS REQUIRED)
- All styling through CSS classes
- **All JavaScript in `src/js/main.js`** - NO inline `<script>` tags in HTML
- 4 responsive breakpoints (mobile, tablet, desktop, 4K)
- "v12.0 Spring" animation: `cubic-bezier(0.34, 1.56, 0.64, 1)`
- Design tokens from CSS variables
- Multi-word headings: `WORD <span class="text-primary-light">WORD</span>`
- All text uppercase in buttons/headings
- Hub navigation for all pages
- **Reuse existing components** - check core.css before creating new
- **Typography system** - Inter font, weight 900 for headings/buttons, proper letter-spacing
- **Spacing scale compliance** - use gap-*, p-*, m-* classes (1-24)

## Color Palette (ONLY)
```css
--color-brand-blue: #3b82f6;
--color-brand-gold: #fbbf24;
--color-slate-50 through --color-slate-900
--color-success: #10b981;
--color-warning: #f59e0b;
--color-error: #ef4444;
```

## Typography
- Font: Inter (900 weight for buttons/headings)
- **Always use existing typography classes** from core.css
- Font weights: 400 (regular), 500 (medium), 700 (bold), 900 (black)
- Headings: .subsection-title, .type-h1 through .type-h5
- Buttons: UPPERCASE, letter-spacing: 0.2em
- Multi-word headings: First word default, second+ word `.text-primary-light`
- Dark backgrounds: First word `.text-white`, second+ `.text-primary-light`

## Animation Standard
```css
transition: all 400ms cubic-bezier(0.34, 1.56, 0.64, 1);
/* Hover: translateY(-2px) + shadow */
/* Active: translateY(1px) + scale(0.96) */
/* NO rotate() on UI elements */
```

## Spacing
.gap-1, .gap-2, .gap-4, .gap-8 (for flexbox/grid)
```
**CRITICAL**: Never use random spacing values. Always use scale classes. spacing scale only: `--spacing-1` (4px) through `--spacing-24` (96px)
```css
.m-4, .p-4, .mt-4, .mb-4, .mx-4, .my-4 etc.
```

## Responsive Breakpoints
```css
/* Mobile: default (320-767px) */
@media (min-width: 768px) { /* Tablet */ }
@media (min-width: 1024px) { /* Desktop */ }
@media (min-width: 1920px) { /* 4K */ }
```

## File Structure
- `core.css` - single source of truth for all styles
- `main.js` - single source of truth for all JavaScript
- `hub.html` - central navigation to all pages
- `pages/` - component demo pages (must link back to hub)

## Before Committing
- [ ] Component in core.css (not duplicated)
- [ ] Demo pages use ONLY components from core.css
- [ ] No inline styles
- [ ] English only
- [ ] **Reused existing components** where possible
- [ ] **Typography follows system** (Inter, proper weights, classes)
- [ ] **Spacing uses scale** (gap-*, p-*, m-* from 1-24)
- [ ] Brand colors only
- [ ] Works on all breakpoints
- [ ] Uses v12.0 Spring physics
- [ ] CSS variables used
- [ ] Page added to hub navigation

Full rules: See `DESIGN-RULES.md`
