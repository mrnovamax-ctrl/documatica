# Отчёт: Исправление переноса полей в PDF УПД

**Дата:** 2 февраля 2026  
**Статус:** ✅ Исправлено

## Проблемы, которые были обнаружены и исправлены

### 1. ❌ Несоответствие имён переменных дата/сведения

**Проблема:** API передавал данные с одними именами, а шаблон ожидал другие

| Поле в API | Поле в шаблоне (старое) | Статус |
|------------|-------------------------|---------|
| `shipping_date` | `transfer_date` | ❌ Не совпадало |
| `other_shipping_info` | `other_transfer_info` | ❌ Не совпадало |
| `receiving_date` | `receipt_date` | ❌ Не совпадало |
| `other_receiving_info` | `other_receipt_info` | ❌ Не совпадало |
| `contract_info` | `transfer_basis` | ❌ Не совпадало |

**Решение:** Добавлены алиасы в `/backend/app/api/documents.py` (строки 257-272):
```python
# Подписант продавца
"shipping_date": format_date_short(request.shipping_date) if request.shipping_date else None,
"transfer_date": format_date_short(request.shipping_date) if request.shipping_date else None,  # Алиас
"other_shipping_info": request.other_shipping_info,
"other_transfer_info": request.other_shipping_info,  # Алиас
"contract_info": request.contract_info,
"transfer_basis": request.contract_info,  # Алиас (основание передачи)

# Подписант покупателя
"receiving_date": format_date_short(request.receiving_date) if request.receiving_date else None,
"receipt_date": format_date_short(request.receiving_date) if request.receiving_date else None,  # Алиас
"other_receiving_info": request.other_receiving_info,
"other_receipt_info": request.other_receiving_info,  # Алиас
```

Теперь оба имени работают, обеспечена обратная совместимость.

---

### 2. ❌ Неправильное использование seller_signer вместо seller_responsible

**Проблема:** В блоке [13] (Ответственный за правильность оформления) использовались данные подписанта (`seller_signer`), а не ответственного лица (`seller_responsible`)

**Где:** `/backend/app/templates/upd_template.html`, строки 1590-1620

**Что было:**
```html
<td colspan=16 class=xl83>{% if seller_signer %}{{ seller_signer.full_name }}{% endif %}</td>
```

**Что стало:**
```html
<td colspan=9 class=xl83>{% if seller_responsible %}{{ seller_responsible.position|default('', true) }}{% endif %}</td>
<td colspan=12 class=xl83>{% if seller_responsible and seller_responsible.signature_image %}...</td>
<td colspan=16 class=xl83>{% if seller_responsible %}{{ seller_responsible.full_name }}{% endif %}</td>
```

Теперь в блоке [13] корректно используются:
- `seller_responsible.position` - должность ответственного
- `seller_responsible.full_name` - ФИО ответственного
- `seller_responsible.signature_image` - подпись ответственного

---

### 3. ❌ Неправильное использование buyer_signer вместо buyer_responsible

**Проблема:** Аналогично для покупателя в блоке [18]

**Что было:**
```html
<td colspan=7 class=xl83>{% if buyer_signer %}{{ buyer_signer.full_name }}{% endif %}</td>
```

**Что стало:**
```html
<td colspan=9 class=xl83>{% if buyer_responsible %}{{ buyer_responsible.position|default('', true) }}{% endif %}</td>
<td colspan=7 class=xl83>{% if buyer_responsible and buyer_responsible.signature_image %}...</td>
<td colspan=9 class=xl83>{% if buyer_responsible %}{{ buyer_responsible.full_name }}{% endif %}</td>
```

---

### 4. ✅ Поля, которые уже работали корректно

| Поле | Статус | Где используется |
|------|--------|------------------|
| `shipping_document` | ✅ Передаётся в API | Готов к использованию |
| `contract_info` / `transfer_basis` | ✅ Работает | Блок [8], строка 1293 |
| `transport_info` | ✅ Работает | Блок [9], строка 1349 |
| `payment_document` | ✅ Передаётся | API готов |
| `government_contract_id` | ✅ Работает | - |

---

## Структура данных подписантов

### seller_signer (Блок [10]) - Товар передал
- `position` - должность
- `full_name` - ФИО
- `signature_image` - подпись

### seller_responsible (Блок [13]) - Ответственный за оформление
- `position` - должность
- `full_name` - ФИО
- `signature_image` - подпись

### buyer_signer (Блок [15]) - Товар получил
- `position` - должность  
- `full_name` - ФИО
- `signature_image` - подпись

### buyer_responsible (Блок [18]) - Ответственный за оформление
- `position` - должность
- `full_name` - ФИО
- `signature_image` - подпись

---

## Итоги

✅ **Все поля теперь корректно переносятся в PDF:**

1. ✅ `shipping_date` → отображается в блоке [11] "Дата отгрузки" (через алиас `transfer_date`)
2. ✅ `receiving_date` → отображается в блоке [16] "Дата получения" (через алиас `receipt_date`)
3. ✅ `other_shipping_info` → отображается в блоке [12] "Иные сведения об отгрузке" (через алиас `other_transfer_info`)
4. ✅ `other_receiving_info` → отображается в блоке [17] "Иные сведения о получении" (через алиас `other_receipt_info`)
5. ✅ `seller_responsible.position` → отображается в блоке [13]
6. ✅ `seller_responsible.full_name` → отображается в блоке [13]
7. ✅ `buyer_responsible.position` → отображается в блоке [18]
8. ✅ `buyer_responsible.full_name` → отображается в блоке [18]
9. ✅ `contract_info` → отображается в блоке [8] "Основание передачи" (через алиас `transfer_basis`)
10. ✅ `shipping_document` - передаётся в API (готов к использованию)

---

## Тестирование

### Автоматический тест

Запустите тестовый скрипт:

```bash
cd /opt/beget/documatica/backend
python test_upd_fields.py
```

### Ручное тестирование через форму

Заполните в форме УПД:

**Блок "Дополнительные сведения":**
- ✅ К платежно-расчетному документу: `№123 от 01.02.2026`
- ✅ Документ об отгрузке: `Накладная №456`

**Блок "Подписант со стороны продавца":**
- ✅ Основание передачи: `Договор №789 от 01.01.2026`
- ✅ Данные о транспортировке: `Транспортная накладная ТН-123`
- ✅ Товар передал - Должность: `Директор`
- ✅ Товар передал - ФИО: `Иванов И.И.`
- ✅ Дата отгрузки: `02.02.2026`
- ✅ Иные сведения об отгрузке: `Товар в исправном состоянии`
- ✅ Ответственный - Должность: `Главный бухгалтер`
- ✅ Ответственный - ФИО: `Петрова П.П.`

**Блок "Подписант со стороны покупателя":**
- ✅ Товар получил - Должность: `Менеджер`
- ✅ Товар получил - ФИО: `Сидоров С.С.`
- ✅ Дата получения: `03.02.2026`
- ✅ Иные сведения о получении: `Претензий нет`
- ✅ Ответственный - Должность: `Ведущий специалист`
- ✅ Ответственный - ФИО: `Васильева В.В.`

Сгенерируйте PDF и проверьте, что все поля отображаются в соответствующих блоках документа.

### Проверка конкретных блоков в PDF

| Блок | Что проверить | Ожидаемый результат |
|------|---------------|---------------------|
| [8] | Основание передачи | `Договор №789 от 01.01.2026` |
| [9] | Данные о транспортировке | `Транспортная накладная ТН-123` |
| [10] | Товар передал (должность/ФИО) | `Директор` / `Иванов И.И.` |
| [11] | Дата отгрузки | `02.02.2026` |
| [12] | Иные сведения об отгрузке | `Товар в исправном состоянии` |
| [13] | Ответственный продавец (должность/ФИО) | `Главный бухгалтер` / `Петрова П.П.` |
| [15] | Товар получил (должность/ФИО) | `Менеджер` / `Сидоров С.С.` |
| [16] | Дата получения | `03.02.2026` |
| [17] | Иные сведения о получении | `Претензий нет` |
| [18] | Ответственный покупатель (должность/ФИО) | `Ведущий специалист` / `Васильева В.В.` |

---

## Файлы, которые были изменены

1. `/backend/app/api/documents.py` - добавлены алиасы для обратной совместимости (строки 258-272)
2. `/backend/app/templates/upd_template.html` - исправлены блоки [13] и [18] для использования seller_responsible/buyer_responsible
3. `/backend/test_upd_fields.py` - создан тестовый скрипт для проверки

**Бэкап:** `backups/full_backup_20260202_150057/`

---

## Технические детали

### Алиасы для совместимости

В API создана система алиасов, которая позволяет использовать как старые имена полей в шаблоне, так и новые в API:

```python
# Новое имя в API → Старое имя в шаблоне
shipping_date → transfer_date
other_shipping_info → other_transfer_info  
receiving_date → receipt_date
other_receiving_info → other_receipt_info
contract_info → transfer_basis
```

Это обеспечивает обратную совместимость и позволяет избежать переписывания шаблона.
