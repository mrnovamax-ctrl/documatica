# Documatica v12.0 Design System - VS Code Copilot Skill

A comprehensive design system skill for GitHub Copilot Agent Mode in VS Code. This skill teaches Copilot to generate UI components following the Documatica v12.0 design language.

## Features

- **53+ Premium Components** - Buttons, forms, cards, tables, modals, navigation, and more
- **Complete Reference Library** - HTML + CSS files for every component
- **Design Tokens** - CSS custom properties for consistent styling
- **AI-Ready** - Optimized for GitHub Copilot code generation

## Design Philosophy

- **Extreme Roundness** - `rounded-[3rem]` for sections, `rounded-2xl` for components
- **Whitespace** - Large paddings (`p-10`, `p-16`, `p-24`)
- **Minimalism** - Only 2 accent colors (blue-600 + gold)
- **Typography** - Uppercase tags, font-black headings
- **No Emojis** - SVG icons only (Heroicons, Lucide)

## Installation

### Option 1: Clone to your workspace

```bash
git clone https://github.com/YOUR_USERNAME/documatica-v12-skill.git .github/skills/v12-style
```

### Option 2: Copy files manually

1. Create `.github/skills/v12-style/` in your project
2. Copy `SKILL.md` and `reference/` folder

## Usage

Once installed, GitHub Copilot in Agent Mode will automatically use this skill when you ask for UI-related tasks:

```
@workspace Create a pricing section with 3 tiers following v12 style
```

```
@workspace Build a form with company name and tax ID inputs
```

## Color Palette

| Purpose | Color | CSS Variable |
|---------|-------|--------------|
| Brand/Accent | #3b82f6 | `--docu-blue` |
| AI/System | #FBBF24 | `--docu-gold` |
| Background | #f1f5f9 | `--docu-base` |
| Headings | #0f172a | `--docu-dark` |
| Body text | #64748b | `--docu-body` |

## Components Reference

| Component | Files |
|-----------|-------|
| Buttons | `reference/buttons.html`, `reference/buttons.css` |
| Inputs | `reference/inputs.html`, `reference/inputs.css` |
| Cards | `reference/cards.html`, `reference/cards.css` |
| Tables | `reference/tables.html`, `reference/tables.css` |
| Modals | `reference/modals.html`, `reference/modals.css` |
| Hero | `reference/hero.html`, `reference/hero.css` |
| Pricing | `reference/pricing.html`, `reference/pricing.css` |
| ... | 53+ components total |

## Button Examples

### Primary Button
```html
<button class="bg-blue-600 text-white rounded-2xl font-black uppercase 
               tracking-[0.2em] px-10 py-4 text-[10px] 
               hover:translate-y-[-2px] hover:shadow-xl 
               hover:shadow-blue-600/30 transition-all duration-300">
  Create Document
</button>
```

### AI Action (Gold)
```html
<button class="bg-[#FBBF24] text-slate-900 rounded-2xl font-black 
               uppercase tracking-widest px-8 py-4 text-[10px] 
               hover:bg-[#f59e0b] hover:shadow-[0_0_25px_rgba(251,191,36,0.4)] 
               transition-all duration-300">
  Fill with AI
</button>
```

## Form Input Example

```html
<div>
  <label class="text-[9px] font-black uppercase tracking-widest 
                text-slate-400 ml-2 mb-2 block">
    Company Name
  </label>
  <input type="text" class="w-full bg-slate-50 border border-slate-100 
                            rounded-2xl px-6 py-4 text-sm font-bold 
                            text-slate-900 focus:bg-white focus:border-blue-600 
                            focus:ring-4 focus:ring-blue-600/10 
                            transition-all duration-200" />
</div>
```

## Pre-Delivery Checklist

- [ ] All roundings >= `rounded-2xl`
- [ ] Labels: 9px, uppercase, tracking-widest
- [ ] Buttons: font-black, uppercase, tracking
- [ ] Paddings >= `p-6` for cards
- [ ] Only blue-600 and docu-gold accents
- [ ] No emojis - SVG icons only
- [ ] Hover states with transition
- [ ] Responsive: 375px, 768px, 1024px, 1440px

## License

MIT License - Feel free to use in personal and commercial projects.

## Credits

Created for [Documatica](https://oplatanalogov.ru) - Document Management System

---

**Works with:** Bootstrap 5, React, Vue.js, Django/Jinja, Tailwind CSS
