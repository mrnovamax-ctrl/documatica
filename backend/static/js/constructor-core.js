/**
 * CONSTRUCTOR CORE v1.0
 * Базовые функции для всех конструкторов документов
 * 
 * Зависимости: jQuery, Flatpickr
 */

const ConstructorCore = (function($) {
    'use strict';
    
    // ============================================
    // CONFIGURATION
    // ============================================
    const config = {
        previewDebounceMs: 1000,
        toastDurationMs: 4000,
        datepickerLocale: 'ru',
        datepickerFormat: 'd.m.Y',
        currencyLocale: 'ru-RU',
        currencyCode: 'RUB'
    };
    
    // ============================================
    // NOTIFICATIONS
    // ============================================
    
    /**
     * Показать уведомление
     * @param {string} type - success, danger, warning, info
     * @param {string} message - текст сообщения
     * @param {number} duration - время показа в мс
     */
    function showNotification(type, message, duration) {
        const toast = $(`
            <div class="toast-v12 ${type}">
                <span>${message}</span>
            </div>
        `);
        $('body').append(toast);
        
        setTimeout(() => {
            toast.fadeOut(300, function() { 
                $(this).remove(); 
            });
        }, duration || config.toastDurationMs);
    }
    
    // ============================================
    // CURRENCY FORMATTING
    // ============================================
    
    /**
     * Форматировать сумму в валюте
     * @param {number} amount - сумма
     * @param {string} currency - код валюты
     * @returns {string} - отформатированная сумма
     */
    function formatCurrency(amount, currency) {
        return new Intl.NumberFormat(config.currencyLocale, {
            style: 'currency',
            currency: currency || config.currencyCode,
            minimumFractionDigits: 2
        }).format(amount);
    }
    
    /**
     * Форматировать число
     * @param {number} num - число
     * @param {number} decimals - количество знаков после запятой
     * @returns {string} - отформатированное число
     */
    function formatNumber(num, decimals) {
        return new Intl.NumberFormat(config.currencyLocale, {
            minimumFractionDigits: decimals || 2,
            maximumFractionDigits: decimals || 2
        }).format(num);
    }
    
    // ============================================
    // DATE UTILITIES
    // ============================================
    
    /**
     * Инициализировать datepicker на элементах
     * @param {string} selector - CSS селектор
     * @param {object} options - дополнительные опции flatpickr
     */
    function initDatePickers(selector, options) {
        const defaults = {
            locale: config.datepickerLocale,
            dateFormat: config.datepickerFormat,
            allowInput: true
        };
        
        flatpickr(selector || '.date-picker', $.extend({}, defaults, options || {}));
    }
    
    /**
     * Получить сегодняшнюю дату в формате ДД.ММ.ГГГГ
     * @returns {string}
     */
    function getTodayFormatted() {
        return new Date().toLocaleDateString('ru-RU');
    }
    
    /**
     * Конвертировать дату из ДД.ММ.ГГГГ в ГГГГ-ММ-ДД (ISO)
     * @param {string} dateStr - дата в формате ДД.ММ.ГГГГ
     * @returns {string} - дата в ISO формате
     */
    function dateToISO(dateStr) {
        if (!dateStr) return new Date().toISOString().split('T')[0];
        const parts = dateStr.split('.');
        if (parts.length === 3) {
            return `${parts[2]}-${parts[1]}-${parts[0]}`;
        }
        return dateStr;
    }
    
    /**
     * Конвертировать дату из ГГГГ-ММ-ДД (ISO) в ДД.ММ.ГГГГ
     * @param {string} isoDate - дата в ISO формате
     * @returns {string} - дата в формате ДД.ММ.ГГГГ
     */
    function dateFromISO(isoDate) {
        if (!isoDate) return '';
        const parts = isoDate.split('-');
        if (parts.length === 3) {
            return `${parts[2]}.${parts[1]}.${parts[0]}`;
        }
        return isoDate;
    }
    
    // ============================================
    // INN/COMPANY SEARCH
    // ============================================
    
    /**
     * Поиск организации по ИНН через DaData
     * @param {string} inn - ИНН организации
     * @returns {Promise<object|null>} - данные организации или null
     */
    async function searchCompanyByINN(inn) {
        if (!inn || inn.length < 10) {
            throw new Error('Введите корректный ИНН (10 или 12 цифр)');
        }
        
        try {
            const response = await fetch(`/api/v1/dadata/suggest/party?query=${inn}`);
            
            if (!response.ok) {
                throw new Error('Ошибка сервера');
            }
            
            const data = await response.json();
            
            if (data.suggestions && data.suggestions.length > 0) {
                const company = data.suggestions[0];
                return {
                    name: company.value,
                    inn: company.data.inn,
                    kpp: company.data.kpp || '',
                    ogrn: company.data.ogrn || '',
                    address: company.data.address?.value || '',
                    management: company.data.management?.name || '',
                    type: company.data.type // LEGAL, INDIVIDUAL
                };
            }
            
            return null;
        } catch (error) {
            throw new Error('Ошибка поиска: ' + error.message);
        }
    }
    
    /**
     * Инициализировать кнопку поиска по ИНН
     * @param {string} btnSelector - селектор кнопки
     * @param {string} innInputSelector - селектор поля ИНН
     * @param {object} fieldMapping - маппинг полей {name: '#selector', kpp: '#selector', ...}
     * @param {function} onSuccess - callback при успехе
     */
    function initINNSearch(btnSelector, innInputSelector, fieldMapping, onSuccess) {
        $(btnSelector).on('click', async function() {
            const inn = $(innInputSelector).val();
            const btn = $(this);
            const originalHtml = btn.html();
            
            btn.prop('disabled', true).html(`
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin">
                    <path d="M21 12a9 9 0 11-6.219-8.56"/>
                </svg>
            `);
            
            try {
                const company = await searchCompanyByINN(inn);
                
                if (company) {
                    // Заполнить поля
                    if (fieldMapping.name) $(fieldMapping.name).val(company.name);
                    if (fieldMapping.inn) $(fieldMapping.inn).val(company.inn);
                    if (fieldMapping.kpp) $(fieldMapping.kpp).val(company.kpp);
                    if (fieldMapping.ogrn) $(fieldMapping.ogrn).val(company.ogrn);
                    if (fieldMapping.address) $(fieldMapping.address).val(company.address);
                    if (fieldMapping.director) $(fieldMapping.director).val(company.management);
                    
                    showNotification('success', 'Данные найдены');
                    
                    if (typeof onSuccess === 'function') {
                        onSuccess(company);
                    }
                } else {
                    showNotification('danger', 'Организация не найдена');
                }
            } catch (error) {
                showNotification('danger', error.message);
            } finally {
                btn.prop('disabled', false).html(originalHtml);
            }
        });
    }
    
    // ============================================
    // BANK SEARCH
    // ============================================
    
    /**
     * Поиск банка по БИК
     * @param {string} bik - БИК банка
     * @returns {Promise<object|null>}
     */
    async function searchBankByBIK(bik) {
        if (!bik || bik.length !== 9) {
            throw new Error('Введите корректный БИК (9 цифр)');
        }
        
        try {
            const response = await fetch(`/api/v1/dadata/suggest/bank?query=${bik}`);
            
            if (!response.ok) {
                throw new Error('Ошибка сервера');
            }
            
            const data = await response.json();
            
            if (data.suggestions && data.suggestions.length > 0) {
                const bank = data.suggestions[0];
                return {
                    name: bank.value,
                    bik: bank.data.bic,
                    correspondentAccount: bank.data.correspondent_account || '',
                    address: bank.data.address?.value || ''
                };
            }
            
            return null;
        } catch (error) {
            throw new Error('Ошибка поиска: ' + error.message);
        }
    }
    
    // ============================================
    // PRODUCTS TABLE
    // ============================================
    
    let productRowCount = 1;
    
    /**
     * Получить HTML шаблона строки товара
     * @param {number} rowNum - номер строки
     * @param {array} units - список единиц измерения
     * @returns {string} - HTML код строки
     */
    function getProductRowHtml(rowNum, units) {
        const defaultUnits = units || ['шт', 'усл', 'ч', 'кг', 'л', 'м', 'м2', 'м3'];
        const unitOptions = defaultUnits.map(u => `<option value="${u}">${u}</option>`).join('');
        
        return `
            <div class="product-row-v12" data-row="${rowNum}">
              <div class="product-grid">
                <div class="form-group-v12">
                  <label class="form-label-v12">Наименование *</label>
                  <input type="text" class="form-input-v12 product-name" placeholder="Название товара или услуги" required>
                </div>
                <div class="form-group-v12">
                  <label class="form-label-v12">Кол-во</label>
                  <input type="number" class="form-input-v12 product-qty" value="1" min="0.01" step="0.01">
                </div>
                <div class="form-group-v12">
                  <label class="form-label-v12">Ед. изм.</label>
                  <select class="form-select-v12 product-unit">
                    ${unitOptions}
                  </select>
                </div>
                <div class="form-group-v12">
                  <label class="form-label-v12">Цена</label>
                  <input type="number" class="form-input-v12 product-price" value="0" min="0" step="0.01">
                </div>
                <div class="form-group-v12" style="align-self: end;">
                  <button type="button" class="remove-btn remove-product" title="Удалить">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
                  </button>
                </div>
              </div>
            </div>
        `;
    }
    
    /**
     * Инициализировать таблицу товаров
     * @param {object} options - опции
     *   containerSelector: '#products-container'
     *   addBtnSelector: '#add-product'
     *   onCalculate: callback для пересчета
     *   units: массив единиц измерения
     */
    function initProductsTable(options) {
        const opts = $.extend({
            containerSelector: '#products-container',
            addBtnSelector: '#add-product',
            onCalculate: null,
            units: ['шт', 'усл', 'ч', 'кг', 'л', 'м', 'м2', 'м3']
        }, options);
        
        const container = $(opts.containerSelector);
        
        // Добавить строку
        $(opts.addBtnSelector).on('click', function() {
            productRowCount++;
            container.append(getProductRowHtml(productRowCount, opts.units));
            
            if (typeof opts.onCalculate === 'function') {
                opts.onCalculate();
            }
        });
        
        // Удалить строку
        $(document).on('click', '.remove-product', function() {
            if ($('.product-row-v12').length > 1) {
                $(this).closest('.product-row-v12').remove();
                if (typeof opts.onCalculate === 'function') {
                    opts.onCalculate();
                }
            } else {
                showNotification('danger', 'Должна остаться хотя бы одна позиция');
            }
        });
        
        // Пересчет при изменении
        $(document).on('input change', '.product-qty, .product-price', function() {
            if (typeof opts.onCalculate === 'function') {
                opts.onCalculate();
            }
        });
    }
    
    /**
     * Собрать данные товаров из таблицы
     * @param {object} vatConfig - {rate: '20', type: 'on-top'}
     * @returns {array} - массив товаров
     */
    function collectProductsData(vatConfig) {
        const items = [];
        let rowNum = 1;
        
        const vatRate = vatConfig?.rate || '20';
        const vatType = vatConfig?.type || 'on-top';
        
        $('.product-row-v12').each(function() {
            const qty = parseFloat($(this).find('.product-qty').val()) || 0;
            const price = parseFloat($(this).find('.product-price').val()) || 0;
            
            let amountWithoutVat, vatAmount, amountWithVat;
            let vatRateStr = 'Без НДС';
            
            if (vatRate !== 'none' && vatRate !== '0') {
                vatRateStr = vatRate + '%';
                const vatPercent = parseFloat(vatRate) / 100;
                
                if (vatType === 'included') {
                    amountWithVat = qty * price;
                    amountWithoutVat = amountWithVat / (1 + vatPercent);
                    vatAmount = amountWithVat - amountWithoutVat;
                } else {
                    amountWithoutVat = qty * price;
                    vatAmount = amountWithoutVat * vatPercent;
                    amountWithVat = amountWithoutVat + vatAmount;
                }
            } else {
                amountWithoutVat = qty * price;
                vatAmount = 0;
                amountWithVat = amountWithoutVat;
                vatRateStr = 'Без НДС';
            }
            
            items.push({
                row_number: rowNum++,
                name: $(this).find('.product-name').val() || 'Товар',
                unit_name: $(this).find('.product-unit').val() || 'шт',
                quantity: qty,
                price: price,
                amount_without_vat: amountWithoutVat,
                vat_rate: vatRateStr,
                vat_amount: vatAmount,
                amount_with_vat: amountWithVat
            });
        });
        
        return items;
    }
    
    // ============================================
    // TOTALS CALCULATION
    // ============================================
    
    /**
     * Рассчитать итоги по товарам
     * @param {object} vatConfig - {rate: '20', type: 'on-top'}
     * @param {object} selectors - {withoutVat: '#id', vat: '#id', withVat: '#id'}
     */
    function calculateTotals(vatConfig, selectors) {
        let totalWithoutVat = 0;
        let totalVat = 0;
        
        const vatRate = vatConfig?.rate || '20';
        const vatType = vatConfig?.type || 'on-top';
        
        $('.product-row-v12').each(function() {
            const qty = parseFloat($(this).find('.product-qty').val()) || 0;
            const price = parseFloat($(this).find('.product-price').val()) || 0;
            
            let subtotal, vat;
            
            if (vatRate !== 'none' && vatRate !== '0') {
                const vatPercent = parseFloat(vatRate) / 100;
                
                if (vatType === 'included') {
                    const total = qty * price;
                    subtotal = total / (1 + vatPercent);
                    vat = total - subtotal;
                } else {
                    subtotal = qty * price;
                    vat = subtotal * vatPercent;
                }
            } else {
                subtotal = qty * price;
                vat = 0;
            }
            
            totalWithoutVat += subtotal;
            totalVat += vat;
        });
        
        const sels = selectors || {
            withoutVat: '#total-without-vat',
            vat: '#total-vat',
            withVat: '#total-with-vat'
        };
        
        $(sels.withoutVat).text(formatCurrency(totalWithoutVat));
        $(sels.vat).text(formatCurrency(totalVat));
        $(sels.withVat).text(formatCurrency(totalWithoutVat + totalVat));
        
        return {
            withoutVat: totalWithoutVat,
            vat: totalVat,
            withVat: totalWithoutVat + totalVat
        };
    }
    
    // ============================================
    // PREVIEW
    // ============================================
    
    let previewDebounceTimer = null;
    
    /**
     * Инициализировать live-preview
     * @param {object} options
     *   iframeSelector: '#sidebar-preview-iframe'
     *   refreshBtnSelector: '#refresh-preview'
     *   previewBtnSelector: '#preview-btn'
     *   apiEndpoint: '/api/v1/documents/xxx/preview'
     *   collectDataFn: function that returns request data
     */
    function initPreview(options) {
        const opts = $.extend({
            iframeSelector: '#sidebar-preview-iframe',
            refreshBtnSelector: '#refresh-preview',
            previewBtnSelector: '#preview-btn',
            apiEndpoint: '',
            collectDataFn: null
        }, options);
        
        if (!opts.apiEndpoint || !opts.collectDataFn) {
            console.warn('Preview: apiEndpoint and collectDataFn are required');
            return;
        }
        
        // Загрузить превью в iframe
        async function loadPreview() {
            const iframe = document.querySelector(opts.iframeSelector);
            if (!iframe) return;
            
            const container = iframe.parentElement;
            const requestData = opts.collectDataFn();
            
            try {
                const response = await fetch(opts.apiEndpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(requestData)
                });
                
                if (response.ok) {
                    const html = await response.text();
                    iframe.srcdoc = html;
                    
                    iframe.onload = function() {
                        const containerWidth = container.clientWidth;
                        const docWidth = 1150;
                        const scale = containerWidth / docWidth;
                        
                        let docHeight = 850;
                        try {
                            const doc = iframe.contentDocument || iframe.contentWindow.document;
                            docHeight = Math.max(doc.body.scrollHeight, doc.documentElement.scrollHeight, 850);
                        } catch(e) {}
                        
                        iframe.style.width = docWidth + 'px';
                        iframe.style.height = docHeight + 'px';
                        iframe.style.transform = 'scale(' + scale + ')';
                        container.style.height = (docHeight * scale) + 'px';
                    };
                }
            } catch (error) {
                console.log('Preview error:', error);
            }
        }
        
        // Debounced update
        function updatePreview() {
            clearTimeout(previewDebounceTimer);
            previewDebounceTimer = setTimeout(loadPreview, config.previewDebounceMs);
        }
        
        // Кнопка обновить
        $(opts.refreshBtnSelector).on('click', loadPreview);
        
        // Кнопка открыть в новом окне
        $(opts.previewBtnSelector).on('click', async function() {
            const requestData = opts.collectDataFn();
            try {
                const response = await fetch(opts.apiEndpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(requestData)
                });
                if (response.ok) {
                    const html = await response.text();
                    const previewWindow = window.open('', '_blank');
                    previewWindow.document.write(html);
                    previewWindow.document.close();
                }
            } catch (error) {
                showNotification('danger', 'Ошибка предпросмотра: ' + error.message);
            }
        });
        
        // Live update on input change
        $(document).on('input change', 'input, select, textarea', function() {
            updatePreview();
        });
        
        // Initial load
        setTimeout(loadPreview, 500);
        
        return {
            load: loadPreview,
            update: updatePreview
        };
    }
    
    // ============================================
    // FORM GENERATION
    // ============================================
    
    /**
     * Инициализировать генерацию документа
     * @param {object} options
     *   formSelector: '#upd-form'
     *   apiEndpoint: '/api/v1/documents/xxx/generate'
     *   collectDataFn: function that returns request data
     *   filename: function(data) that returns filename
     */
    function initFormGeneration(options) {
        const opts = $.extend({
            formSelector: '#form',
            apiEndpoint: '',
            collectDataFn: null,
            filename: null
        }, options);
        
        $(opts.formSelector).on('submit', async function(e) {
            e.preventDefault();
            
            if (!this.checkValidity()) {
                this.reportValidity();
                return;
            }
            
            const submitBtn = $(this).find('button[type="submit"]');
            const originalHtml = submitBtn.html();
            submitBtn.prop('disabled', true).html(`
                <span class="spin" style="display:inline-block;width:16px;height:16px;border:2px solid white;border-top-color:transparent;border-radius:50%;margin-right:8px;"></span>
                Генерация...
            `);
            
            try {
                const requestData = opts.collectDataFn();
                
                const response = await fetch(opts.apiEndpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(requestData)
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    let errorMessage = 'Ошибка генерации';
                    if (typeof error.detail === 'string') {
                        errorMessage = error.detail;
                    } else if (Array.isArray(error.detail)) {
                        errorMessage = error.detail.map(e => e.msg).join('; ');
                    }
                    throw new Error(errorMessage);
                }
                
                const contentType = response.headers.get('content-type');
                
                if (contentType && contentType.includes('text/html')) {
                    // HTML - открыть для печати
                    const html = await response.text();
                    const printWindow = window.open('', '_blank');
                    printWindow.document.write(html);
                    printWindow.document.close();
                    printWindow.onload = function() {
                        setTimeout(() => printWindow.print(), 500);
                    };
                    showNotification('success', 'Документ готов к печати');
                } else {
                    // PDF - скачать
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = typeof opts.filename === 'function' ? opts.filename(requestData) : 'document.pdf';
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    a.remove();
                    showNotification('success', 'Документ успешно сгенерирован!');
                }
                
            } catch (error) {
                console.error('Error:', error);
                showNotification('danger', 'Ошибка: ' + error.message);
            } finally {
                submitBtn.prop('disabled', false).html(originalHtml);
            }
        });
    }
    
    // ============================================
    // DRAFTS & TEMPLATES
    // ============================================
    
    /**
     * Сохранить черновик в localStorage
     * @param {string} key - ключ для сохранения
     * @param {function} collectDataFn - функция сбора данных
     */
    function initDraftSave(key, collectDataFn, btnSelector) {
        $(btnSelector || '#save-draft').on('click', function() {
            const formData = collectDataFn();
            localStorage.setItem(key, JSON.stringify(formData));
            showNotification('success', 'Черновик сохранен!');
        });
    }
    
    /**
     * Загрузить черновик из localStorage
     * @param {string} key - ключ
     * @returns {object|null}
     */
    function loadDraft(key) {
        const saved = localStorage.getItem(key);
        if (saved) {
            try {
                return JSON.parse(saved);
            } catch(e) {
                return null;
            }
        }
        return null;
    }
    
    /**
     * Инициализировать сохранение как шаблон
     * @param {function} collectDataFn - функция сбора данных
     * @param {string} docType - тип документа (upd, invoice, etc.)
     * @param {function} nameGeneratorFn - функция генерации имени шаблона
     */
    function initTemplateSave(collectDataFn, docType, nameGeneratorFn, btnSelector) {
        $(btnSelector || '#save-template').on('click', async function() {
            const formData = collectDataFn();
            const templateName = typeof nameGeneratorFn === 'function' 
                ? nameGeneratorFn(formData) 
                : 'Шаблон ' + new Date().toLocaleDateString('ru-RU');
            
            const btn = $(this);
            btn.prop('disabled', true);
            
            try {
                const response = await fetch('/api/v1/templates/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({
                        name: templateName,
                        doc_type: docType,
                        data: formData
                    })
                });
                
                if (response.ok) {
                    showNotification('success', 'Шаблон успешно сохранен!');
                } else {
                    const err = await response.json();
                    showNotification('danger', err.detail || 'Ошибка сохранения шаблона');
                }
            } catch (error) {
                showNotification('danger', 'Ошибка: ' + error.message);
            } finally {
                btn.prop('disabled', false);
            }
        });
    }
    
    // ============================================
    // AI ANALYSIS
    // ============================================
    
    /**
     * Инициализировать ИИ анализ
     * @param {object} options
     *   btnSelector: '#ai-analyze-btn'
     *   resultSelector: '#ai-analysis-result'
     *   apiEndpoint: '/api/v1/ai/analyze-xxx'
     *   collectDataFn: function that returns data to analyze
     */
    function initAIAnalysis(options) {
        const opts = $.extend({
            btnSelector: '#ai-analyze-btn',
            resultSelector: '#ai-analysis-result',
            apiEndpoint: '',
            collectDataFn: null
        }, options);
        
        $(opts.btnSelector).on('click', async function() {
            const btn = $(this);
            const resultContainer = $(opts.resultSelector);
            
            // Loading state
            btn.prop('disabled', true);
            btn.html(`
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin">
                    <path d="M21 12a9 9 0 11-6.219-8.56"/>
                </svg>
                Анализ...
            `);
            
            resultContainer.html(`
                <div class="ai-analysis-loading-v12">
                    <div class="spinner"></div>
                    <span>ИИ анализирует документ...</span>
                </div>
            `);
            
            try {
                const analysisData = opts.collectDataFn();
                
                const response = await fetch(opts.apiEndpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify(analysisData)
                });
                
                if (!response.ok) {
                    const err = await response.json();
                    throw new Error(err.detail || 'Ошибка анализа');
                }
                
                const result = await response.json();
                renderAnalysisResult(resultContainer, result);
                
            } catch (error) {
                resultContainer.html(`
                    <div class="ai-result-v12">
                        <div class="ai-section error">
                            <div class="ai-section-title">Ошибка</div>
                            <p>${error.message}</p>
                        </div>
                    </div>
                `);
            } finally {
                btn.prop('disabled', false);
                btn.html(`
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="11" cy="11" r="8"/>
                        <path d="m21 21-4.3-4.3"/>
                    </svg>
                    Анализировать
                `);
            }
        });
    }
    
    function renderAnalysisResult(container, result) {
        let html = '<div class="ai-result-v12">';
        
        // Errors
        if (result.errors && result.errors.length > 0) {
            html += `
                <div class="ai-section error">
                    <div class="ai-section-title">Критические ошибки (${result.errors.length})</div>
                    <ul>
                        ${result.errors.map(e => `<li><span class="highlight-error">${e.field || 'Документ'}</span>: ${e.message}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        // Warnings
        if (result.warnings && result.warnings.length > 0) {
            html += `
                <div class="ai-section warning">
                    <div class="ai-section-title">Предупреждения (${result.warnings.length})</div>
                    <ul>
                        ${result.warnings.map(w => `<li><span class="highlight-warning">${w.field || 'Документ'}</span>: ${w.message}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        // Suggestions
        if (result.suggestions && result.suggestions.length > 0) {
            html += `
                <div class="ai-section">
                    <div class="ai-section-title">Рекомендации (${result.suggestions.length})</div>
                    <ul>
                        ${result.suggestions.map(s => `<li><strong>${s.field || 'Общее'}</strong>: ${s.message}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        // Success
        if ((!result.errors || result.errors.length === 0) && 
            (!result.warnings || result.warnings.length === 0) &&
            (!result.suggestions || result.suggestions.length === 0)) {
            html += `
                <div class="ai-section success">
                    <div class="ai-section-title">Проверка пройдена</div>
                    <p>Документ заполнен корректно. Ошибок не обнаружено.</p>
                </div>
            `;
        }
        
        // Summary
        if (result.summary) {
            html += `
                <div class="ai-section">
                    <div class="ai-section-title">Заключение</div>
                    <p>${result.summary}</p>
                </div>
            `;
        }
        
        html += '</div>';
        container.html(html);
    }
    
    // ============================================
    // AUTO NUMBER
    // ============================================
    
    /**
     * Инициализировать автонумерацию
     * @param {string} btnSelector - кнопка
     * @param {string} inputSelector - поле номера
     * @param {function} callback - callback после установки номера
     */
    function initAutoNumber(btnSelector, inputSelector, callback) {
        $(btnSelector).on('click', function() {
            const num = Math.floor(Math.random() * 1000) + 1;
            $(inputSelector).val(num);
            
            if (typeof callback === 'function') {
                callback(num);
            }
        });
    }
    
    // ============================================
    // PUBLIC API
    // ============================================
    
    return {
        // Config
        config: config,
        
        // Notifications
        showNotification: showNotification,
        
        // Formatting
        formatCurrency: formatCurrency,
        formatNumber: formatNumber,
        
        // Dates
        initDatePickers: initDatePickers,
        getTodayFormatted: getTodayFormatted,
        dateToISO: dateToISO,
        dateFromISO: dateFromISO,
        
        // Company search
        searchCompanyByINN: searchCompanyByINN,
        initINNSearch: initINNSearch,
        searchBankByBIK: searchBankByBIK,
        
        // Products
        initProductsTable: initProductsTable,
        collectProductsData: collectProductsData,
        getProductRowHtml: getProductRowHtml,
        
        // Totals
        calculateTotals: calculateTotals,
        
        // Preview
        initPreview: initPreview,
        
        // Form
        initFormGeneration: initFormGeneration,
        
        // Drafts & Templates
        initDraftSave: initDraftSave,
        loadDraft: loadDraft,
        initTemplateSave: initTemplateSave,
        
        // AI Analysis
        initAIAnalysis: initAIAnalysis,
        
        // Auto number
        initAutoNumber: initAutoNumber
    };
    
})(jQuery);

// Глобальный алиас для удобства
window.CC = ConstructorCore;
