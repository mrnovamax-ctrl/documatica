/**
 * Akt Constructor - Documatica v12.0
 * Адаптировано из upd-constructor для работы с Актами выполненных работ
 */

$(document).ready(function() {
    // Отключаем transitions при инициализации страницы
    document.body.classList.add('no-transitions');
    setTimeout(function() {
        document.body.classList.remove('no-transitions');
    }, 100);
    
    // Initialize date picker
    flatpickr('.date-picker', {
        dateFormat: 'd.m.Y',
        allowInput: true,
        locale: {
            firstDayOfWeek: 1,
            weekdays: {
                shorthand: ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'],
                longhand: ['Воскресенье', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']
            },
            months: {
                shorthand: ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'],
                longhand: ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
            }
        }
    });
    
    // Устанавливаем сегодняшнюю дату
    setTimeout(function() {
        const aktDateEl = document.getElementById('akt-date');
        if (aktDateEl && aktDateEl._flatpickr) {
            aktDateEl._flatpickr.setDate(new Date());
            
            document.getElementById('akt-date-icon').addEventListener('click', function() {
                aktDateEl._flatpickr.open();
            });
        }
        
        const contractDateIcon = document.getElementById('contract-date-icon');
        const contractDateEl = document.getElementById('contract-date');
        if (contractDateIcon && contractDateEl && contractDateEl._flatpickr) {
            contractDateIcon.addEventListener('click', function() {
                contractDateEl._flatpickr.open();
            });
        }
    }, 100);
    
    // API URL
    const API_URL = window.AKT_CONFIG?.apiUrl || '/api/v1';
    
    // Настраиваем интерфейс для авторизованного пользователя
    (function() {
        const token = localStorage.getItem('documatica_token');
        const user = JSON.parse(localStorage.getItem('documatica_user') || '{}');
        
        if (token && user) {
            if (user.name) {
                const initials = user.name.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2);
                $('#user-initials').text(initials);
                $('#user-name').text(user.name);
            }
            if (user.email) {
                $('#user-email').text(user.email);
            }
        } else {
            $('#user-initials').text('Г');
            $('#user-name').text('Гость');
            $('#user-email').text('Войдите для сохранения');
        }
        
        $('#logout-btn').on('click', function(e) {
            e.preventDefault();
            localStorage.removeItem('documatica_token');
            localStorage.removeItem('documatica_user');
            window.location.href = '/';
        });
    })();
    
    // ID редактируемого документа
    const editDocumentId = window.AKT_CONFIG?.editDocumentId || '';
    
    // Загрузка данных редактируемого документа
    if (editDocumentId) {
        (async function() {
            try {
                const response = await fetch(`${API_URL}/documents/akt/${editDocumentId}/data`, { credentials: 'include' });
                if (response.ok) {
                    const result = await response.json();
                    if (result.success && result.data) {
                        setTimeout(function() {
                            loadFormDataForEdit(result.data);
                            toastSuccess('Документ загружен для редактирования');
                        }, 500);
                    }
                }
            } catch (error) {
                console.error('Error loading document:', error);
            }
        })();
    }
    
    // Storage for loaded data
    let organizationsList = [];
    let contractorsList = [];
    let productsList = [];
    let selectedExecutorOrg = null;  // Для хранения выбранной организации (подпись, печать)
    
    // Определение типа организации по ИНН (10 цифр = ООО, 12 цифр = ИП)
    function getOrgTypeByInn(inn) {
        if (!inn) return 'ooo';
        const cleanInn = inn.toString().replace(/\D/g, '');
        return cleanInn.length === 12 ? 'ip' : 'ooo';
    }

    // ============== DADATA АВТОЗАПОЛНЕНИЕ ==============
    
    async function searchCompanyByInn(inn, targetType) {
        const innInputId = `${targetType}-inn`;
        
        if (!inn || inn.length < 10) {
            showInputError(innInputId, 'ИНН должен содержать минимум 10 символов');
            return null;
        }
        
        clearInputError(innInputId);
        const loadingEl = $(`#${targetType}-inn-loading`);
        const searchBtn = $(`#${targetType}-inn-search`);
        
        try {
            loadingEl.removeClass('d-none');
            searchBtn.prop('disabled', true);
            
            const response = await fetch(`${API_URL}/dadata/company/by-inn`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ inn: inn.trim(), branch_type: 'MAIN' })
            });
            
            if (!response.ok) {
                if (response.status === 404) {
                    showInputError(innInputId, 'Компания с таким ИНН не найдена');
                    return null;
                }
                throw new Error('Ошибка при поиске');
            }
            
            return await response.json();
            
        } catch (error) {
            console.error('Dadata search error:', error);
            showInputError(innInputId, 'Ошибка при поиске компании');
            return null;
        } finally {
            loadingEl.addClass('d-none');
            searchBtn.prop('disabled', false);
        }
    }
    
    function fillExecutorFields(company) {
        if (!company) return;
        
        $('#executor-name').val(company.name || '');
        $('#executor-inn').val(company.inn || '');
        $('#executor-kpp').val(company.kpp || '');
        $('#executor-address').val(company.address_full || company.address || '');
        
        $('#executor-name, #executor-inn, #executor-kpp, #executor-address').addClass('bg-success-100');
        setTimeout(() => {
            $('#executor-name, #executor-inn, #executor-kpp, #executor-address').removeClass('bg-success-100');
        }, 2000);
        
        toastSuccess(`Данные компании "${company.name}" загружены`);
        updatePreview();
    }
    
    function fillCustomerFields(company) {
        if (!company) return;
        
        $('#customer-name').val(company.name || '');
        $('#customer-inn').val(company.inn || '');
        $('#customer-kpp').val(company.kpp || '');
        $('#customer-address').val(company.address_full || company.address || '');
        
        $('#customer-name, #customer-inn, #customer-kpp, #customer-address').addClass('bg-success-100');
        setTimeout(() => {
            $('#customer-name, #customer-inn, #customer-kpp, #customer-address').removeClass('bg-success-100');
        }, 2000);
        
        toastSuccess(`Данные компании "${company.name}" загружены`);
        updatePreview();
    }
    
    $('#executor-inn-search').on('click', async function() {
        const inn = $('#executor-inn').val();
        const company = await searchCompanyByInn(inn, 'executor');
        if (company) {
            fillExecutorFields(company);
        }
    });
    
    $('#customer-inn-search').on('click', async function() {
        const inn = $('#customer-inn').val();
        const company = await searchCompanyByInn(inn, 'customer');
        if (company) {
            fillCustomerFields(company);
        }
    });
    
    // ============== MODALS ==============
    
    async function loadOrganizationsModal(searchTerm = '') {
        try {
            const response = await fetch(`${API_URL}/organizations`);
            organizationsList = await response.json();
        } catch (error) {
            console.log('API unavailable, using localStorage');
            organizationsList = JSON.parse(localStorage.getItem('organizations') || '[]');
        }
        renderOrganizationsModal(searchTerm);
    }
    
    function renderOrganizationsModal(searchTerm = '') {
        const container = $('#organizations-modal-list');
        const noMessage = $('#no-organizations-message');
        
        let filtered = organizationsList;
        if (searchTerm) {
            const term = searchTerm.toLowerCase();
            filtered = organizationsList.filter(o => 
                o.name.toLowerCase().includes(term) || 
                o.inn.includes(term)
            );
        }
        
        if (filtered.length === 0) {
            container.hide();
            noMessage.show();
            return;
        }
        
        noMessage.hide();
        container.show();
        
        let html = '';
        filtered.forEach(org => {
            const logoHtml = org.logo_url 
                ? `<img src="${org.logo_url}" alt="${org.name}" style="max-width: 48px; max-height: 48px; object-fit: contain;">`
                : `<div class="w-48-px h-48-px bg-primary-100 rounded-circle d-flex justify-content-center align-items-center">
                     <iconify-icon icon="mdi:domain" class="text-primary-600 text-xl"></iconify-icon>
                   </div>`;
            
            html += `
                <div class="col-12 organization-item" data-id="${org.id}">
                    <div class="card radius-8 border-0 shadow-sm h-100" style="cursor: pointer; transition: all 0.2s;">
                        <div class="card-body p-20">
                            <div class="d-flex align-items-start justify-content-between">
                                <div class="flex-grow-1">
                                    <h6 class="fw-semibold mb-8">${org.name}</h6>
                                    <p class="text-secondary-light text-sm mb-6">ИНН: ${org.inn}</p>
                                    ${org.kpp ? `<p class="text-secondary-light text-sm mb-6">КПП: ${org.kpp}</p>` : ''}
                                    ${org.address ? `<p class="text-secondary-light text-sm mb-0">
                                        <iconify-icon icon="mdi:map-marker" class="me-1"></iconify-icon>${org.address}
                                    </p>` : ''}
                                </div>
                                <div class="d-flex align-items-center gap-2 ms-3" style="flex-shrink: 0;">
                                    ${logoHtml}
                                    <iconify-icon icon="mdi:chevron-right" class="text-xl text-secondary-light"></iconify-icon>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        container.html(html);
    }
    
    async function loadContractorsModal(searchTerm = '') {
        try {
            const response = await fetch(`${API_URL}/contractors`);
            contractorsList = await response.json();
        } catch (error) {
            console.log('API unavailable, using localStorage');
            contractorsList = JSON.parse(localStorage.getItem('contractors') || '[]');
        }
        renderContractorsModal(searchTerm);
    }
    
    function renderContractorsModal(searchTerm = '') {
        const container = $('#contractors-modal-list');
        const noMessage = $('#no-contractors-message');
        
        let filtered = contractorsList;
        if (searchTerm) {
            const term = searchTerm.toLowerCase();
            filtered = contractorsList.filter(c => 
                c.name.toLowerCase().includes(term) || 
                c.inn.includes(term)
            );
        }
        
        if (filtered.length === 0) {
            container.hide();
            noMessage.show();
            return;
        }
        
        noMessage.hide();
        container.show();
        
        let html = '';
        filtered.forEach(contractor => {
            const logoHtml = contractor.logo_url 
                ? `<img src="${contractor.logo_url}" alt="${contractor.name}" style="max-width: 48px; max-height: 48px; object-fit: contain;">`
                : `<div class="w-48-px h-48-px bg-success-100 rounded-circle d-flex justify-content-center align-items-center">
                     <iconify-icon icon="mdi:account-group" class="text-success-600 text-xl"></iconify-icon>
                   </div>`;
            
            html += `
                <div class="col-12 contractor-item" data-id="${contractor.id}">
                    <div class="card radius-8 border-0 shadow-sm h-100" style="cursor: pointer; transition: all 0.2s;">
                        <div class="card-body p-20">
                            <div class="d-flex align-items-start justify-content-between">
                                <div class="flex-grow-1">
                                    <h6 class="fw-semibold mb-8">${contractor.name}</h6>
                                    <p class="text-secondary-light text-sm mb-6">ИНН: ${contractor.inn}</p>
                                    ${contractor.kpp ? `<p class="text-secondary-light text-sm mb-6">КПП: ${contractor.kpp}</p>` : ''}
                                    ${contractor.address ? `<p class="text-secondary-light text-sm mb-0">
                                        <iconify-icon icon="mdi:map-marker" class="me-1"></iconify-icon>${contractor.address}
                                    </p>` : ''}
                                </div>
                                <div class="d-flex align-items-center gap-2 ms-3" style="flex-shrink: 0;">
                                    ${logoHtml}
                                    <iconify-icon icon="mdi:chevron-right" class="text-xl text-secondary-light"></iconify-icon>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        container.html(html);
    }
    
    async function loadProductsModal(searchTerm = '') {
        try {
            const response = await fetch(`${API_URL}/products`);
            productsList = await response.json();
        } catch (error) {
            productsList = JSON.parse(localStorage.getItem('products') || '[]');
        }
        renderProductsModal(searchTerm);
    }
    
    function renderProductsModal(searchTerm = '') {
        const container = $('#products-modal-list');
        const noMessage = $('#no-products-message');
        
        let filtered = productsList;
        if (searchTerm) {
            const term = searchTerm.toLowerCase();
            filtered = productsList.filter(p => 
                p.name.toLowerCase().includes(term) || 
                (p.sku && p.sku.toLowerCase().includes(term))
            );
        }
        
        if (filtered.length === 0) {
            container.hide();
            noMessage.show();
            return;
        }
        
        noMessage.hide();
        container.show();
        
        let html = '';
        filtered.forEach(product => {
            const typeLabel = product.type === 'service' ? 'Услуга' : 'Товар';
            const typeBadgeClass = product.type === 'service' ? 'bg-success-100 text-success-600' : 'bg-info-100 text-info-600';
            const price = product.price ? parseFloat(product.price).toLocaleString('ru-RU', {minimumFractionDigits: 2}) : '0,00';
            html += `
                <div class="card border mb-12 product-item" data-id="${product.id}" style="cursor: pointer;">
                    <div class="card-body p-16">
                        <div class="d-flex justify-content-between align-items-start">
                            <div class="flex-grow-1">
                                <span class="badge ${typeBadgeClass} mb-8">${typeLabel}</span>
                                <h6 class="mb-4">${product.name}</h6>
                                <p class="text-secondary-light small mb-0">
                                    ${product.sku ? 'Арт: ' + product.sku + ' | ' : ''}
                                    Ед: ${product.unit} | Цена: ${price} руб.
                                </p>
                            </div>
                            <iconify-icon icon="mdi:plus-circle" class="text-xl text-primary-600"></iconify-icon>
                        </div>
                    </div>
                </div>
            `;
        });
        container.html(html);
    }
    
    // Select organization from modal
    $(document).on('click', '.organization-item', function() {
        const id = $(this).data('id');
        const org = organizationsList.find(o => o.id === id);
        if (org) {
            // Сохраняем выбранную организацию для использования подписи и печати
            selectedExecutorOrg = org;
            
            document.body.classList.add('no-transitions');
            
            $('#executor-name').val(org.name);
            $('#executor-inn').val(org.inn);
            $('#executor-kpp').val(org.kpp || '');
            $('#executor-address').val(org.address || '');
            
            // Заполняем подписанта если есть
            if (org.director_name) {
                $('#executor-signatory').val(org.director_name);
            }
            
            bootstrap.Modal.getInstance(document.getElementById('selectCompanyModal')).hide();
            $('#save-executor-btn').removeClass('show');
            
            setTimeout(function() {
                document.body.classList.remove('no-transitions');
            }, 50);
            
            updatePreview();
        }
    });
    
    // Select contractor from modal
    $(document).on('click', '.contractor-item', function() {
        const id = $(this).data('id');
        const contractor = contractorsList.find(c => c.id === id);
        if (contractor) {
            document.body.classList.add('no-transitions');
            
            $('#customer-name').val(contractor.name);
            $('#customer-inn').val(contractor.inn);
            $('#customer-kpp').val(contractor.kpp || '');
            $('#customer-address').val(contractor.address || '');
            
            bootstrap.Modal.getInstance(document.getElementById('selectContractorModal')).hide();
            $('#save-customer-btn').removeClass('show');
            
            setTimeout(function() {
                document.body.classList.remove('no-transitions');
            }, 50);
            
            updatePreview();
        }
    });
    
    // Select product from modal
    $(document).on('click', '.product-item', function() {
        const id = $(this).data('id');
        const product = productsList.find(p => p.id === id);
        if (product) {
            addProductFromCatalog(product);
        }
    });
    
    // Modal events
    $('#selectCompanyModal').on('shown.bs.modal', function() {
        loadOrganizationsModal();
        $('#search-organization').val('').focus();
    });
    
    $('#selectContractorModal').on('shown.bs.modal', function() {
        loadContractorsModal();
        $('#search-contractor').val('').focus();
    });
    
    $('#selectProductModal').on('shown.bs.modal', function() {
        loadProductsModal();
        $('#search-product-modal').val('').focus();
    });
    
    $('#search-organization').on('input', function() {
        renderOrganizationsModal($(this).val());
    });
    
    $('#search-contractor').on('input', function() {
        renderContractorsModal($(this).val());
    });
    
    $('#search-product-modal').on('input', function() {
        renderProductsModal($(this).val());
    });
    
    // ============== PRODUCTS ==============
    
    let productRowCount = 1;
    
    function addProductFromCatalog(product) {
        productRowCount++;
        
        const newRow = `
            <div class="product-row card border radius-12 p-16 mb-16" data-row="${productRowCount}">
                <div class="row g-12 align-items-end">
                    <div class="col">
                        <label class="form-label fw-bold text-xs text-slate-600 text-uppercase" style="letter-spacing: 0.05em; margin-top: 16px; margin-bottom: 8px;">Наименование <span class="text-danger">*</span></label>
                        <input type="text" class="form-control product-name" value="${product.name}" required>
                    </div>
                    <div class="col-auto" style="width: 100px;">
                        <label class="form-label fw-bold text-xs text-slate-600 text-uppercase" style="letter-spacing: 0.05em; margin-top: 16px; margin-bottom: 8px;">Кол-во</label>
                        <input type="number" class="form-control product-qty" value="${product.qty || 1}" min="0.01" step="0.01">
                    </div>
                    <div class="col-auto" style="width: 110px;">
                        <label class="form-label fw-bold text-xs text-slate-600 text-uppercase" style="letter-spacing: 0.05em; margin-top: 16px; margin-bottom: 8px;">Ед. изм.</label>
                        <select class="form-select product-unit">
                            <option value="усл" ${product.unit === 'усл' ? 'selected' : ''}>усл</option>
                            <option value="шт" ${product.unit === 'шт' ? 'selected' : ''}>шт</option>
                            <option value="ч" ${product.unit === 'ч' ? 'selected' : ''}>ч</option>
                            <option value="кг" ${product.unit === 'кг' ? 'selected' : ''}>кг</option>
                            <option value="л" ${product.unit === 'л' ? 'selected' : ''}>л</option>
                            <option value="м" ${product.unit === 'м' ? 'selected' : ''}>м</option>
                            <option value="м2" ${product.unit === 'м2' ? 'selected' : ''}>м2</option>
                            <option value="м3" ${product.unit === 'м3' ? 'selected' : ''}>м3</option>
                        </select>
                    </div>
                    <div class="col-auto" style="width: 120px;">
                        <label class="form-label fw-bold text-xs text-slate-600 text-uppercase" style="letter-spacing: 0.05em; margin-top: 16px; margin-bottom: 8px;">Цена</label>
                        <input type="number" class="form-control product-price" value="${product.price || 0}" min="0" step="0.01">
                    </div>
                    <div class="col-auto" style="width: 120px;">
                        <label class="form-label fw-bold text-xs text-slate-600 text-uppercase" style="letter-spacing: 0.05em; margin-top: 16px; margin-bottom: 8px;">Сумма</label>
                        <input type="text" class="form-control product-total" value="0 ₽" readonly>
                    </div>
                    <div class="col-auto">
                        <button type="button" class="btn btn-outline-danger remove-product" title="Удалить">
                            <iconify-icon icon="mdi:trash-can-outline"></iconify-icon>
                        </button>
                    </div>
                </div>
            </div>
        `;
        $('#products-container').append(newRow);
        calculateTotals();
        updatePreview();
    }
    
    // Add product row
    $('#add-product').on('click', function() {
        productRowCount++;
        
        const newRow = `
            <div class="product-row card border radius-12 p-16 mb-16" data-row="${productRowCount}">
                <div class="row g-12 align-items-end">
                    <div class="col">
                        <label class="form-label fw-bold text-xs text-slate-600 text-uppercase" style="letter-spacing: 0.05em; margin-top: 16px; margin-bottom: 8px;">Наименование <span class="text-danger">*</span></label>
                        <input type="text" class="form-control product-name" placeholder="Название работы или услуги" required>
                    </div>
                    <div class="col-auto" style="width: 100px;">
                        <label class="form-label fw-bold text-xs text-slate-600 text-uppercase" style="letter-spacing: 0.05em; margin-top: 16px; margin-bottom: 8px;">Кол-во</label>
                        <input type="number" class="form-control product-qty" value="1" min="0.01" step="0.01">
                    </div>
                    <div class="col-auto" style="width: 110px;">
                        <label class="form-label fw-bold text-xs text-slate-600 text-uppercase" style="letter-spacing: 0.05em; margin-top: 16px; margin-bottom: 8px;">Ед. изм.</label>
                        <select class="form-select product-unit">
                            <option value="усл" selected>усл</option>
                            <option value="шт">шт</option>
                            <option value="ч">ч</option>
                            <option value="кг">кг</option>
                            <option value="л">л</option>
                            <option value="м">м</option>
                            <option value="м2">м2</option>
                            <option value="м3">м3</option>
                        </select>
                    </div>
                    <div class="col-auto" style="width: 120px;">
                        <label class="form-label fw-bold text-xs text-slate-600 text-uppercase" style="letter-spacing: 0.05em; margin-top: 16px; margin-bottom: 8px;">Цена</label>
                        <input type="number" class="form-control product-price" value="0" min="0" step="0.01">
                    </div>
                    <div class="col-auto" style="width: 120px;">
                        <label class="form-label fw-bold text-xs text-slate-600 text-uppercase" style="letter-spacing: 0.05em; margin-top: 16px; margin-bottom: 8px;">Сумма</label>
                        <input type="text" class="form-control product-total" value="0 ₽" readonly>
                    </div>
                    <div class="col-auto">
                        <button type="button" class="btn btn-outline-danger remove-product" title="Удалить">
                            <iconify-icon icon="mdi:trash-can-outline"></iconify-icon>
                        </button>
                    </div>
                </div>
            </div>
        `;
        $('#products-container').append(newRow);
    });
    
    // Remove product row
    $(document).on('click', '.remove-product', function() {
        const rows = $('.product-row');
        if (rows.length > 1) {
            $(this).closest('.product-row').remove();
            calculateTotals();
            updatePreview();
        } else {
            toastWarning('Должна быть хотя бы одна позиция');
        }
    });
    
    // Calculate totals on input
    $(document).on('input', '.product-qty, .product-price', function() {
        calculateTotals();
    });
    
    $('#default-vat, #default-vat-type').on('change', function() {
        calculateTotals();
    });
    
    function calculateTotals() {
        let totalAmount = 0;
        
        $('.product-row').each(function() {
            const qty = parseFloat($(this).find('.product-qty').val()) || 0;
            const price = parseFloat($(this).find('.product-price').val()) || 0;
            const sum = qty * price;
            $(this).find('.product-total').val(sum.toLocaleString('ru-RU', {minimumFractionDigits: 2}) + ' ₽');
            totalAmount += sum;
        });
        
        const vatRate = $('#default-vat').val();
        const vatType = $('#default-vat-type').val();
        
        let totalWithoutVat = totalAmount;
        let totalVat = 0;
        let totalWithVat = totalAmount;
        
        if (vatRate !== 'none') {
            const vatPercent = parseFloat(vatRate);
            if (vatType === 'included') {
                totalWithVat = totalAmount;
                totalVat = totalAmount * vatPercent / (100 + vatPercent);
                totalWithoutVat = totalAmount - totalVat;
            } else {
                totalWithoutVat = totalAmount;
                totalVat = totalAmount * vatPercent / 100;
                totalWithVat = totalAmount + totalVat;
            }
        }
        
        $('#total-without-vat').text(totalWithoutVat.toLocaleString('ru-RU', {minimumFractionDigits: 2}) + ' ₽');
        $('#total-vat').text(totalVat.toLocaleString('ru-RU', {minimumFractionDigits: 2}) + ' ₽');
        $('#total-with-vat').text(totalWithVat.toLocaleString('ru-RU', {minimumFractionDigits: 2}) + ' ₽');
    }
    
    // ============== PREVIEW ==============
    
    let previewDebounceTimer = null;
    
    function updatePreview() {
        clearTimeout(previewDebounceTimer);
        previewDebounceTimer = setTimeout(doUpdatePreview, 500);
    }
    
    async function doUpdatePreview() {
        const formData = collectFormData();
        
        try {
            const response = await fetch(`${API_URL}/documents/akt/preview`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
            
            if (response.ok) {
                const htmlContent = await response.text();
                
                // Update iframe in modal
                const iframe = document.getElementById('preview-iframe');
                if (iframe) {
                    iframe.srcdoc = htmlContent;
                }
                
                // Update sidebar canvas
                renderPreviewToCanvas(htmlContent);
            }
        } catch (error) {
            console.error('Preview error:', error);
        }
    }
    
    function renderPreviewToCanvas(htmlContent) {
        const canvas = document.getElementById('sidebar-preview-canvas');
        if (!canvas) return;
        
        const container = document.createElement('div');
        container.style.cssText = 'position:absolute;left:-9999px;top:-9999px;width:800px;background:white;';
        container.innerHTML = htmlContent;
        document.body.appendChild(container);
        
        html2canvas(container, {
            scale: 1,
            useCORS: true,
            logging: false
        }).then(renderedCanvas => {
            const ctx = canvas.getContext('2d');
            canvas.width = renderedCanvas.width;
            canvas.height = renderedCanvas.height;
            ctx.drawImage(renderedCanvas, 0, 0);
            document.body.removeChild(container);
        }).catch(err => {
            console.error('html2canvas error:', err);
            document.body.removeChild(container);
        });
    }
    
    function collectFormData() {
        const items = [];
        $('.product-row').each(function() {
            const name = $(this).find('.product-name').val();
            const qty = parseFloat($(this).find('.product-qty').val()) || 0;
            const unit = $(this).find('.product-unit').val();
            const price = parseFloat($(this).find('.product-price').val()) || 0;
            const total = qty * price;
            
            if (name) {
                items.push({
                    name: name,
                    quantity: qty,
                    unit: unit,
                    price: price,
                    amount: total
                });
            }
        });
        
        return {
            document_number: $('#akt-number').val(),
            document_date: $('#akt-date').val(),
            contract_number: $('#contract-number').val(),
            contract_date: $('#contract-date').val(),
            
            executor: {
                name: $('#executor-name').val(),
                inn: $('#executor-inn').val(),
                kpp: $('#executor-kpp').val(),
                address: $('#executor-address').val()
            },
            executor_signatory: $('#executor-signatory').val(),
            executor_org_type: getOrgTypeByInn($('#executor-inn').val()),
            executor_stamp_image: selectedExecutorOrg?.stamp_base64 || null,
            executor_signature: selectedExecutorOrg?.director_signature || null,
            
            customer: {
                name: $('#customer-name').val(),
                inn: $('#customer-inn').val(),
                kpp: $('#customer-kpp').val(),
                address: $('#customer-address').val()
            },
            customer_signatory: $('#customer-signatory').val(),
            
            vat_rate: $('#default-vat').val(),
            vat_type: $('#default-vat-type').val(),
            
            items: items,
            notes: $('#notes').val()
        };
    }
    
    // ============== DRAFT SAVING ==============
    
    // Сохранение документа как pending для неавторизованного пользователя (на сервере)
    async function savePendingDocument(requestData) {
        try {
            const response = await fetch('/api/v1/drafts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    document_type: 'akt',
                    document_data: requestData
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('documatica_draft_token', data.draft_token);
                localStorage.setItem('documatica_pending_document', JSON.stringify(requestData));
                return data.draft_token;
            }
        } catch (error) {
            console.error('Ошибка сохранения черновика:', error);
        }
        
        localStorage.setItem('documatica_pending_document', JSON.stringify(requestData));
        return null;
    }
    
    // Обновление UI модалки при сохранении черновика
    function updateModalSaveStatus(success, draftToken) {
        // Обновляем оба возможных элемента статуса
        const statusIds = ['draft-save-status', 'draft-save-status-auth'];
        
        statusIds.forEach(id => {
            const statusEl = document.getElementById(id);
            if (!statusEl) return;
            
            if (success) {
                statusEl.innerHTML = `
                    <div style="display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="3">
                            <polyline points="20 6 9 17 4 12"></polyline>
                        </svg>
                        <span style="color: #166534; font-weight: 600;">Черновик сохранён на сервере</span>
                    </div>
                `;
            } else {
                statusEl.innerHTML = `
                    <div style="display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2">
                            <circle cx="12" cy="12" r="10"></circle>
                            <path d="M12 16v-4M12 8h.01"></path>
                        </svg>
                        <span style="color: #92400e; font-weight: 600;">Черновик сохранён локально</span>
                    </div>
                `;
            }
        });
    }
    
    // ============== FORM SUBMIT ==============
    
    $('#akt-form').on('submit', async function(e) {
        e.preventDefault();
        
        const formData = collectFormData();
        
        // Валидация
        if (!formData.document_number) {
            toastError('Укажите номер акта');
            return;
        }
        if (!formData.executor.name) {
            toastError('Укажите наименование исполнителя');
            return;
        }
        if (!formData.customer.name) {
            toastError('Укажите наименование заказчика');
            return;
        }
        if (formData.items.length === 0) {
            toastError('Добавьте хотя бы одну позицию');
            return;
        }
        
        const submitBtn = $(this).find('button[type="submit"]');
        const originalText = submitBtn.html();
        submitBtn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm me-2"></span>Сохранение...');
        
        try {
            const token = localStorage.getItem('documatica_token');
            
            // Если нет токена - сохраняем как черновик и показываем модалку
            if (!token) {
                submitBtn.prop('disabled', false).html(originalText);
                
                // Показываем модалку сразу
                const modal = new bootstrap.Modal(document.getElementById('guestRegistrationModal'));
                modal.show();
                
                // Сохраняем черновик на сервере
                const draftToken = await savePendingDocument(formData);
                updateModalSaveStatus(!!draftToken, draftToken);
                
                // Добавляем draft_token к ссылкам OAuth
                if (draftToken) {
                    const yandexLinks = document.querySelectorAll('#guestRegistrationModal a[href*="/auth/yandex/login"]');
                    yandexLinks.forEach(link => {
                        link.href = `/auth/yandex/login?draft_token=${draftToken}&redirect_to=/dashboard/akt/create/`;
                    });
                }
                return;
            }
            
            const headers = { 'Content-Type': 'application/json' };
            headers['Authorization'] = 'Bearer ' + token;
            
            const response = await fetch(`${API_URL}/documents/akt/save`, {
                method: 'POST',
                headers: headers,
                credentials: 'include',
                body: JSON.stringify(formData)
            });
            
            // Проверяем что ответ - JSON
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                throw new Error('Сервер вернул некорректный ответ');
            }
            
            const result = await response.json();
            
            if (result.success) {
                toastSuccess('Акт успешно сохранен!');
                
                if (result.pdf_url) {
                    window.open(result.pdf_url, '_blank');
                } else if (result.html_url) {
                    window.open(result.html_url, '_blank');
                }
            } else if (result.require_auth) {
                const modal = new bootstrap.Modal(document.getElementById('guestRegistrationModal'));
                modal.show();
            } else if (result.limit_reached) {
                toastWarning(result.message || 'Достигнут лимит документов');
            } else {
                toastError(result.message || 'Ошибка сохранения');
            }
        } catch (error) {
            console.error('Save error:', error);
            toastError('Ошибка соединения с сервером');
        } finally {
            submitBtn.prop('disabled', false).html(originalText);
        }
    });
    
    // Modal download button
    $('#modal-download-pdf').on('click', function() {
        $('#akt-form').trigger('submit');
    });
    
    // Preview button
    $('#preview-btn').on('click', function() {
        updatePreview();
    });
    
    // Auto number button
    $('#auto-number-btn').on('click', function() {
        const now = new Date();
        const prefix = now.getFullYear().toString().slice(-2) + 
                      String(now.getMonth() + 1).padStart(2, '0');
        const random = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
        $('#akt-number').val(prefix + '-' + random);
    });
    
    // Guest registration form
    $('#guest-registration-form').on('submit', async function(e) {
        e.preventDefault();
        
        const email = $('#guest-email').val();
        const password = $('#guest-password').val();
        const name = $('#guest-name').val();
        const terms = $('#guest-terms').is(':checked');
        
        if (!terms) {
            $('#guest-reg-alert').text('Примите условия использования').removeClass('d-none');
            return;
        }
        
        const submitBtn = $('#guest-reg-submit-btn');
        submitBtn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm me-2"></span>Регистрация...');
        $('#guest-reg-alert').addClass('d-none');
        
        try {
            const response = await fetch(`${API_URL}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password, name })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                // Привязываем черновик к пользователю
                const draftToken = localStorage.getItem('documatica_draft_token');
                if (draftToken && result.access_token) {
                    try {
                        await fetch('/api/v1/drafts/claim', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'Authorization': `Bearer ${result.access_token}`
                            },
                            body: JSON.stringify({ draft_token: draftToken })
                        });
                        localStorage.removeItem('documatica_draft_token');
                        localStorage.removeItem('documatica_pending_document');
                    } catch (err) {
                        console.error('Ошибка привязки черновика:', err);
                    }
                }
                
                toastSuccess('Проверьте почту для подтверждения аккаунта');
                bootstrap.Modal.getInstance(document.getElementById('guestRegistrationModal')).hide();
            } else {
                $('#guest-reg-alert').text(result.detail || 'Ошибка регистрации').removeClass('d-none');
            }
        } catch (error) {
            $('#guest-reg-alert').text('Ошибка соединения с сервером').removeClass('d-none');
        } finally {
            submitBtn.prop('disabled', false).html('Зарегистрироваться');
        }
    });
    
    // ============== AI ANALYSIS ==============
    
    $('#ai-analyze-btn').on('click', async function() {
        const btn = $(this);
        const resultContainer = $('#ai-analysis-result');
        
        // Show loading state
        btn.prop('disabled', true);
        btn.html(`
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin">
                <path d="M21 12a9 9 0 11-6.219-8.56"/>
            </svg>
            Анализ...
        `);
        
        resultContainer.html(`
            <div class="text-center py-32">
                <div class="spinner-border text-primary" role="status"></div>
                <p class="mt-16 mb-0 text-secondary-light">ИИ анализирует документ...</p>
            </div>
        `);
        
        // Collect form data
        const formData = collectFormData();
        
        // Prepare request for AKT analysis
        const analysisData = {
            akt_number: formData.document_number || '',
            akt_date: formData.document_date || '',
            contract_number: formData.contract_number || '',
            contract_date: formData.contract_date || '',
            executor_name: formData.executor?.name || '',
            executor_inn: formData.executor?.inn || '',
            executor_kpp: formData.executor?.kpp || '',
            executor_address: formData.executor?.address || '',
            customer_name: formData.customer?.name || '',
            customer_inn: formData.customer?.inn || '',
            customer_kpp: formData.customer?.kpp || '',
            customer_address: formData.customer?.address || '',
            items: formData.items || [],
            notes: formData.notes || ''
        };
        
        try {
            const response = await fetch('/api/v1/ai/analyze-akt', {
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
            renderAnalysisResult(result);
            
        } catch (error) {
            console.error('AI Analysis error:', error);
            resultContainer.html(`
                <div class="alert alert-danger mb-0">
                    <strong>Ошибка:</strong> ${error.message}
                </div>
            `);
        } finally {
            btn.prop('disabled', false);
            btn.html(`
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="11" cy="11" r="8"/>
                    <path d="m21 21-4.3-4.3"/>
                </svg>
                Анализировать
            `);
        }
    });
    
    function renderAnalysisResult(result) {
        const container = $('#ai-analysis-result');
        let html = '';
        
        // Errors
        if (result.errors && result.errors.length > 0) {
            html += `
                <div class="alert alert-danger mb-16" style="border-left: 4px solid #dc2626;">
                    <div class="fw-bold mb-8" style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em;">Критические ошибки (${result.errors.length})</div>
                    <ul class="mb-0 ps-20">
                        ${result.errors.map(e => `<li class="mb-4"><span class="badge bg-danger-100 text-danger-600 me-8">${e.field || 'Документ'}</span>${e.message}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        // Warnings
        if (result.warnings && result.warnings.length > 0) {
            html += `
                <div class="alert alert-warning mb-16" style="border-left: 4px solid #f59e0b;">
                    <div class="fw-bold mb-8" style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em;">Предупреждения (${result.warnings.length})</div>
                    <ul class="mb-0 ps-20">
                        ${result.warnings.map(w => `<li class="mb-4"><span class="badge bg-warning-100 text-warning-600 me-8">${w.field || 'Документ'}</span>${w.message}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        // Suggestions
        if (result.suggestions && result.suggestions.length > 0) {
            html += `
                <div class="alert alert-info mb-16" style="border-left: 4px solid #3b82f6;">
                    <div class="fw-bold mb-8" style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em;">Рекомендации (${result.suggestions.length})</div>
                    <ul class="mb-0 ps-20">
                        ${result.suggestions.map(s => `<li class="mb-4"><strong>${s.field || 'Общее'}:</strong> ${s.message}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        // Success case - no issues
        if ((!result.errors || result.errors.length === 0) && 
            (!result.warnings || result.warnings.length === 0) &&
            (!result.suggestions || result.suggestions.length === 0)) {
            html += `
                <div class="alert alert-success mb-16" style="border-left: 4px solid #10b981;">
                    <div class="fw-bold mb-8" style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em;">Проверка пройдена</div>
                    <p class="mb-0">Документ заполнен корректно. Ошибок не обнаружено.</p>
                </div>
            `;
        }
        
        // Summary
        if (result.summary) {
            html += `
                <div class="bg-neutral-50 radius-8 p-16">
                    <div class="fw-bold mb-8" style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b;">Заключение</div>
                    <p class="mb-0 text-secondary-light">${result.summary}</p>
                </div>
            `;
        }
        
        container.html(html);
    }
    
    // Clear highlights button
    $('#clear-highlights-btn').on('click', function() {
        $(this).removeClass('d-flex').addClass('d-none');
        // Reset preview
        updatePreview();
    });
    
    // ============== HELPERS ==============
    
    function showInputError(inputId, message) {
        const container = $(`#${inputId}-error-container`);
        const errorEl = $(`#${inputId}-error`);
        if (container.length && errorEl.length) {
            errorEl.text(message);
            container.removeClass('d-none');
        }
        $(`#${inputId}`).addClass('is-invalid');
    }
    
    function clearInputError(inputId) {
        $(`#${inputId}-error-container`).addClass('d-none');
        $(`#${inputId}`).removeClass('is-invalid');
    }
    
    function loadFormDataForEdit(data) {
        if (!data) return;
        
        $('#akt-number').val(data.document_number || '');
        $('#akt-date').val(data.document_date || '');
        $('#contract-number').val(data.contract_number || '');
        $('#contract-date').val(data.contract_date || '');
        
        if (data.executor) {
            $('#executor-name').val(data.executor.name || '');
            $('#executor-inn').val(data.executor.inn || '');
            $('#executor-kpp').val(data.executor.kpp || '');
            $('#executor-address').val(data.executor.address || '');
        }
        $('#executor-signatory').val(data.executor_signatory || '');
        
        if (data.customer) {
            $('#customer-name').val(data.customer.name || '');
            $('#customer-inn').val(data.customer.inn || '');
            $('#customer-kpp').val(data.customer.kpp || '');
            $('#customer-address').val(data.customer.address || '');
        }
        $('#customer-signatory').val(data.customer_signatory || '');
        
        $('#default-vat').val(data.vat_rate || '20');
        $('#default-vat-type').val(data.vat_type || 'on-top');
        $('#notes').val(data.notes || '');
        
        // Load items
        if (data.items && data.items.length > 0) {
            $('#products-container').empty();
            
            data.items.forEach((item, index) => {
                productRowCount = index + 1;
                const row = `
                    <div class="product-row card border radius-12 p-16 mb-16" data-row="${productRowCount}">
                        <div class="row g-12 align-items-end">
                            <div class="col">
                                <label class="form-label fw-bold text-xs text-slate-600 text-uppercase" style="letter-spacing: 0.05em; margin-top: 16px; margin-bottom: 8px;">Наименование <span class="text-danger">*</span></label>
                                <input type="text" class="form-control product-name" value="${item.name || ''}" required>
                            </div>
                            <div class="col-auto" style="width: 100px;">
                                <label class="form-label fw-bold text-xs text-slate-600 text-uppercase" style="letter-spacing: 0.05em; margin-top: 16px; margin-bottom: 8px;">Кол-во</label>
                                <input type="number" class="form-control product-qty" value="${item.quantity || 1}" min="0.01" step="0.01">
                            </div>
                            <div class="col-auto" style="width: 110px;">
                                <label class="form-label fw-bold text-xs text-slate-600 text-uppercase" style="letter-spacing: 0.05em; margin-top: 16px; margin-bottom: 8px;">Ед. изм.</label>
                                <select class="form-select product-unit">
                                    <option value="усл" ${item.unit === 'усл' ? 'selected' : ''}>усл</option>
                                    <option value="шт" ${item.unit === 'шт' ? 'selected' : ''}>шт</option>
                                    <option value="ч" ${item.unit === 'ч' ? 'selected' : ''}>ч</option>
                                    <option value="кг" ${item.unit === 'кг' ? 'selected' : ''}>кг</option>
                                    <option value="л" ${item.unit === 'л' ? 'selected' : ''}>л</option>
                                    <option value="м" ${item.unit === 'м' ? 'selected' : ''}>м</option>
                                    <option value="м2" ${item.unit === 'м2' ? 'selected' : ''}>м2</option>
                                    <option value="м3" ${item.unit === 'м3' ? 'selected' : ''}>м3</option>
                                </select>
                            </div>
                            <div class="col-auto" style="width: 120px;">
                                <label class="form-label fw-bold text-xs text-slate-600 text-uppercase" style="letter-spacing: 0.05em; margin-top: 16px; margin-bottom: 8px;">Цена</label>
                                <input type="number" class="form-control product-price" value="${item.price || 0}" min="0" step="0.01">
                            </div>
                            <div class="col-auto" style="width: 120px;">
                                <label class="form-label fw-bold text-xs text-slate-600 text-uppercase" style="letter-spacing: 0.05em; margin-top: 16px; margin-bottom: 8px;">Сумма</label>
                                <input type="text" class="form-control product-total" value="0 ₽" readonly>
                            </div>
                            <div class="col-auto">
                                <button type="button" class="btn btn-outline-danger remove-product" title="Удалить">
                                    <iconify-icon icon="mdi:trash-can-outline"></iconify-icon>
                                </button>
                            </div>
                        </div>
                    </div>
                `;
                $('#products-container').append(row);
            });
        }
        
        calculateTotals();
        updatePreview();
    }
    
    // Auto-update preview on input
    $(document).on('input', '#executor-name, #executor-inn, #customer-name, #customer-inn, #akt-number, .product-name', function() {
        updatePreview();
    });
    
    // Initial preview
    setTimeout(function() {
        updatePreview();
    }, 500);
    
    // Initial totals calculation
    calculateTotals();
    
    // ============== CANVAS MAGNIFIER (лупа) ==============
    const $magnifier = $('#canvas-magnifier');
    const $magnifierCanvas = $('#magnifier-canvas')[0];
    const $previewCanvas = $('#sidebar-preview-canvas')[0];
    const $container = $previewCanvas ? $($previewCanvas).parent() : null;
    
    if ($container && $previewCanvas && $magnifierCanvas) {
        const displayWidth = 400; // Визуальный размер лупы
        const displayHeight = 300;
        const canvasWidth = 1200; // Физическое разрешение canvas
        const canvasHeight = 900;
        const magnification = 1.1; // Увеличение в 1.1 раза
        const magnifierCtx = $magnifierCanvas.getContext('2d');
        
        $container.on('mouseenter', function() {
            if ($previewCanvas.width > 0) { // Проверяем что canvas отрендерен
                $magnifier.show();
            }
        });
        
        $container.on('mouseleave', function() {
            $magnifier.hide();
        });
        
        $container.on('mousemove', function(e) {
            if ($previewCanvas.width === 0) return;
            
            const containerOffset = $container.offset();
            const mouseX = e.pageX - containerOffset.left;
            const mouseY = e.pageY - containerOffset.top;
            
            // Позиционируем лупу (центр в курсоре) - используем визуальные размеры
            let left = mouseX - displayWidth / 2;
            let top = mouseY - displayHeight / 2;
            
            // Ограничиваем лупу границами контейнера
            const containerWidth = $container.width();
            const containerHeight = $container.height();
            
            if (left < 0) left = 0;
            if (top < 0) top = 0;
            if (left + displayWidth > containerWidth) left = containerWidth - displayWidth;
            if (top + displayHeight > containerHeight) top = containerHeight - displayHeight;
            
            $magnifier.css({
                left: left + 'px',
                top: top + 'px'
            });
            
            // Вычисляем координаты на canvas с учётом масштабирования
            const canvasRect = $previewCanvas.getBoundingClientRect();
            const containerRect = $container[0].getBoundingClientRect();
            
            // Относительные координаты мыши на canvas
            const canvasMouseX = (mouseX - (canvasRect.left - containerRect.left)) * ($previewCanvas.width / canvasRect.width);
            const canvasMouseY = (mouseY - (canvasRect.top - containerRect.top)) * ($previewCanvas.height / canvasRect.height);
            
            // Размер области которую захватываем (в пикселях оригинального canvas)
            const sourceWidth = displayWidth / magnification;
            const sourceHeight = displayHeight / magnification;
            
            // Очищаем magnifier canvas
            magnifierCtx.clearRect(0, 0, canvasWidth, canvasHeight);
            
            // Рисуем увеличенную область
            magnifierCtx.drawImage(
                $previewCanvas,
                canvasMouseX - sourceWidth / 2, // source x
                canvasMouseY - sourceHeight / 2, // source y
                sourceWidth, // source width
                sourceHeight, // source height
                0, // dest x
                0, // dest y
                canvasWidth, // dest width
                canvasHeight  // dest height
            );
        });
    }
    // ============== END CANVAS MAGNIFIER ==============
    
});
