# Documatica v12.0 - Quick Start (3 минуты)

## Главное правило: НЕ УСЛОЖНЯЙ

### ✅ Что нужно знать (всё остальное - детали)

1. **Один файл стилей**: `src/styles/core.css` - ВСЕ стили там
2. **Классы готовы**: Просто используй, не создавай новые
3. **Spacing scale**: `gap-4`, `p-8`, `m-6` (числа 1-24)
4. **Цвета из палитры**: `--color-brand-blue`, `--color-brand-gold`

### 🚀 Начни за 30 секунд

```html
<!DOCTYPE html>
<html>
<head>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;900&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="src/styles/core.css">
</head>
<body>
  <div class="container">
    <button class="btn btn-primary">ЭТО РАБОТАЕТ</button>
  </div>
</body>
</html>
```

### 📦 Готовые компоненты (копируй-вставляй)

**Кнопка:**
```html
<button class="btn btn-primary">КНОПКА</button>
```

**Карточка:**
```html
<div class="card p-8">
  <h3>Заголовок</h3>
  <p>Текст</p>
</div>
```

**Рейтинг:**
```html
<div class="rating-card">
  <div class="rating rating--lg">★★★★★</div>
  <span class="rating-card__score">5.0</span>
  <span class="rating-card__label">ОТЛИЧНО</span>
</div>
```

**Badge:**
```html
<span class="badge badge--primary">NEW</span>
```

### 📐 Размеры и отступы

**НЕ пиши `padding: 20px`**  
**ПИШИ:** `class="p-5"` (20px из spacing scale)

```
p-1 = 4px    gap-4 = 16px   m-8 = 32px
p-2 = 8px    gap-6 = 24px   m-12 = 48px
p-4 = 16px   gap-8 = 32px   m-16 = 64px
```

### 🎨 Цвета

**НЕ пиши `color: #3b82f6`**  
**ПИШИ:** `class="text-primary"` или используй переменную

```css
var(--color-brand-blue)   /* Синий */
var(--color-brand-gold)   /* Золотой */
var(--color-slate-900)    /* Темный текст */
```

### ⚠️ Что ЗАПРЕЩЕНО

- ❌ `style="..."` в HTML
- ❌ Создавать новые CSS файлы
- ❌ Случайные цвета типа `#ff5733`
- ❌ Хардкод размеры `padding: 23px`

### ✅ Правильный workflow

1. Открой `src/hub.html` - посмотри все компоненты
2. Найди нужный компонент
3. Открой страницу компонента (например `pages/buttons.html`)
4. Скопируй код из `<code>` блока
5. Вставь в свой проект
6. Готово!

### 🔧 Адаптивность (автоматическая!)

Все компоненты адаптивные из коробки:
- Mobile: 320-767px
- Tablet: 768-1023px  
- Desktop: 1024-1919px
- 4K: 1920px+

Используй `.flex-row-responsive` для элементов, которые должны переноситься на мобилке.

### 📚 Полная документация

Смотри `DESIGN-RULES.md` только если что-то сломалось или нужны детали.

**Основной принцип: Используй готовое, не изобретай велосипед.**

---

## Примеры реальных задач

**Задача: Добавить карточку с рейтингом**
```html
<div class="container">
  <div class="rating-card">
    <div class="rating rating--lg">
      <span class="rating-star rating-star--filled">★</span>
      <span class="rating-star rating-star--filled">★</span>
      <span class="rating-star rating-star--filled">★</span>
      <span class="rating-star rating-star--filled">★</span>
      <span class="rating-star rating-star--half">★</span>
    </div>
    <span class="rating-card__score">4.5</span>
    <span class="rating-card__label">VERY GOOD</span>
    <span class="rating-card__count">Based on 324 reviews</span>
  </div>
</div>
```

**Задача: Сетка из 3 карточек**
```html
<div class="container">
  <div class="flex-row-responsive gap-6">
    <div class="card p-8">Карточка 1</div>
    <div class="card p-8">Карточка 2</div>
    <div class="card p-8">Карточка 3</div>
  </div>
</div>
```

**Задача: Кнопки рядом**
```html
<div class="flex-row-responsive gap-4">
  <button class="btn btn-primary">ГЛАВНАЯ</button>
  <button class="btn btn-outline">ОТМЕНА</button>
</div>
```

Всё просто. Никаких сложностей.
  </div>
</div>
```

## Responsive Breakpoints

- **Mobile**: 320px - 767px (default, no media query)
- **Tablet**: 768px - 1023px (`@media (min-width: 768px)`)
- **Desktop**: 1024px - 1919px (`@media (min-width: 1024px)`)
- **4K**: 1920px+ (`@media (min-width: 1920px)`)

## Next Steps

1. ✅ Test the showcase page (index.html)
2. ✅ Experiment with different components
3. ⏳ Create React.js version (convert components to React)
4. ⏳ Create Vue.js version (convert components to Vue)
5. ⏳ Add more components (modals, dropdowns, tooltips, tables)

## Design System Features

- ✨ **"The v12.0 Spring"** - Physics-based animations on all interactions
- 🎨 **Design Tokens** - CSS custom properties for easy theming
- 📱 **Fully Responsive** - Mobile-first with 4 breakpoints
- 🚀 **Zero Inline Styles** - Professional, maintainable code
- 🌍 **International** - All code and docs in English
- ♿ **Accessible** - ARIA labels, keyboard navigation, screen reader support

## Support

For questions or issues, refer to the main [README.md](../README.md) for complete documentation.

---

**Version**: v12.0  
**Last Updated**: 2024  
**Status**: Production Ready ✅
