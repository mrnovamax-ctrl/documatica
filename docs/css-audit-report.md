# Отчёт аудита CSS — структура и дублирование

## Порядок загрузки

| Страница | CSS файлы (порядок) |
|----------|---------------------|
| Все (base.html) | bootstrap → v12/core.css → documatica.css |
| Публичные (base_public) | + home.css |
| landing.html | + landing.css |
| contact, envato | + home.css (через base_public) |

## Выявленные проблемы

### 1. Дублирование базовых стилей в home.css

- **:root** — переменные дублируют v12/core.css (slate, colors, etc.)
- **\* { margin: 0; padding: 0; box-sizing }** — уже в core.css
- **body** — уже в core.css

**Рекомендация:** Удалить из home.css. Оставить только переменные, уникальные для home.

### 2. Дублирование pattern-* и bg-*

| Селектор | home.css | documatica.css | Конфликт |
|----------|----------|----------------|----------|
| .pattern-light | 24px grid | 32px, fixed | home перезаписывает (идёт позже) |
| .pattern-dark | 24px | 24px, fixed | разные opacity |
| .bg-white, .bg-surface... | есть | частично в docu | home добавляет утилиты |

**Рекомендация:** Оставить pattern-* и bg-* только в documatica.css. Удалить из home.css. При необходимости скорректировать documatica под текущий вид.

### 3. Legacy Header (.header) — вероятно мёртвый код

- home.css: `.header`, `.header-content`, `.logo`, `.nav-links` (строки ~686–830)
- **Использование:** header_dynamic.html использует `.main-header`. Шаблон с классом `.header` на верхнеуровневом header не найден.
- **Исключение:** contact.py (email) и akt_template.html используют `<div class="header">` — но это в другом контексте (email/PDF), не навигация.

**Рекомендация:** Стили `.header` в home.css относятся к навигации (position: fixed, height: 72px). В email/PDF они вряд ли нужны. Можно удалить блок Legacy Header из home.css. Если email сломается — добавить минимальные стили в шаблон письма.

### 4. Два варианта feature-card

| Страница | Классы | Файл стилей |
|----------|--------|-------------|
| home.html | .feature-card, .feature-icon, .feature-title, .feature-text | home.css |
| landing.html | .feature-card, .feature-card__icon, .feature-card__title, .feature-card__description | landing.css |
| blocks/features.html | .feature-card, .feature-card--bg-* | documatica.css |

**Рекомендация:** Оставить как есть — разные макеты, разная разметка. Не смешивать.

### 5. Структура home.css

Файл ~5260 строк. Основные блоки:
- patterns, bg-* (~90 строк) — дубликаты
- main-header (~450 строк) — нужен для header_dynamic
- Legacy .header (~150 строк) — мёртвый код
- hero, section, feature-card, hero-ai-* — специфика главной/публичных страниц

## Рекомендуемые действия

1. **home.css:** удалить дубликаты (:root, *, body), pattern-*, bg-* (полагаться на documatica)
2. **home.css:** удалить блок Legacy Header (.header, .header-content, .logo, .nav-links и т.д.)
3. **documatica.css:** проверить, что pattern-light, pattern-dark, bg-* покрывают все кейсы
4. **Проверка:** После правок проверить главную, лендинги, contact, envato
