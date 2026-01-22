# Documatica - Инструкции для Copilot

## Общие правила

1. **НЕ использовать эмодзи** - нигде в проекте не используются эмодзи (ни в коде, ни в комментариях, ни в UI)

2. **Язык интерфейса** - русский

3. **Технологический стек**:
   - Backend: FastAPI + Jinja2
   - Frontend: Bootstrap + Documatica v12.0 Design System
   - CSS: `/static/css/documatica.css` (основной файл стилей)
   - Хранение данных: JSON файлы (для MVP)

4. **WeasyPrint не работает на Windows** - используем HTML-to-print fallback

5. **API URL**: http://localhost:8000 / https://new.oplatanalogov.ru/

## Структура проекта

- `backend/` - FastAPI бэкенд
- `backend/app/templates/` - Jinja2 шаблоны
- `backend/app/static/css/documatica.css` - Дизайн-система v12.0
- `backend/data/` - JSON файлы для хранения данных

---

## Дизайн-манифест Documatica v12.0

### 1. Общие принципы (Core Guidelines)

**Геометрия и Скругления:**
- Секции и крупные контейнеры: `rounded-[3rem]` (или 4rem для акцентных CTA)
- Компоненты (кнопки, инпуты, карточки): `rounded-2xl` или `rounded-[1.5rem]`
- Никогда не используй острые углы или стандартный `rounded-md`

**Работа с Пространством (Whitespace):**
- Используй экстремально большие паддинги: `p-10`, `p-16`, `p-24`
- Чем важнее блок, тем больше вокруг него "воздуха"

**Цветовая палитра:**
- Фон: `bg-slate-50` с синим точечным паттерном (`.pattern-light`)
- Текст основной: `slate-500`, заголовки: `slate-900`
- Акценты: только `blue-600` (бренд) и `docu-gold` (#FBBF24) для системных индикаторов

**Микро-взаимодействия:**
- Все интерактивные элементы: `transition 0.3s или 0.5s` с `cubic-bezier(0.4, 0, 0.2, 1)`
- Hover карточек: `hover:-translate-y-2` и мягкая тень

### 2. CSS Variables (Design Tokens)

```css
:root {
  --docu-blue: #3b82f6;
  --docu-gold: #FBBF24;
  --docu-dark: #0f172a;
  --docu-base: #f1f5f9;
  --docu-radius-max: 3rem;
  --docu-radius-input: 1.5rem;
  --docu-ink: #0f172a;        /* slate-900 */
  --docu-body: #64748b;       /* slate-500 */
  --docu-muted: #94a3b8;      /* slate-400 */
}
```

### 3. Типографика (Typography Manifest)

| Элемент | Классы |
|---------|--------|
| H1 Hero | `.docu-h1` - clamp(4rem, 12vw, 8rem), font-black, uppercase, tracking-tighter |
| H2 Section | `.docu-h2` - clamp(2.5rem, 6vw, 3.75rem), font-black, uppercase |
| H3 Card | `.docu-h3` - 1.5rem, font-black, uppercase |
| Tag Primary | `.docu-tag` - 10px, font-black, uppercase, tracking-[0.4em], blue-600 |
| Tag Muted | `.docu-tag-muted` - 10px, font-black, uppercase, tracking-[0.4em], slate-400 |
| Body | `.docu-body` - 1rem, font-medium, slate-500 |
| Lead | `.docu-lead` - 1.25rem, font-medium, slate-500 |
| Micro | `.docu-micro` - 9px, font-bold, uppercase, tracking-widest |

### 4. Геометрия Форм (Form Architecture)

- Фон страницы: `bg-slate-50` с `.pattern-light`
- Контейнер формы: `bg-white`, `border-slate-100`, `rounded-[4rem]`, `p-10 или p-16`
- Тень: `shadow-[0_50px_100px_-20px_rgba(15,23,42,0.05)]`
- Разделители секций: `border-b border-slate-100`

### 5. Поля ввода (Input Components)

**Базовый стиль:**
- `bg-slate-50`, `border border-slate-100`, `rounded-2xl`, `px-6 py-4`

**Focus State:**
- `bg-white`, `border-blue-600`, `ring-4 ring-blue-600/10`

**Labels:**
- `text-[9px] font-black uppercase tracking-widest text-slate-400 ml-2 mb-2`

**Input Values:**
- `text-sm font-bold text-slate-900`

### 6. Контролы выбора (Selection Controls)

**Checkbox:**
- Квадрат `w-6 h-6`, `rounded-lg`, `border-2 border-slate-200`
- Checked: `bg-blue-600`, `border-blue-600`, белая галочка

**Radio Button:**
- Круг `w-5 h-5`, `border-2 border-slate-300`
- Внутри: круг `w-2.5 h-2.5 bg-blue-600` с анимацией scale

### 7. Кнопки (Button Systems)

**7.1. Primary Button (Основное действие):**
- Стиль: `bg-blue-600`, `text-white`, `rounded-2xl`, `font-black`, `uppercase`, `tracking-[0.2em]`
- Размер: Стандарт `px-10 py-4`, текст `text-[10px]`
- Hover: `hover:translate-y-[-2px]`, `hover:shadow-xl`, `hover:shadow-blue-600/30`

**7.2. Massive CTA (Финальный захват):**
- Стиль: `bg-blue-600`, `text-white`, `rounded-[2.5rem]`, `font-black`, `uppercase`, `tracking-[0.3em]`
- Размер: `px-16 py-8`, текст `text-[12px]`
- Hover: Анимация "пружины" `cubic-bezier(0.34, 1.56, 0.64, 1)`, `scale-[1.02]`, `translate-y-[-4px]`

**7.3. AI Action (Смарт-кнопка):**
- Стиль: `bg-[#FBBF24]` (Smart Gold), `text-slate-900`, `rounded-2xl`, `font-black`, `uppercase`, `tracking-widest`
- Hover: `hover:bg-[#f59e0b]`, `hover:shadow-[0_0_25px_rgba(251,191,36,0.4)]`

**7.4. Outline / Ghost:**
- Стиль: `border-2 border-slate-200`, `text-slate-400`, `rounded-2xl`
- Hover: `hover:bg-slate-50`, `hover:text-slate-600`

### 7.5. Спецификация Таблиц (Data Tables)

**Контейнер:** `bg-white`, `border border-slate-100`, `rounded-[2.5rem]`, `overflow-hidden`

**Шапка (Header):**
- Фон: `bg-slate-50/80` (с легким backdrop-blur)
- Текст: `text-[10px] font-black uppercase tracking-[0.4em] text-slate-400`
- Отступы: `px-8 py-5`

**Ячейки данных (Cells):**
- Основной текст: `text-sm font-bold text-slate-900`
- Вторичный текст: `text-sm font-medium text-slate-500`
- Отступы: `px-8 py-6`

**Строки (Rows):**
- Разделитель: `border-b border-slate-50`
- Hover: `hover:bg-slate-50/50 transition-colors`

**Итоговая строка (Total Row):**
- Фон: `bg-blue-50/30`
- Текст суммы: `text-xl font-black text-blue-600 tracking-tighter`

### 8. Логотип

```html
<a href="/" class="docu-logo">
  <svg viewBox="0 0 64 64" width="40" height="40">
    <path d="M12 16H48V48H12V16Z" fill="#3b82f6" fill-opacity="0.1"/>
    <path d="M18 24H46M18 32H46M18 40H34" stroke="#3b82f6" stroke-width="6" stroke-linecap="round"/>
    <circle cx="48" cy="40" r="6" fill="#FBBF24"/>
  </svg>
  <span class="docu-logo-bold">docu</span><span class="docu-logo-light">matica</span>
</a>
```

### 9. Паттерн фона

```css
.pattern-light {
  background-image: radial-gradient(#3b82f6 1px, transparent 1px);
  background-size: 32px 32px;
  opacity: 0.25;
}
```

### 10. Секции Лендинга

| Секция | Класс | Описание |
|--------|-------|----------|
| Hero | `.hero-v12` | pattern-light фон, massive typography |
| Features | `.features-section-v12` | 3-колоночная сетка карточек |
| UPD Types | `.upd-types-v12` | 9 Hub-style карточек |
| Pricing | `.pricing-section-v12` | 3 тарифа (Starter/Pro/Enterprise) |
| CTA | `.cta-section-v12` | Белая карточка с massive button |
| Footer | `.footer-v12` | 5-колоночный, status node, signature |

---

## Prompt для быстрого создания форм

```
Create a form in Documatica v12.0 style.
Use: White card rounded-[4rem], Inter font.
All labels: 9px black uppercase tracking-widest.
Inputs: bg-slate-50, rounded-2xl, bold text.
Footer: A massive blue-600 submit button and a 'System Ready' status node.
```

---

## Референсы WowDash (устаревшее, для dashboard)

Для dashboard используем стили из `Bootstarp_Html/wowdash-admin/`:

| Элемент | Файл-референс |
|---------|---------------|
| Заголовки | `typography.html` |
| Кнопки | `button.html` |
| Дропдауны | `dropdown.html` |
| Табы | `tabs.html` |
| Таблицы | `table-data.html` |
