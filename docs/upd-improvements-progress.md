# Прогресс улучшений УПД генератора

**Дата начала:** 22 января 2026
**Файлы в работе:**
- `backend/app/templates/dashboard/upd/create.html`
- `backend/app/static/js/upd-constructor/upd-main.js` (версия 2.9)
- `backend/app/static/css/upd-constructor.css` (версия 1.5)

---

## Выполненные задачи

### 1. ✅ Проблема с z-index попапов (РЕШЕНО)
**Проблема:** Все попапы (модалы, flatpickr, dropdowns) отображались под футером

**Решение:** 
- Удалён футер из личного кабинета (`{% include 'components/footer.html' %}` убран из create.html строка ~610)
- Добавлены CSS правила в upd-constructor.css для z-index попапов (100000)
- flatpickr calendar получил `position: absolute !important`

**Файлы изменены:**
- `create.html` - удалена строка с include footer
- `upd-constructor.css` v1.4 → v1.5

---

### 2. ✅ Поле "Дата документа" - улучшения
**Что сделано:**
- ✅ По умолчанию ставится сегодняшняя дата
- ✅ Добавлен datepicker (flatpickr) с русской локализацией
- ✅ Добавлена кнопка-иконка календаря для открытия datepicker
- ✅ Возможность ручного ввода даты
- ✅ Маска ввода дд.мм.гггг (автоматическая расстановка точек)
- ✅ Валидация даты:
  - Ограничение дня 01-31
  - Ограничение месяца 01-12
  - Проверка существования даты (31 февраля = ошибка)
  - Сообщение "Некорректная дата" при ошибке

**HTML изменения (create.html):**
```html
<div class="input-group">
  <input type="text" class="form-control date-picker" id="upd-date" placeholder="дд.мм.гггг">
  <button class="btn btn-outline-secondary-600" type="button" id="upd-date-icon">
    <iconify-icon icon="mdi:calendar"></iconify-icon>
  </button>
</div>
```

**JS изменения (upd-main.js строки ~1-70):**
- Flatpickr config: `allowInput: true`, русская локализация
- Маска ввода с проверкой на ввод (event listener 'input')
- Валидация на blur
- Синхронизация с flatpickr

**Версия JS:** 2.6

---

### 3. ✅ Кнопка поиска по ИНН в DaData
**Проблема:** При вводе в поле ИНН кнопка поиска исчезала

**Решение:**
- Увеличен z-index кнопки с 2 до 10 в upd-constructor.css
- Добавлены явные свойства: `pointer-events: auto`, `visibility: visible`, `opacity: 1`
- Добавлен `z-index: 1` для input

**CSS изменения (upd-constructor.css строки ~145-180):**
```css
.input-group .form-control {
  z-index: 1 !important;
}

.input-group .btn {
  z-index: 10 !important;
  pointer-events: auto !important;
  visibility: visible !important;
  opacity: 1 !important;
}
```

**Версия CSS:** 1.5

---

### 4. ✅ Сообщения об ошибках поиска по ИНН
**Что сделано:**
- Сообщения об ошибках теперь выводятся ПОД полем ИНН, а не в notification
- Используется отдельная строка (col-12) чтобы не ломать layout
- Bootstrap alert для оформления
- Автоматическое исчезновение через 5 секунд

**HTML изменения (create.html):**

Для продавца (после строки с ИНН/КПП):
```html
<div class="col-12 d-none" id="seller-inn-error-container">
  <div class="alert alert-danger py-2 px-3 mb-0" role="alert">
    <small id="seller-inn-error"></small>
  </div>
</div>
```

Для покупателя (после строки с ИНН/КПП):
```html
<div class="col-12 d-none" id="buyer-inn-error-container">
  <div class="alert alert-danger py-2 px-3 mb-0" role="alert">
    <small id="buyer-inn-error"></small>
  </div>
</div>
```

**JS изменения (upd-main.js):**

Новые функции (строки ~1345-1380):
```javascript
function showInputError(inputId, message) {
  const errorContainer = $(`#${inputId}-error`);
  const errorContainerWrapper = $(`#${inputId}-error-container`);
  
  input.addClass('is-invalid');
  errorContainer.text(message);
  errorContainerWrapper.removeClass('d-none');
  
  setTimeout(() => clearInputError(inputId), 5000);
}

function clearInputError(inputId) {
  const input = $(`#${inputId}`);
  const errorContainerWrapper = $(`#${inputId}-error-container`);
  
  input.removeClass('is-invalid');
  errorContainerWrapper.addClass('d-none');
}
```

Изменена функция `searchCompanyByInn` (строки ~210-250):
- Вместо `showNotification('error', ...)` → `showInputError('seller-inn', ...)`
- Вместо `showNotification('warning', ...)` → `showInputError('seller-inn', ...)`
- Добавлен `clearInputError(innInputId)` в начале поиска

**Типы ошибок:**
- "ИНН должен содержать минимум 10 символов"
- "Компания с таким ИНН не найдена"
- "Ошибка при поиске компании"

**Версия JS:** 2.9

---

## Текущее состояние файлов

### create.html
- CSS: `upd-constructor.css?v=1.5`
- JS: `upd-main.js?v=2.9`
- Футер удалён
- Контейнеры ошибок для seller-inn и buyer-inn добавлены

### upd-main.js
- Версия: 2.9
- Размер: ~2300 строк
- Основные изменения: строки 1-70 (дата), 210-250 (DaData), 1345-1380 (ошибки)

### upd-constructor.css
- Версия: 1.5
- Размер: ~744 строки
- Основные изменения: строки 145-180 (input-group), 685-738 (z-index)

---

## Что НЕ сделано / В планах

### Дата исправления
- [ ] Убрать placeholder "от" из поля correction-date (по умолчанию должно быть пустым)

### Другие улучшения УПД
- [ ] Продолжение работы над формой (ждём указаний от пользователя)

---

## Важные заметки

1. **WeasyPrint не работает на Windows** - используется HTML-to-print fallback
2. **Футер удалён из всех страниц личного кабинета** - это системное решение, не только для УПД
3. **Flatpickr версия 4.6.13** загружен с CDN jsdelivr
4. **Z-index hierarchy:** flatpickr/modals (100000) > input-group buttons (10) > inputs (1)
5. **API URL:** http://localhost:8000 (Docker port mapping)

---

## Технический стек

- **Backend:** FastAPI + Jinja2
- **Frontend:** Bootstrap + Documatica v12.0 Design System
- **CSS:** `/static/css/documatica.css` (основной) + `upd-constructor.css` (специфичный)
- **JS Libraries:** jQuery, Flatpickr, Bootstrap Bundle
- **Icons:** Iconify

---

## Контакты и доступ

- **User:** e@diez.io
- **Password:** documatica2026
- **Workspace:** /opt/beget/documatica
- **Backup:** documatica_full_backup_20260122_155239 (45 MB, 1,191 files)

---

_Последнее обновление: 22.01.2026 после внедрения сообщений об ошибках под полями ИНН_
