$(document).ready(function() {
    // Отключаем transitions при инициализации страницы
    document.body.classList.add('no-transitions');
    setTimeout(function() {
        document.body.classList.remove('no-transitions');
    }, 100);
    
    // ============== DRAFT RESTORE ==============
    // Check if we have a draft_token in URL (after OAuth redirect)
    async function checkAndRestoreDraft() {
        const urlParams = new URLSearchParams(window.location.search);
        const draftToken = urlParams.get('draft_token');
        
        if (draftToken) {
            try {
                const response = await fetch(`/api/v1/drafts/${draftToken}`);
                if (response.ok) {
                    const draft = await response.json();
                    console.log('[DRAFT] Restored draft from server:', draft.document_type);
                    
                    // Store data in localStorage for form restoration
                    localStorage.setItem('documatica_pending_document', JSON.stringify(draft.document_data));
                    
                    // Clear draft_token from URL
                    const newUrl = window.location.pathname;
                    window.history.replaceState({}, '', newUrl);
                    
                    // Reload page to apply restored data
                    // (form will pick up from localStorage)
                    window.location.reload();
                }
            } catch (error) {
                console.error('[DRAFT] Error restoring draft:', error);
            }
        }
    }
    
    // Check for draft token in URL (after OAuth redirect)
    const hasToken = localStorage.getItem('documatica_token') || document.cookie.includes('access_token=');
    const hasDraftInUrl = new URLSearchParams(window.location.search).get('draft_token');
    if (hasToken && hasDraftInUrl) {
        checkAndRestoreDraft();
    }
    // ============== END DRAFT RESTORE ==============
    
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
    
    // Устанавливаем сегодняшнюю дату и обработчик иконки после инициализации
    setTimeout(function() {
        const updDateEl = document.getElementById('upd-date');
        if (updDateEl && updDateEl._flatpickr) {
            // Устанавливаем сегодняшнюю дату
            updDateEl._flatpickr.setDate(new Date());
            
            // Иконка календаря открывает датапикер
            document.getElementById('upd-date-icon').addEventListener('click', function() {
                updDateEl._flatpickr.open();
            });
            
            // Маска для ручного ввода даты дд.мм.гггг
            updDateEl.addEventListener('input', function(e) {
                let value = e.target.value.replace(/\D/g, ''); // Только цифры
                if (value.length > 8) value = value.substring(0, 8);
                
                let formatted = '';
                if (value.length > 0) {
                    let day = value.substring(0, 2);
                    // Ограничиваем день 01-31
                    if (parseInt(day) > 31) day = '31';
                    if (value.length === 1 && parseInt(day) > 3) day = '0' + day;
                    formatted = day;
                }
                if (value.length > 2) {
                    let month = value.substring(2, 4);
                    // Ограничиваем месяц 01-12
                    if (parseInt(month) > 12) month = '12';
                    if (value.length === 3 && parseInt(month) > 1) month = '0' + month;
                    formatted += '.' + month;
                }
                if (value.length > 4) {
                    formatted += '.' + value.substring(4, 8);
                }
                
                // Обновляем значение только если оно изменилось
                if (e.target.value !== formatted) {
                    const cursorPos = formatted.length;
                    e.target.value = formatted;
                    e.target.setSelectionRange(cursorPos, cursorPos);
                }
            });
            
            // Проверка валидности даты при потере фокуса
            updDateEl.addEventListener('blur', function(e) {
                const value = e.target.value;
                if (value && value.length === 10) {
                    const parts = value.split('.');
                    const day = parseInt(parts[0]);
                    const month = parseInt(parts[1]);
                    const year = parseInt(parts[2]);
                    
                    // Создаём дату и проверяем валидность
                    const date = new Date(year, month - 1, day);
                    const isValid = date.getFullYear() === year && 
                                  date.getMonth() === month - 1 && 
                                  date.getDate() === day;
                    
                    if (!isValid) {
                        e.target.classList.add('is-invalid');
                        // Показываем сообщение об ошибке
                        let errorMsg = e.target.parentElement.querySelector('.invalid-feedback');
                        if (!errorMsg) {
                            errorMsg = document.createElement('div');
                            errorMsg.className = 'invalid-feedback';
                            errorMsg.style.display = 'block';
                            errorMsg.textContent = 'Некорректная дата';
                            e.target.parentElement.appendChild(errorMsg);
                        }
                    } else {
                        e.target.classList.remove('is-invalid');
                        const errorMsg = e.target.parentElement.querySelector('.invalid-feedback');
                        if (errorMsg) errorMsg.remove();
                        // Синхронизируем с flatpickr
                        if (e.target._flatpickr) {
                            e.target._flatpickr.setDate(date, false);
                        }
                    }
                }
            });
        }
    }, 100);
    
    // API URL - берём из конфига или используем дефолтное значение
    const API_URL = window.UPD_CONFIG?.apiUrl || '/api/v1';
    
    // Настраиваем интерфейс для авторизованного пользователя
    (function() {
        const token = localStorage.getItem('documatica_token');
        const user = JSON.parse(localStorage.getItem('documatica_user') || '{}');
        
        // Сайдбар показываем всегда, авторизация проверяется только при генерации PDF
        
        if (token && user) {
            // Пользователь авторизован - показываем его данные
            if (user.name) {
                const initials = user.name.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2);
                $('#user-initials').text(initials);
                $('#user-name').text(user.name);
            }
            if (user.email) {
                $('#user-email').text(user.email);
            }
        } else {
            // Не авторизован - показываем гостевые инициалы
            $('#user-initials').text('Г');
            $('#user-name').text('Гость');
            $('#user-email').text('Войдите для сохранения');
        }
        
        // Обработчик выхода
        $('#logout-btn').on('click', function(e) {
            e.preventDefault();
            localStorage.removeItem('documatica_token');
            localStorage.removeItem('documatica_user');
            window.location.href = '/';
        });
    })();
    
    // ID редактируемого документа (если есть) - берём из window.UPD_CONFIG
    const editDocumentId = window.UPD_CONFIG?.editDocumentId || '';
    
    // Загрузка данных редактируемого документа
    if (editDocumentId) {
        (async function() {
            try {
                const response = await fetch(`/api/v1/documents/saved/${editDocumentId}/form-data`, { credentials: 'include' });
                if (response.ok) {
                    const formData = await response.json();
                    setTimeout(function() {
                        loadFormDataForEdit(formData);
                        toastSuccess('Документ загружен для редактирования');
                    }, 500);
                } else {
                    toastError('Не удалось загрузить данные документа');
                }
            } catch (error) {
                console.error('Error loading document:', error);
                toastError('Ошибка загрузки документа');
            }
        })();
    }
    
    // Check if we need to load a template
    const urlParams = new URLSearchParams(window.location.search);
    const templateId = urlParams.get('template');
    if (templateId && templateId !== 'true') {
        // Загрузка шаблона с сервера по ID
        (async function() {
            try {
                const response = await fetch(`/api/v1/templates/${templateId}`, { credentials: 'include' });
                if (response.ok) {
                    const template = await response.json();
                    setTimeout(function() {
                        loadTemplateData(template.data);
                        toastSuccess('Шаблон загружен! Измените данные и создайте документ.');
                    }, 500);
                } else {
                    toastError('Не удалось загрузить шаблон');
                }
            } catch (error) {
                console.error('Error loading template:', error);
                toastError('Ошибка загрузки шаблона');
            }
        })();
    } else if (templateId === 'true') {
        // Старый способ через localStorage (для обратной совместимости)
        const templateData = localStorage.getItem('upd_use_template');
        if (templateData) {
            setTimeout(function() {
                loadTemplateData(JSON.parse(templateData));
                localStorage.removeItem('upd_use_template');
                toastSuccess('Шаблон загружен! Измените данные и создайте документ.');
            }, 500);
        }
    }
    
    // Check if we need to load a draft
    if (urlParams.get('draft') === 'true') {
        const draftData = localStorage.getItem('upd_draft');
        if (draftData) {
            setTimeout(function() {
                loadTemplateData(JSON.parse(draftData));
                toastSuccess('Черновик загружен!');
            }, 500);
        }
    }
    
    // Storage for loaded data
    let organizationsList = [];
    let contractorsList = [];
    let selectedSellerOrg = null;  // Сохраняем выбранную организацию для подписи и печати
    
    // ============== DADATA АВТОЗАПОЛНЕНИЕ ==============
    
    // Поиск компании по ИНН через Dadata
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
            
            const company = await response.json();
            return company;
            
        } catch (error) {
            console.error('Dadata search error:', error);
            showInputError(innInputId, 'Ошибка при поиске компании');
            return null;
        } finally {
            loadingEl.addClass('d-none');
            searchBtn.prop('disabled', false);
        }
    }
    
    // Заполнение полей продавца
    function fillSellerFields(company) {
        if (!company) return;
        
        $('#seller-name').val(company.name || '');
        $('#seller-inn').val(company.inn || '');
        $('#seller-kpp').val(company.kpp || '');
        $('#seller-address').val(company.address_full || company.address || '');
        
        // Подсветка заполненных полей
        $('#seller-name, #seller-inn, #seller-kpp, #seller-address').addClass('bg-success-100');
        setTimeout(() => {
            $('#seller-name, #seller-inn, #seller-kpp, #seller-address').removeClass('bg-success-100');
        }, 2000);
        
        toastSuccess(`Данные компании "${company.name}" загружены`);
    }
    
    // Заполнение полей покупателя
    function fillBuyerFields(company) {
        if (!company) return;
        
        $('#buyer-name').val(company.name || '');
        $('#buyer-inn').val(company.inn || '');
        $('#buyer-kpp').val(company.kpp || '');
        $('#buyer-address').val(company.address_full || company.address || '');
        
        // Подсветка заполненных полей
        $('#buyer-name, #buyer-inn, #buyer-kpp, #buyer-address').addClass('bg-success-100');
        setTimeout(() => {
            $('#buyer-name, #buyer-inn, #buyer-kpp, #buyer-address').removeClass('bg-success-100');
        }, 2000);
        
        toastSuccess(`Данные компании "${company.name}" загружены`);
    }
    
    // Обработчики кнопок поиска по ИНН
    $('#seller-inn-search').on('click', async function() {
        const inn = $('#seller-inn').val();
        const company = await searchCompanyByInn(inn, 'seller');
        if (company) {
            fillSellerFields(company);
        }
    });
    
    $('#buyer-inn-search').on('click', async function() {
        const inn = $('#buyer-inn').val();
        const company = await searchCompanyByInn(inn, 'buyer');
        if (company) {
            fillBuyerFields(company);
        }
    });
    
    // Автопоиск при вводе полного ИНН (10 или 12 символов) и нажатии Enter
    $('#seller-inn').on('keypress', async function(e) {
        if (e.which === 13) {
            e.preventDefault();
            const inn = $(this).val();
            if (inn.length >= 10) {
                const company = await searchCompanyByInn(inn, 'seller');
                if (company) {
                    fillSellerFields(company);
                }
            }
        }
    });
    
    $('#buyer-inn').on('keypress', async function(e) {
        if (e.which === 13) {
            e.preventDefault();
            const inn = $(this).val();
            if (inn.length >= 10) {
                const company = await searchCompanyByInn(inn, 'buyer');
                if (company) {
                    fillBuyerFields(company);
                }
            }
        }
    });
    
    // ============== КОНЕЦ DADATA ==============
    
    // Load organizations for modal
    async function loadOrganizationsModal(searchTerm = '') {
        try {
            const response = await fetch(`${API_URL}/organizations`);
            organizationsList = await response.json();
            // Sync to localStorage
            localStorage.setItem('organizations', JSON.stringify(organizationsList));
        } catch (error) {
            console.log('API unavailable, using localStorage');
            organizationsList = JSON.parse(localStorage.getItem('organizations') || '[]');
        }
        
        renderOrganizationsModal(searchTerm);
    }
    
    // Render organizations in modal
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
        
        // Добавляем hover эффект
        $('.organization-item .card').hover(
            function() { $(this).css('transform', 'translateY(-2px)'); },
            function() { $(this).css('transform', 'translateY(0)'); }
        );
    }
    
    // Load contractors for modal
    async function loadContractorsModal(searchTerm = '') {
        try {
            const response = await fetch(`${API_URL}/contractors`);
            contractorsList = await response.json();
            // Sync to localStorage
            localStorage.setItem('contractors', JSON.stringify(contractorsList));
        } catch (error) {
            console.log('API unavailable, using localStorage');
            contractorsList = JSON.parse(localStorage.getItem('contractors') || '[]');
        }
        
        renderContractorsModal(searchTerm);
    }
    
    // Render contractors in modal
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
        
        // Добавляем hover эффект
        $('.contractor-item .card').hover(
            function() { $(this).css('transform', 'translateY(-2px)'); },
            function() { $(this).css('transform', 'translateY(0)'); }
        );
    }
    
    // Определение типа организации по ИНН (10 цифр = ООО, 12 цифр = ИП)
    function getOrgTypeByInn(inn) {
        if (!inn) return 'ooo';
        const cleanInn = inn.toString().replace(/\D/g, '');
        return cleanInn.length === 12 ? 'ip' : 'ooo';
    }
    
    // Обновление отображения типа организации
    function updateOrgTypeDisplay(inn) {
        const orgType = getOrgTypeByInn(inn);
        const badge = $('#seller-org-type-badge');
        if (badge.length) {
            if (orgType === 'ip') {
                badge.text('ИП').removeClass('bg-primary-100 text-primary-600').addClass('bg-warning-100 text-warning-600');
            } else {
                badge.text('ООО').removeClass('bg-warning-100 text-warning-600').addClass('bg-primary-100 text-primary-600');
            }
            badge.removeClass('d-none');
        }
        return orgType;
    }
    
    // Select organization from modal
    $(document).on('click', '.organization-item', function() {
        const id = $(this).data('id');
        const org = organizationsList.find(o => o.id === id);
        if (org) {
            // Сохраняем выбранную организацию для использования подписи и печати
            selectedSellerOrg = org;
            
            // Определяем тип организации
            updateOrgTypeDisplay(org.inn);
            
            // Отключаем transitions при массовом заполнении полей
            document.body.classList.add('no-transitions');
            
            // Fill seller fields
            $('#seller-name').val(org.name);
            $('#seller-inn').val(org.inn);
            $('#seller-kpp').val(org.kpp || '');
            $('#seller-address').val(org.address || '');
            
            // Fill seller signer fields if available
            if (org.director_name || org.director) {
                $('#released-position').val('Генеральный директор');
                $('#released-by').val(org.director_name || org.director);
            }
            if (org.responsible_name) {
                $('#responsible-position').val(org.responsible_position || '');
                $('#responsible-name').val(org.responsible_name);
            }
            if (org.transfer_name) {
                // Can be used for transfer person
            }
            if (org.economic_entity) {
                $('#economic-entity').val(org.economic_entity);
            } else {
                $('#economic-entity').val(org.name + ', ИНН ' + org.inn);
            }
            
            // Close modal
            bootstrap.Modal.getInstance(document.getElementById('selectCompanyModal')).hide();
            
            // Hide "add to organizations" button since selected from list
            $('#save-seller-btn').removeClass('show');
            
            // Включаем transitions обратно
            setTimeout(function() {
                document.body.classList.remove('no-transitions');
            }, 50);
            
            // Update preview
            updatePreview();
        }
    });
    
    // Select contractor from modal
    $(document).on('click', '.contractor-item', function() {
        const id = $(this).data('id');
        const contractor = contractorsList.find(c => c.id === id);
        if (contractor) {
            // Отключаем transitions при массовом заполнении полей
            document.body.classList.add('no-transitions');
            
            // Fill buyer fields
            $('#buyer-name').val(contractor.name);
            $('#buyer-inn').val(contractor.inn);
            $('#buyer-kpp').val(contractor.kpp || '');
            $('#buyer-address').val(contractor.address || '');
            
            // Fill buyer signer fields if available
            if (contractor.receiver_name) {
                $('#received-position').val(contractor.receiver_position || '');
                $('#received-by').val(contractor.receiver_name);
            }
            if (contractor.responsible_name) {
                $('#buyer-responsible-position').val(contractor.responsible_position || '');
                $('#buyer-responsible-name').val(contractor.responsible_name);
            }
            if (contractor.economic_entity) {
                $('#buyer-economic-entity').val(contractor.economic_entity);
            } else {
                $('#buyer-economic-entity').val(contractor.name + ', ИНН ' + contractor.inn);
            }
            
            // Close modal
            bootstrap.Modal.getInstance(document.getElementById('selectContractorModal')).hide();
            
            // Hide "add to clients" button since selected from list
            $('#save-buyer-btn').removeClass('show');
            
            // Включаем transitions обратно
            setTimeout(function() {
                document.body.classList.remove('no-transitions');
            }, 50);
            
            // Update preview
            updatePreview();
        }
    });
    
    // Products list for modal
    let productsList = [];
    
    // Load products for modal
    async function loadProductsModal(searchTerm = '') {
        try {
            const response = await fetch(`${API_URL}/products`);
            productsList = await response.json();
        } catch (error) {
            console.log('API unavailable, using localStorage');
            productsList = JSON.parse(localStorage.getItem('products') || '[]');
        }
        
        renderProductsModal(searchTerm);
    }
    
    // Render products in modal
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
    
    // Select product from modal - add to products list
    $(document).on('click', '.product-item', function() {
        const id = $(this).data('id');
        const product = productsList.find(p => p.id === id);
        if (product) {
            addProductFromCatalog(product);
        }
    });
    
    // Add product from catalog to form
    function addProductFromCatalog(product) {
        productRowCount++;
        
        const newRow = `
            <div class="product-row card border radius-12 p-16 mb-16" data-row="${productRowCount}">
                <div class="row g-12 align-items-end">
                    <div class="col">
                        <label class="form-label text-sm mb-4">Наименование <span class="text-danger">*</span></label>
                        <input type="text" class="form-control product-name" value="${product.name}" required>
                    </div>
                    <div class="col-auto" style="width: 100px;">
                        <label class="form-label text-sm mb-4">Кол-во</label>
                        <input type="number" class="form-control product-qty" value="${product.qty || 1}" min="0.01" step="0.01">
                    </div>
                    <div class="col-auto" style="width: 110px;">
                        <label class="form-label text-sm mb-4">Ед. изм.</label>
                        <select class="form-select product-unit">
                            <option value="шт" ${product.unit === 'шт' ? 'selected' : ''}>шт</option>
                            <option value="усл" ${product.unit === 'усл' ? 'selected' : ''}>усл</option>
                            <option value="ч" ${product.unit === 'ч' ? 'selected' : ''}>ч</option>
                            <option value="кг" ${product.unit === 'кг' ? 'selected' : ''}>кг</option>
                            <option value="л" ${product.unit === 'л' ? 'selected' : ''}>л</option>
                            <option value="м" ${product.unit === 'м' ? 'selected' : ''}>м</option>
                            <option value="м2" ${product.unit === 'м2' ? 'selected' : ''}>м2</option>
                            <option value="м3" ${product.unit === 'м3' ? 'selected' : ''}>м3</option>
                        </select>
                    </div>
                    <div class="col-auto" style="width: 120px;">
                        <label class="form-label text-sm mb-4">Цена</label>
                        <input type="number" class="form-control product-price" value="${product.price || 0}" min="0" step="0.01">
                    </div>
                    <div class="col-auto" style="width: 120px;">
                        <label class="form-label text-sm mb-4">Сумма</label>
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
        
        // Don't close modal - allow adding multiple products
    }
    
    // Load organizations when modal opens
    $('#selectCompanyModal').on('shown.bs.modal', function() {
        loadOrganizationsModal();
        $('#search-organization').val('').focus();
    });
    
    // Load contractors when modal opens
    $('#selectContractorModal').on('shown.bs.modal', function() {
        loadContractorsModal();
        $('#search-contractor').val('').focus();
    });
    
    // Load products when modal opens
    $('#selectProductModal').on('shown.bs.modal', function() {
        loadProductsModal();
        $('#search-product-modal').val('').focus();
    });
    
    // Search in organization modal
    $('#search-organization').on('input', function() {
        renderOrganizationsModal($(this).val());
    });
    
    // Search in contractor modal
    $('#search-contractor').on('input', function() {
        renderContractorsModal($(this).val());
    });
    
    // Search in product modal
    $('#search-product-modal').on('input', function() {
        renderProductsModal($(this).val());
    });
    
    // Check for pre-selected organization/contractor from other pages
    const selectedOrganization = sessionStorage.getItem('selectedOrganization');
    if (selectedOrganization) {
        const org = JSON.parse(selectedOrganization);
        $('#seller-name').val(org.name);
        $('#seller-inn').val(org.inn);
        $('#seller-kpp').val(org.kpp || '');
        $('#seller-address').val(org.address || '');
        if (org.director_name) {
            $('#released-position').val('Генеральный директор');
            $('#released-by').val(org.director_name);
        }
        if (org.economic_entity) {
            $('#economic-entity').val(org.economic_entity);
        } else {
            $('#economic-entity').val(org.name + ', ИНН ' + org.inn);
        }
        
        // Установка НДС из организации
        if (org.vat_type) {
            if (org.vat_type === 'without' || org.vat_type === 'none') {
                $('#default-vat').val('none');
                // Без НДС - статус 2 (только передаточный документ)
                $('input[name="upd-status"][value="2"]').prop('checked', true);
            } else {
                $('#default-vat').val(org.vat_type);
                // Есть НДС - статус 1 (счет-фактура и передаточный документ)
                $('input[name="upd-status"][value="1"]').prop('checked', true);
            }
        }
        
        sessionStorage.removeItem('selectedOrganization');
    }
    
    const selectedContractor = sessionStorage.getItem('selectedContractor');
    if (selectedContractor) {
        const contractor = JSON.parse(selectedContractor);
        $('#buyer-name').val(contractor.name);
        $('#buyer-inn').val(contractor.inn);
        $('#buyer-kpp').val(contractor.kpp || '');
        $('#buyer-address').val(contractor.address || '');
        if (contractor.receiver_name) {
            $('#received-position').val(contractor.receiver_position || '');
            $('#received-by').val(contractor.receiver_name);
        }
        if (contractor.economic_entity) {
            $('#buyer-economic-entity').val(contractor.economic_entity);
        } else {
            $('#buyer-economic-entity').val(contractor.name + ', ИНН ' + contractor.inn);
        }
        sessionStorage.removeItem('selectedContractor');
    }
    
    // Пересчет при изменении настроек НДС
    $('#default-vat, #default-vat-type').on('change', function() {
        // Автоматический статус УПД по НДС
        const vatRate = $('#default-vat').val();
        if (vatRate === 'none') {
            // Без НДС - статус 2 (только передаточный документ)
            $('input[name="upd-status"][value="2"]').prop('checked', true);
            $('#upd-status-display').text('2 - передаточный документ (акт)');
        } else {
            // Любой НДС (включая 0%) - статус 1 (счет-фактура)
            $('input[name="upd-status"][value="1"]').prop('checked', true);
            $('#upd-status-display').text('1 - счет-фактура и передаточный документ');
        }
        calculateTotals();
        updatePreview();
    });
    
    // Auto-numbering
    let autoNumberCounter = 1;
    $('#auto-number-btn').on('click', function() {
        const today = new Date();
        const dateStr = today.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' }).replace(/\./g, '');
        $('#upd-number').val(`${autoNumberCounter}-${dateStr}`);
        autoNumberCounter++;
    });
    
    // Show "Add to organizations" button on manual input
    $('#seller-name, #seller-inn').on('input', function() {
        const name = $('#seller-name').val().trim();
        const inn = $('#seller-inn').val().trim();
        if (name && inn && inn.length >= 10) {
            $('#save-seller-btn').addClass('show');
        } else {
            $('#save-seller-btn').removeClass('show');
        }
    });
    
    // Save seller to organizations
    $('#save-seller-btn').on('click', async function() {
        const data = {
            org_type: $('#seller-inn').val().length === 12 ? 'ip' : 'ooo',
            name: $('#seller-name').val(),
            inn: $('#seller-inn').val(),
            kpp: $('#seller-kpp').val() || null,
            address: $('#seller-address').val()
        };
        
        try {
            const response = await fetch('/api/v1/organizations', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (!response.ok) throw new Error('API error');
        } catch (error) {
            // Fallback to localStorage
            const orgs = JSON.parse(localStorage.getItem('organizations') || '[]');
            data.id = 'org_' + Date.now();
            orgs.push(data);
            localStorage.setItem('organizations', JSON.stringify(orgs));
        }
        
        const toast = $('<div class="position-fixed top-0 end-0 m-24 p-16 bg-success-100 text-success-main shadow-lg" style="z-index: 9999;"><div class="d-flex align-items-center gap-8"><iconify-icon icon="mdi:check-circle" class="text-xl"></iconify-icon><span>Организация добавлена!</span></div></div>');
        $('body').append(toast);
        setTimeout(() => toast.fadeOut(300, function() { $(this).remove(); }), 2000);
        $('#save-seller-btn').removeClass('show');
    });
    
    // Show "Add to clients" button on manual buyer input
    $('#buyer-name, #buyer-inn').on('input', function() {
        const name = $('#buyer-name').val().trim();
        const inn = $('#buyer-inn').val().trim();
        if (name && inn && inn.length >= 10) {
            $('#save-buyer-btn').addClass('show');
        } else {
            $('#save-buyer-btn').removeClass('show');
        }
    });
    
    // Save buyer to clients
    $('#save-buyer-btn').on('click', async function() {
        const data = {
            org_type: $('#buyer-inn').val().length === 12 ? 'ip' : 'ooo',
            name: $('#buyer-name').val(),
            inn: $('#buyer-inn').val(),
            kpp: $('#buyer-kpp').val() || null,
            address: $('#buyer-address').val()
        };
        
        try {
            const response = await fetch('/api/v1/contractors', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (!response.ok) throw new Error('API error');
        } catch (error) {
            // Fallback to localStorage
            const contractors = JSON.parse(localStorage.getItem('contractors') || '[]');
            data.id = 'contractor_' + Date.now();
            contractors.push(data);
            localStorage.setItem('contractors', JSON.stringify(contractors));
        }
        
        const toast = $('<div class="position-fixed top-0 end-0 m-24 p-16 bg-success-100 text-success-main shadow-lg" style="z-index: 9999;"><div class="d-flex align-items-center gap-8"><iconify-icon icon="mdi:check-circle" class="text-xl"></iconify-icon><span>Контрагент добавлен!</span></div></div>');
        $('body').append(toast);
        setTimeout(() => toast.fadeOut(300, function() { $(this).remove(); }), 2000);
        $('#save-buyer-btn').removeClass('show');
    });
    
    // Show "Add to contracts" button when transfer-basis is filled
    $('#transfer-basis').on('input', function() {
        const value = $(this).val().trim();
        if (value.length > 5) {
            $('#add-contract-btn').removeClass('d-none');
        } else {
            $('#add-contract-btn').addClass('d-none');
        }
    });
    
    // Add contract to list
    $('#add-contract-btn').on('click', function() {
        const contract = {
            name: $('#transfer-basis').val(),
            buyer_inn: $('#buyer-inn').val(),
            buyer_name: $('#buyer-name').val()
        };
        // TODO: Save to API/localStorage
        const toast = $('<div class="position-fixed top-0 end-0 m-24 p-16 bg-success-100 text-success-main shadow-lg" style="z-index: 9999;"><div class="d-flex align-items-center gap-8"><iconify-icon icon="mdi:check-circle" class="text-xl"></iconify-icon><span>Договор добавлен!</span></div></div>');
        $('body').append(toast);
        setTimeout(() => toast.fadeOut(300, function() { $(this).remove(); }), 2000);
        $('#add-contract-btn').addClass('d-none');
    });
    
    // Set today's date for receiving
    $('#set-today-receiving').on('click', function() {
        const today = new Date();
        const formattedDate = today.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' });
        $('#receiving-date').val(formattedDate);
        updatePreview();
    });
    
    // Set today's date for shipping
    $('#set-today-shipping').on('click', function() {
        const today = new Date();
        const formattedDate = today.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' });
        $('#shipping-date').val(formattedDate);
        updatePreview();
    });
    
    // Consignor (грузоотправитель) radio handlers
    $('input[name="consignor-type"]').on('change', function() {
        const value = $(this).val();
        const input = $('#consignor-address');
        
        if (value === 'none') {
            input.val('').prop('disabled', true);
        } else if (value === 'same') {
            input.val($('#seller-name').val() + ', ' + $('#seller-address').val());
            input.prop('disabled', true);
        } else if (value === 'manual') {
            input.val('').prop('disabled', false).focus();
        }
        updatePreview();
    });
    
    // Consignee (грузополучатель) radio handlers
    $('input[name="consignee-type"]').on('change', function() {
        const value = $(this).val();
        const input = $('#consignee-address');
        
        if (value === 'none') {
            input.val('').prop('disabled', true);
        } else if (value === 'same') {
            input.val($('#buyer-name').val() + ', ' + $('#buyer-address').val());
            input.prop('disabled', true);
        } else if (value === 'manual') {
            input.val('').prop('disabled', false).focus();
        }
        updatePreview();
    });
    
    // Update consignor if seller changes (when "same" selected)
    $('#seller-name, #seller-address').on('input', function() {
        if ($('#consignor-same').is(':checked')) {
            $('#consignor-address').val($('#seller-name').val() + ', ' + $('#seller-address').val());
        }
    });
    
    // Update consignee if buyer changes (when "same" selected)
    $('#buyer-name, #buyer-address').on('input', function() {
        if ($('#consignee-same').is(':checked')) {
            $('#consignee-address').val($('#buyer-name').val() + ', ' + $('#buyer-address').val());
        }
    });

    // Product row counter
    let productRowCount = 1;

    // Add new product row
    $('#add-product').on('click', function() {
        productRowCount++;
        
        const newRow = `
            <div class="product-row card border radius-12 p-16 mb-16" data-row="${productRowCount}">
                <div class="row g-12 align-items-end">
                    <div class="col">
                        <label class="form-label text-sm mb-4">Наименование <span class="text-danger">*</span></label>
                        <input type="text" class="form-control product-name" placeholder="Название товара или услуги" required>
                    </div>
                    <div class="col-auto" style="width: 100px;">
                        <label class="form-label text-sm mb-4">Кол-во</label>
                        <input type="number" class="form-control product-qty" value="1" min="0.01" step="0.01">
                    </div>
                    <div class="col-auto" style="width: 110px;">
                        <label class="form-label text-sm mb-4">Ед. изм.</label>
                        <select class="form-select product-unit">
                            <option value="шт">шт</option>
                            <option value="усл">усл</option>
                            <option value="ч">ч</option>
                            <option value="кг">кг</option>
                            <option value="л">л</option>
                            <option value="м">м</option>
                            <option value="м2">м2</option>
                            <option value="м3">м3</option>
                        </select>
                    </div>
                    <div class="col-auto" style="width: 120px;">
                        <label class="form-label text-sm mb-4">Цена</label>
                        <input type="number" class="form-control product-price" value="0" min="0" step="0.01">
                    </div>
                    <div class="col-auto" style="width: 120px;">
                        <label class="form-label text-sm mb-4">Сумма</label>
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
    });

    // Remove product row
    $(document).on('click', '.remove-product', function() {
        if ($('.product-row').length > 1) {
            $(this).closest('.product-row').remove();
            calculateTotals();
            updatePreview();
        } else {
            if (typeof toastWarning === 'function') {
                toastWarning('Должна остаться хотя бы одна позиция');
            }
        }
    });

    // Calculate totals on input change
    $(document).on('input change', '.product-qty, .product-price, .product-vat', function() {
        calculateTotals();
        updatePreview();
    });

    // Calculate totals
    function calculateTotals() {
        let totalWithoutVat = 0;
        let totalVat = 0;
        
        // Берем НДС из настроек по умолчанию
        const vatRate = $('#default-vat').val();
        const vatType = $('#default-vat-type').val() || 'on-top';

        $('.product-row').each(function() {
            const qty = parseFloat($(this).find('.product-qty').val()) || 0;
            const price = parseFloat($(this).find('.product-price').val()) || 0;
            
            let subtotal, vat, total;
            
            if (vatRate !== 'none') {
                const vatPercent = parseFloat(vatRate) / 100;
                
                if (vatType === 'included') {
                    // НДС включен в цену
                    total = qty * price;
                    subtotal = total / (1 + vatPercent);
                    vat = total - subtotal;
                } else {
                    // НДС сверху
                    subtotal = qty * price;
                    vat = subtotal * vatPercent;
                    total = subtotal + vat;
                }
            } else {
                subtotal = qty * price;
                vat = 0;
                total = subtotal;
            }
            
            $(this).find('.product-total').val(formatCurrency(total));
            
            totalWithoutVat += subtotal;
            totalVat += vat;
        });

        $('#total-without-vat').text(formatCurrency(totalWithoutVat));
        $('#total-vat').text(formatCurrency(totalVat));
        $('#total-with-vat').text(formatCurrency(totalWithoutVat + totalVat));
    }

    // Format currency
    function formatCurrency(amount) {
        return new Intl.NumberFormat('ru-RU', {
            style: 'currency',
            currency: 'RUB',
            minimumFractionDigits: 2
        }).format(amount);
    }

    // Update preview - теперь загружает реальную форму через API
    let previewDebounceTimer = null;
    let isPreviewUpdating = false;
    function updatePreview() {
        // Debounce - обновляем не чаще чем раз в 1.5 секунды для снижения нагрузки
        clearTimeout(previewDebounceTimer);
        previewDebounceTimer = setTimeout(() => {
            if (typeof loadSidebarPreview === 'function' && !isPreviewUpdating) {
                loadSidebarPreview();
            }
        }, 1500);
    }

    // Live update preview on any input change
    $(document).on('input change', 'input, select, textarea', function() {
        updatePreview();
    });

    // Select company from modal
    $('.select-company').on('click', function() {
        $('#seller-name').val($(this).data('name'));
        $('#seller-inn').val($(this).data('inn'));
        $('#seller-kpp').val($(this).data('kpp'));
        $('#seller-address').val($(this).data('address'));
        $('#selectCompanyModal').modal('hide');
        updatePreview();
    });

    // Select contractor from modal
    $('.select-contractor').on('click', function() {
        $('#buyer-name').val($(this).data('name'));
        $('#buyer-inn').val($(this).data('inn'));
        $('#buyer-kpp').val($(this).data('kpp'));
        $('#buyer-address').val($(this).data('address'));
        $('#selectContractorModal').modal('hide');
        updatePreview();
    });

    // Проверка авторизации пользователя
    function isUserAuthenticated() {
        const token = localStorage.getItem('documatica_token');
        return !!token;
    }

    // Сохранение документа как pending для неавторизованного пользователя (на сервере)
    async function savePendingDocument(requestData) {
        try {
            const response = await fetch('/api/v1/drafts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    document_type: 'upd',
                    document_data: requestData
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                // Сохраняем токен черновика
                localStorage.setItem('documatica_draft_token', data.draft_token);
                localStorage.setItem('documatica_pending_document', JSON.stringify(requestData));
                return data.draft_token;
            }
        } catch (error) {
            console.error('Ошибка сохранения черновика:', error);
        }
        
        // Fallback - сохраняем только в localStorage
        localStorage.setItem('documatica_pending_document', JSON.stringify(requestData));
        return null;
    }
    
    // Обновление UI модалки при сохранении черновика
    function updateModalSaveStatus(success, draftToken) {
        const statusEl = document.getElementById('draft-save-status');
        if (!statusEl) return;
        
        if (success) {
            statusEl.innerHTML = `
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="3">
                        <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                    <span style="color: #166534; font-weight: 600;">Черновик сохранён на сервере</span>
                </div>
            `;
        } else {
            statusEl.innerHTML = `
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <path d="M12 16v-4M12 8h.01"></path>
                    </svg>
                    <span style="color: #92400e; font-weight: 600;">Черновик сохранён локально</span>
                </div>
            `;
        }
    }

    // ============== SAVE DRAFT BUTTON ==============
    // Кнопка "Сохранить черновик"
    $('#save-draft-btn').on('click', async function(e) {
        e.preventDefault();
        
        const btn = $(this);
        const originalText = btn.html();
        btn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm me-8"></span>Сохранение...');
        
        try {
            const requestData = collectFormDataForSubmit();
            const token = localStorage.getItem('documatica_token') || getCookie('access_token');
            
            if (!token) {
                toastError('Необходима авторизация для сохранения документа');
                btn.prop('disabled', false).html(originalText);
                return;
            }
            
            // Проверяем, есть ли уже сохранённый documentId (для обновления)
            const existingDocId = window.savedDocumentId || null;
            
            const response = await fetch('/api/v1/documents/upd/save' + (existingDocId ? `?document_id=${existingDocId}` : ''), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                credentials: 'include',
                body: JSON.stringify(requestData)
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Ошибка сохранения');
            }
            
            const result = await response.json();
            
            // Сохраняем document_id для последующих обновлений
            window.savedDocumentId = result.document_id;
            
            // Активируем кнопку XLS (теперь можно экспортировать)
            $('#export-xls-btn').prop('disabled', false).attr('title', 'Скачать в формате Excel 2003');
            
            toastSuccess(result.message || 'Черновик успешно сохранён');
            
        } catch (error) {
            toastError('Ошибка: ' + error.message);
        } finally {
            btn.prop('disabled', false).html(originalText);
        }
    });
    // ============== END SAVE DRAFT BUTTON ==============

    // Form submit - генерация PDF через API
    $('#upd-form').on('submit', async function(e) {
        e.preventDefault();
        
        // Validate form
        if (!this.checkValidity()) {
            this.reportValidity();
            return;
        }
        
        // Собираем данные формы
        const requestData = collectFormDataForSubmit();
        
        // Проверяем авторизацию
        if (!isUserAuthenticated()) {
            // Показываем модалку сразу (с индикатором загрузки)
            $('#authRequiredModal').modal('show');
            
            // Сохраняем документ на сервере
            const draftToken = await savePendingDocument(requestData);
            
            // Обновляем статус в модалке
            updateModalSaveStatus(!!draftToken, draftToken);
            
            // Добавляем draft_token к ссылкам OAuth
            if (draftToken) {
                const yandexLinks = document.querySelectorAll('#authRequiredModal a[href*="/auth/yandex/login"]');
                yandexLinks.forEach(link => {
                    link.href = `/auth/yandex/login?draft_token=${draftToken}&redirect_to=/dashboard/upd/create/`;
                });
            }
            return;
        }
        
        // Пользователь авторизован - генерируем PDF
        await generateAndDownloadPDF(requestData);
    });
    
    // Функция генерации и скачивания PDF (для авторизованных)
    async function generateAndDownloadPDF(requestData) {
        // ПРОВЕРКА АВТОРИЗАЦИИ - для гостей показываем модалку регистрации
        const token = localStorage.getItem('documatica_token') || getCookie('access_token');
        
        if (!token) {
            // Гость - показываем модалку сразу
            $('#guestRegistrationModal').modal('show');
            
            // Сохраняем данные на сервере
            const draftToken = await savePendingDocument(requestData);
            localStorage.setItem('pending_upd_data', JSON.stringify(requestData));
            
            // Обновляем статус в модалке
            const statusEl = document.querySelector('#guestRegistrationModal #draft-save-status');
            if (statusEl) {
                updateModalSaveStatus(!!draftToken, draftToken);
            }
            
            // Добавляем draft_token к ссылкам OAuth
            if (draftToken) {
                const yandexLinks = document.querySelectorAll('#guestRegistrationModal a[href*="/auth/yandex/login"]');
                yandexLinks.forEach(link => {
                    link.href = `/auth/yandex/login?draft_token=${draftToken}&redirect_to=/dashboard/upd/create/`;
                });
            }
            return;
        }
        
        const submitBtn = $('#upd-form').find('button[type="submit"]');
        const originalText = submitBtn.html();
        submitBtn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm me-8"></span>Генерация...');
        
        try {
            const API_URL = '';
            const token = localStorage.getItem('documatica_token');
            const response = await fetch(`${API_URL}/api/v1/documents/upd/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': token ? `Bearer ${token}` : ''
                },
                body: JSON.stringify(requestData)
            });
            
            if (!response.ok) {
                const error = await response.json();
                // Обработка разных форматов ошибок
                let errorMessage = 'Ошибка генерации';
                if (typeof error.detail === 'string') {
                    errorMessage = error.detail;
                } else if (Array.isArray(error.detail)) {
                    // Pydantic validation errors
                    errorMessage = error.detail.map(e => {
                        const field = e.loc ? e.loc.join(' -> ') : 'поле';
                        return `${field}: ${e.msg}`;
                    }).join('; ');
                } else if (error.detail) {
                    errorMessage = JSON.stringify(error.detail);
                }
                throw new Error(errorMessage);
            }
            
            // Проверяем тип ответа
            const contentType = response.headers.get('content-type');
            
            if (contentType && contentType.includes('text/html')) {
                // Сервер вернул HTML (WeasyPrint недоступен) - открываем в новом окне для печати
                const html = await response.text();
                const printWindow = window.open('', '_blank');
                printWindow.document.write(html);
                printWindow.document.close();
                
                // Автоматически открываем диалог печати после загрузки
                printWindow.onload = function() {
                    setTimeout(function() {
                        printWindow.print();
                    }, 500);
                };
                
                toastSuccess('Для сохранения в PDF выберите "Сохранить как PDF" в диалоге печати');
            } else {
                // Скачиваем PDF
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `UPD_${requestData.document_number}_${requestData.document_date.replace(/-/g, '')}.pdf`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                a.remove();
                toastSuccess('УПД успешно сгенерирован и скачан!');
            }
            
            // Сохраняем документ в личном кабинете
            try {
                const saveResponse = await fetch(`${API_URL}/api/v1/documents/upd/save`, {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Authorization': token ? `Bearer ${token}` : ''
                    },
                    body: JSON.stringify(requestData)
                });
                
                if (saveResponse.ok) {
                    const saveResult = await saveResponse.json();
                    console.log('Документ сохранён:', saveResult.document_id);
                    
                    // Сохраняем ID документа и активируем кнопку XLS
                    window.savedDocumentId = saveResult.document_id;
                    
                    const xlsBtn = $('#export-xls-btn');
                    console.log('XLS button found:', xlsBtn.length > 0);
                    
                    if (xlsBtn.length > 0) {
                        xlsBtn.prop('disabled', false).attr('title', 'Скачать Excel файл');
                        console.log('XLS button activated');
                    } else {
                        console.error('XLS button not found in DOM');
                    }
                }
            } catch (saveError) {
                console.log('Не удалось сохранить документ:', saveError);
            }
            
        } catch (error) {
            console.error('Error:', error);
            toastError('Ошибка: ' + error.message);
        } finally {
            submitBtn.prop('disabled', false).html(originalText);
        }
    }
    
    // Вспомогательная функция для получения cookie
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }
    
    // Собираем данные формы (вынесено в отдельную функцию)
    function collectFormDataForSubmit() {
        const items = [];
        let rowNum = 1;
        
        // Берем НДС и страну из настроек по умолчанию
        const vatRate = $('#default-vat').val();
        const vatType = $('#default-vat-type').val();
        const defaultCountry = $('#default-country').val() || 'Россия';
        const defaultCountryCode = $('#default-country-code').val() || '643';
        
        $('.product-row').each(function() {
            const qty = parseFloat($(this).find('.product-qty').val()) || 0;
            const price = parseFloat($(this).find('.product-price').val()) || 0;
            let amountWithoutVat, vatAmount, amountWithVat;
            
            let vatMultiplier = 0;
            let vatRateStr = 'без НДС';
            if (vatRate === '22') { vatMultiplier = 0.22; vatRateStr = '22%'; }
            else if (vatRate === '20') { vatMultiplier = 0.20; vatRateStr = '20%'; }
            else if (vatRate === '18') { vatMultiplier = 0.18; vatRateStr = '18%'; }
            else if (vatRate === '10') { vatMultiplier = 0.10; vatRateStr = '10%'; }
            else if (vatRate === '7') { vatMultiplier = 0.07; vatRateStr = '7%'; }
            else if (vatRate === '5') { vatMultiplier = 0.05; vatRateStr = '5%'; }
            else if (vatRate === '0') { vatMultiplier = 0; vatRateStr = '0%'; }
            
            if (vatType === 'included' && vatRate !== 'none') {
                // НДС включен в цену
                amountWithVat = qty * price;
                amountWithoutVat = amountWithVat / (1 + vatMultiplier);
                vatAmount = amountWithVat - amountWithoutVat;
            } else {
                // НДС сверху
                amountWithoutVat = qty * price;
                vatAmount = amountWithoutVat * vatMultiplier;
                amountWithVat = amountWithoutVat + vatAmount;
            }
            
            items.push({
                row_number: rowNum++,
                name: $(this).find('.product-name').val() || 'Товар',
                unit_code: null,
                unit_name: $(this).find('.product-unit').val() || 'шт',
                quantity: qty,
                price: price,
                price_without_vat: price,  // Для XLS экспорта
                amount_without_vat: amountWithoutVat,
                vat_rate: vatRateStr,
                vat_amount: vatAmount,
                amount_with_vat: amountWithVat,
                country_code: defaultCountryCode,
                country_name: defaultCountry
            });
        });
        
        // Считаем итоги
        let totalWithoutVat = 0, totalVat = 0, totalWithVat = 0;
        items.forEach(item => {
            totalWithoutVat += item.amount_without_vat;
            totalVat += item.vat_amount;
            totalWithVat += item.amount_with_vat;
        });
        
        // Формируем запрос к API
        const correctionNumber = $('#correction-number').val()?.trim();
        const correctionDate = $('#correction-date').val()?.trim();
        
        // Грузоотправитель
        let consignorValue = null;
        const consignorType = $('input[name="consignor-type"]:checked').val();
        if (consignorType === 'same') {
            consignorValue = $('#seller-name').val() + ', ' + $('#seller-address').val();
        } else if (consignorType === 'manual') {
            consignorValue = $('#consignor-address').val() || null;
        }
        
        // Грузополучатель
        let consigneeValue = null;
        const consigneeType = $('input[name="consignee-type"]:checked').val();
        if (consigneeType === 'same') {
            consigneeValue = $('#buyer-name').val() + ', ' + $('#buyer-address').val();
        } else if (consigneeType === 'manual') {
            consigneeValue = $('#consignee-address').val() || null;
        }
        
        return {
            document_number: $('#upd-number').val(),
            document_date: convertDateToISO($('#upd-date').val()),
            correction_number: correctionNumber || null,
            correction_date: correctionDate ? convertDateToISO(correctionDate) : null,
            status: parseInt($('input[name="upd-status"]:checked').val()) || 1,
            seller: {
                name: $('#seller-name').val(),
                inn: $('#seller-inn').val(),
                kpp: $('#seller-kpp').val() || null,
                address: $('#seller-address').val()
            },
            buyer: {
                name: $('#buyer-name').val(),
                inn: $('#buyer-inn').val(),
                kpp: $('#buyer-kpp').val() || null,
                address: $('#buyer-address').val()
            },
            consignor: consignorValue,
            consignee: consigneeValue,
            items: items,
            total_amount_without_vat: totalWithoutVat,
            total_vat_amount: totalVat,
            total_amount_with_vat: totalWithVat,
            currency_code: $('#currency-code').val() || '643',
            currency_name: $('#currency-name').val() || 'Российский рубль',
            gov_contract_id: $('#gov-contract-id').val() || null,
            payment_document: $('#payment-document').val() || null,
            shipping_document: $('#shipping-document').val() || null,
            contract_info: $('#transfer-basis').val() || null,
            transport_info: $('#transport-info').val() || null,
            shipping_date: $('#shipping-date').val() ? convertDateToISO($('#shipping-date').val()) : null,
            receiving_date: $('#receiving-date').val() ? convertDateToISO($('#receiving-date').val()) : null,
            other_shipping_info: $('#other-shipping-info').val() || null,
            other_receiving_info: $('#other-receiving-info').val() || null,
            seller_signer: $('#released-by').val() ? {
                position: $('#released-position').val() || 'Директор',
                full_name: $('#released-by').val(),
                basis: 'Устав',
                signature_image: selectedSellerOrg?.director_signature || null
            } : null,
            seller_responsible: $('#responsible-name').val() ? {
                position: $('#responsible-position').val() || null,
                full_name: $('#responsible-name').val()
            } : null,
            economic_entity: $('#economic-entity').val() || null,
            seller_stamp_image: selectedSellerOrg?.stamp_base64 || null,
            seller_org_type: getOrgTypeByInn($('#seller-inn').val()),
            accountant_name: selectedSellerOrg?.accountant_name || null,
            accountant_signature: selectedSellerOrg?.accountant_signature || null,
            buyer_signer: $('#received-by').val() ? {
                position: $('#received-position').val() || 'Директор',
                full_name: $('#received-by').val(),
                basis: 'Устав'
            } : null,
            buyer_responsible: $('#buyer-responsible-name').val() ? {
                position: $('#buyer-responsible-position').val() || null,
                full_name: $('#buyer-responsible-name').val()
            } : null,
            buyer_economic_entity: $('#buyer-economic-entity').val() || null
        };
    }
    
    // Конвертация даты DD.MM.YYYY в YYYY-MM-DD
    function convertDateToISO(dateStr) {
        if (!dateStr) return new Date().toISOString().split('T')[0];
        const parts = dateStr.split('.');
        if (parts.length === 3) {
            return `${parts[2]}-${parts[1]}-${parts[0]}`;
        }
        return dateStr;
    }
    
    // Функция показа ошибки под инпутом
    function showInputError(inputId, message) {
        const input = $(`#${inputId}`);
        const errorContainer = $(`#${inputId}-error`);
        const errorContainerWrapper = $(`#${inputId}-error-container`);
        
        input.addClass('is-invalid');
        
        if (errorContainer.length && errorContainerWrapper.length) {
            // Используем существующий контейнер
            errorContainer.text(message);
            errorContainerWrapper.removeClass('d-none');
        } else {
            // Создаём новый контейнер (fallback)
            const errorDiv = $(`<div class="invalid-feedback" id="${inputId}-error" style="display: block;">${message}</div>`);
            input.closest('.col-md-3, .col-md-6, .col-12').append(errorDiv);
        }
        
        // Автоматически убираем ошибку через 5 секунд
        setTimeout(() => {
            clearInputError(inputId);
        }, 5000);
    }
    
    // Функция очистки ошибки под инпутом
    function clearInputError(inputId) {
        const input = $(`#${inputId}`);
        const errorContainer = $(`#${inputId}-error`);
        const errorContainerWrapper = $(`#${inputId}-error-container`);
        
        input.removeClass('is-invalid');
        
        if (errorContainerWrapper.length) {
            errorContainerWrapper.addClass('d-none');
            errorContainer.text('');
        } else {
            errorContainer.fadeOut(300, function() {
                $(this).text('').hide();
            });
        }
    }
    
    // Функция загрузки данных шаблона в форму
    function loadTemplateData(data) {
        if (!data) return;
        
        // Конвертация даты YYYY-MM-DD в DD.MM.YYYY
        function convertDateFromISO(dateStr) {
            if (!dateStr) return '';
            const parts = dateStr.split('-');
            if (parts.length === 3) {
                return `${parts[2]}.${parts[1]}.${parts[0]}`;
            }
            return dateStr;
        }
        
        // Document info - не заполняем номер и дату, чтобы были новые
        // $('#upd-number').val(data.document_number || '');
        // $('#upd-date').val(convertDateFromISO(data.document_date) || '');
        if (data.status) {
            $(`input[name="upd-status"][value="${data.status}"]`).prop('checked', true);
        }
        
        // Seller info
        if (data.seller) {
            $('#seller-name').val(data.seller.name || '');
            $('#seller-inn').val(data.seller.inn || '');
            $('#seller-kpp').val(data.seller.kpp || '');
            $('#seller-address').val(data.seller.address || '');
        }
        
        // Buyer info
        if (data.buyer) {
            $('#buyer-name').val(data.buyer.name || '');
            $('#buyer-inn').val(data.buyer.inn || '');
            $('#buyer-kpp').val(data.buyer.kpp || '');
            $('#buyer-address').val(data.buyer.address || '');
        }
        
        // Currency
        $('#currency-name').val(data.currency_name || 'Российский рубль');
        $('#currency-code').val(data.currency_code || '643');
        $('#gov-contract-id').val(data.gov_contract_id || '');
        
        // Documents
        $('#payment-document').val(data.payment_document || '');
        $('#shipping-document').val(data.shipping_document || '');
        
        // Contract info
        $('#transfer-basis').val(data.contract_info || '');
        $('#transport-info').val(data.transport_info || '');
        $('#other-shipping-info').val(data.other_shipping_info || '');
        $('#other-receiving-info').val(data.other_receiving_info || '');
        
        // Seller signer
        if (data.seller_signer) {
            $('#released-position').val(data.seller_signer.position || '');
            $('#released-by').val(data.seller_signer.full_name || '');
        }
        if (data.seller_responsible) {
            $('#responsible-position').val(data.seller_responsible.position || '');
            $('#responsible-name').val(data.seller_responsible.full_name || '');
        }
        $('#economic-entity').val(data.economic_entity || '');
        
        // Buyer signer
        if (data.buyer_signer) {
            $('#received-position').val(data.buyer_signer.position || '');
            $('#received-by').val(data.buyer_signer.full_name || '');
        }
        if (data.buyer_responsible) {
            $('#buyer-responsible-position').val(data.buyer_responsible.position || '');
            $('#buyer-responsible-name').val(data.buyer_responsible.full_name || '');
        }
        $('#buyer-economic-entity').val(data.buyer_economic_entity || '');
        
        // Products
        if (data.items && data.items.length > 0) {
            $('#products-container').empty();
            productRowCount = 0;
            
            data.items.forEach((item, index) => {
                productRowCount++;
                const row = createProductRow(productRowCount, item);
                $('#products-container').append(row);
            });
        }
        
        // Recalculate
        calculateTotals();
        updatePreview();
    }
    
    // Функция загрузки данных для редактирования (заполняет все поля включая номер и дату)
    function loadFormDataForEdit(data) {
        if (!data) return;
        
        // Конвертация даты YYYY-MM-DD в DD.MM.YYYY
        function convertDateFromISO(dateStr) {
            if (!dateStr) return '';
            const parts = dateStr.split('-');
            if (parts.length === 3) {
                return `${parts[2]}.${parts[1]}.${parts[0]}`;
            }
            return dateStr;
        }
        
        // Document info - заполняем номер и дату
        $('#upd-number').val(data.document_number || '');
        $('#upd-date').val(convertDateFromISO(data.document_date) || '');
        $('#correction-number').val(data.correction_number || '');
        $('#correction-date').val(convertDateFromISO(data.correction_date) || '');
        
        if (data.status) {
            $(`input[name="upd-status"][value="${data.status}"]`).prop('checked', true);
        }
        
        // Seller info
        if (data.seller) {
            $('#seller-name').val(data.seller.name || '');
            $('#seller-inn').val(data.seller.inn || '');
            $('#seller-kpp').val(data.seller.kpp || '');
            $('#seller-address').val(data.seller.address || '');
        }
        
        // Buyer info
        if (data.buyer) {
            $('#buyer-name').val(data.buyer.name || '');
            $('#buyer-inn').val(data.buyer.inn || '');
            $('#buyer-kpp').val(data.buyer.kpp || '');
            $('#buyer-address').val(data.buyer.address || '');
        }
        
        // Currency
        $('#currency-name').val(data.currency_name || 'Российский рубль');
        $('#currency-code').val(data.currency_code || '643');
        $('#gov-contract-id').val(data.gov_contract_id || '');
        
        // Documents
        $('#payment-document').val(data.payment_document || '');
        $('#shipping-document').val(data.shipping_document || '');
        
        // Contract info
        $('#transfer-basis').val(data.contract_info || '');
        $('#transport-info').val(data.transport_info || '');
        $('#other-shipping-info').val(data.other_shipping_info || '');
        $('#other-receiving-info').val(data.other_receiving_info || '');
        
        // Seller signer
        if (data.seller_signer) {
            $('#released-position').val(data.seller_signer.position || '');
            $('#released-by').val(data.seller_signer.full_name || '');
        }
        
        // Seller responsible
        if (data.seller_responsible) {
            $('#responsible-position').val(data.seller_responsible.position || '');
            $('#responsible-name').val(data.seller_responsible.full_name || '');
        }
        $('#economic-entity').val(data.economic_entity || '');
        
        // Shipping date
        $('#shipping-date').val(convertDateFromISO(data.shipping_date) || '');
        
        // Buyer signer
        if (data.buyer_signer) {
            $('#received-position').val(data.buyer_signer.position || '');
            $('#received-by').val(data.buyer_signer.full_name || '');
        }
        
        // Buyer responsible
        if (data.buyer_responsible) {
            $('#buyer-responsible-position').val(data.buyer_responsible.position || '');
            $('#buyer-responsible-name').val(data.buyer_responsible.full_name || '');
        }
        $('#buyer-economic-entity').val(data.buyer_economic_entity || '');
        
        // Receiving date
        $('#receiving-date').val(convertDateFromISO(data.receiving_date) || '');
        
        // Consignor (грузоотправитель)
        if (data.consignor) {
            $('#consignor-manual').prop('checked', true);
            $('#consignor-address').val(data.consignor).prop('disabled', false);
        }
        
        // Consignee (грузополучатель)
        if (data.consignee) {
            $('#consignee-manual').prop('checked', true);
            $('#consignee-address').val(data.consignee).prop('disabled', false);
        }
        
        // Products
        if (data.items && data.items.length > 0) {
            $('#products-container').empty();
            productRowCount = 0;
            
            data.items.forEach((item, index) => {
                productRowCount++;
                const row = createProductRow(productRowCount, item);
                $('#products-container').append(row);
            });
        }
        
        // Recalculate
        calculateTotals();
        updatePreview();
    }
    
    // Создание строки товара
    function createProductRow(rowNum, item = {}) {
        return `
            <div class="product-row card border radius-12 p-16 mb-16" data-row="${rowNum}">
                <div class="row g-12 align-items-end">
                    <div class="col">
                        <label class="form-label text-sm mb-4">Наименование <span class="text-danger">*</span></label>
                        <input type="text" class="form-control product-name" value="${item.name || ''}" placeholder="Название товара или услуги" required>
                    </div>
                    <div class="col-auto" style="width: 100px;">
                        <label class="form-label text-sm mb-4">Кол-во</label>
                        <input type="number" class="form-control product-qty" value="${item.quantity || 1}" min="0.01" step="0.01">
                    </div>
                    <div class="col-auto" style="width: 90px;">
                        <label class="form-label text-sm mb-4">Ед. изм.</label>
                        <select class="form-select product-unit">
                            <option value="шт" ${item.unit_name === 'шт' ? 'selected' : ''}>шт</option>
                            <option value="усл" ${item.unit_name === 'усл' ? 'selected' : ''}>усл</option>
                            <option value="ч" ${item.unit_name === 'ч' ? 'selected' : ''}>ч</option>
                            <option value="кг" ${item.unit_name === 'кг' ? 'selected' : ''}>кг</option>
                            <option value="л" ${item.unit_name === 'л' ? 'selected' : ''}>л</option>
                            <option value="м" ${item.unit_name === 'м' ? 'selected' : ''}>м</option>
                            <option value="м2" ${item.unit_name === 'м2' ? 'selected' : ''}>м2</option>
                            <option value="м3" ${item.unit_name === 'м3' ? 'selected' : ''}>м3</option>
                        </select>
                    </div>
                    <div class="col-auto" style="width: 120px;">
                        <label class="form-label text-sm mb-4">Цена</label>
                        <input type="number" class="form-control product-price" value="${item.price || 0}" min="0" step="0.01">
                    </div>
                    <div class="col-auto">
                        <button type="button" class="btn btn-outline-danger remove-product" title="Удалить">
                            <iconify-icon icon="mdi:trash-can-outline"></iconify-icon>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    // Сохранить как шаблон
    $('#save-template').on('click', async function() {
        const formData = collectFormData();
        
        // Формируем название шаблона
        const templateName = formData.seller.name + ' - ' + (formData.buyer.name || 'Шаблон');
        
        const btn = $(this);
        btn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm me-1"></span>Сохранение...');
        
        try {
            const response = await fetch('/api/v1/templates/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                    name: templateName,
                    doc_type: 'upd',
                    data: formData
                })
            });
            
            if (response.ok) {
                toastSuccess('Шаблон успешно сохранен!');
            } else {
                const err = await response.json();
                toastError(err.detail || 'Ошибка сохранения шаблона');
            }
        } catch (error) {
            console.error('Error saving template:', error);
            toastError('Ошибка сохранения: ' + error.message);
        } finally {
            btn.prop('disabled', false).html('Сохранить как шаблон');
        }
    });
    
    // Сохранить черновик
    $('#save-draft').on('click', function() {
        const formData = collectFormData();
        localStorage.setItem('upd_draft', JSON.stringify(formData));
        toastSuccess('Черновик сохранен!');
    });

    // Initial calculations
    calculateTotals();
    updatePreview();
    
    // Функция для сбора данных формы
    function collectFormData() {
        const items = [];
        let rowNum = 1;
        
        // Берем НДС и страну из настроек по умолчанию
        const vatRate = $('#default-vat').val();
        const vatType = $('#default-vat-type').val() || 'on-top';
        const defaultCountry = $('#default-country').val() || 'Россия';
        const defaultCountryCode = $('#default-country-code').val() || '643';
        
        $('.product-row').each(function() {
            const qty = parseFloat($(this).find('.product-qty').val()) || 0;
            const price = parseFloat($(this).find('.product-price').val()) || 0;
            
            let amountWithoutVat, vatAmount, amountWithVat;
            let vatRateStr = 'Без НДС';
            
            if (vatRate !== 'none') {
                vatRateStr = vatRate + '%';
                const vatPercent = parseFloat(vatRate) / 100;
                
                if (vatType === 'included') {
                    // НДС включен в цену
                    amountWithVat = qty * price;
                    amountWithoutVat = amountWithVat / (1 + vatPercent);
                    vatAmount = amountWithVat - amountWithoutVat;
                } else {
                    // НДС сверху
                    amountWithoutVat = qty * price;
                    vatAmount = amountWithoutVat * vatPercent;
                    amountWithVat = amountWithoutVat + vatAmount;
                }
            } else {
                amountWithoutVat = qty * price;
                vatAmount = 0;
                amountWithVat = amountWithoutVat;
            }
            
            items.push({
                row_number: rowNum++,
                name: $(this).find('.product-name').val() || 'Товар',
                unit_code: '796',
                unit_name: $(this).find('.product-unit').val() || 'шт',
                quantity: qty,
                price: price,
                amount_without_vat: amountWithoutVat,
                vat_rate: vatRateStr,
                vat_amount: vatAmount,
                amount_with_vat: amountWithVat,
                country_code: defaultCountryCode,
                country_name: defaultCountry
            });
        });
        
        let totalWithoutVat = 0, totalVat = 0, totalWithVat = 0;
        items.forEach(item => {
            totalWithoutVat += item.amount_without_vat;
            totalVat += item.vat_amount;
            totalWithVat += item.amount_with_vat;
        });
        
        // Значения по умолчанию для обязательных полей
        const sellerName = $('#seller-name').val() || 'Продавец';
        const sellerInn = $('#seller-inn').val() || '0000000000';
        const sellerAddress = $('#seller-address').val() || 'Адрес не указан';
        const buyerName = $('#buyer-name').val() || 'Покупатель';
        const buyerInn = $('#buyer-inn').val() || '0000000000';
        const buyerAddress = $('#buyer-address').val() || 'Адрес не указан';
        
        // Грузоотправитель
        let consignorValue = null;
        const consignorType = $('input[name="consignor-type"]:checked').val();
        if (consignorType === 'same') {
            consignorValue = sellerName + ', ' + sellerAddress;
        } else if (consignorType === 'manual') {
            consignorValue = $('#consignor-address').val() || null;
        }
        
        // Грузополучатель
        let consigneeValue = null;
        const consigneeType = $('input[name="consignee-type"]:checked').val();
        if (consigneeType === 'same') {
            consigneeValue = buyerName + ', ' + buyerAddress;
        } else if (consigneeType === 'manual') {
            consigneeValue = $('#consignee-address').val() || null;
        }
        
        return {
            document_number: $('#upd-number').val() || '1',
            document_date: convertDateToISO($('#upd-date').val()),
            status: parseInt($('input[name="upd-status"]:checked').val()) || 1,
            correction_number: $('#correction-number').val() || null,
            correction_date: $('#correction-date').val() ? convertDateToISO($('#correction-date').val()) : null,
            seller: {
                name: sellerName,
                inn: sellerInn,
                kpp: $('#seller-kpp').val() || null,
                address: sellerAddress
            },
            buyer: {
                name: buyerName,
                inn: buyerInn,
                kpp: $('#buyer-kpp').val() || null,
                address: buyerAddress
            },
            consignor: consignorValue,
            consignee: consigneeValue,
            payment_document: $('#payment-document').val() || null,
            shipping_document: $('#shipping-document').val() || null,
            items: items.length > 0 ? items : [{
                row_number: 1,
                name: 'Товар',
                unit_code: '796',
                unit_name: 'шт',
                quantity: 1,
                price: 0,
                amount_without_vat: 0,
                vat_rate: '20%',
                vat_amount: 0,
                amount_with_vat: 0,
                country_code: '643',
                country_name: 'Россия'
            }],
            total_amount_without_vat: totalWithoutVat,
            total_vat_amount: totalVat,
            total_amount_with_vat: totalWithVat,
            currency_code: $('#currency-code').val() || '643',
            currency_name: $('#currency-name').val() || 'Российский рубль',
            gov_contract_id: $('#gov-contract-id').val() || null,
            contract_info: $('#transfer-basis').val() || null,
            transport_info: $('#transport-info').val() || null,
            shipping_date: $('#shipping-date').val() ? convertDateToISO($('#shipping-date').val()) : null,
            other_shipping_info: $('#other-shipping-info').val() || null,
            seller_signer: $('#released-by').val() ? {
                position: $('#released-position').val() || 'Директор',
                full_name: $('#released-by').val(),
                basis: 'Устав',
                signature_image: selectedSellerOrg?.director_signature || null
            } : null,
            seller_responsible: $('#responsible-name').val() ? {
                position: $('#responsible-position').val() || null,
                full_name: $('#responsible-name').val()
            } : null,
            economic_entity: $('#economic-entity').val() || null,
            seller_stamp_image: selectedSellerOrg?.stamp_base64 || null,
            seller_org_type: getOrgTypeByInn($('#seller-inn').val()),
            accountant_name: selectedSellerOrg?.accountant_name || null,
            accountant_signature: selectedSellerOrg?.accountant_signature || null,
            receiving_date: $('#receiving-date').val() ? convertDateToISO($('#receiving-date').val()) : null,
            other_receiving_info: $('#other-receiving-info').val() || null,
            buyer_signer: $('#received-by').val() ? {
                position: $('#received-position').val() || 'Директор',
                full_name: $('#received-by').val(),
                basis: 'Устав'
            } : null,
            buyer_responsible: $('#buyer-responsible-name').val() ? {
                position: $('#buyer-responsible-position').val() || null,
                full_name: $('#buyer-responsible-name').val()
            } : null,
            buyer_economic_entity: $('#buyer-economic-entity').val() || null
        };
    }
    
    // Загрузка предпросмотра в iframe при открытии модалки
    $('#previewModal').on('shown.bs.modal', async function() {
        const iframe = document.getElementById('preview-iframe');
        const requestData = collectFormData();
        
        try {
            const API_URL = '';
            const response = await fetch(`${API_URL}/api/v1/documents/upd/preview`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData)
            });
            
            if (!response.ok) {
                throw new Error('Ошибка генерации предпросмотра');
            }
            
            const html = await response.text();
            iframe.srcdoc = html;
        } catch (error) {
            iframe.srcdoc = '<html><body style="padding:20px;font-family:Arial;"><h3>Ошибка загрузки</h3><p>' + error.message + '</p></body></html>';
        }
    });
    
    // Скачать PDF из модалки
    $('#modal-download-pdf').on('click', function() {
        $('#upd-form').submit();
        $('#previewModal').modal('hide');
    });
    
    // Функция для загрузки предпросмотра в боковой iframe
    async function loadSidebarPreview() {
        if (isPreviewUpdating) return; // Пропускаем если уже обновляется
        
        const canvas = document.getElementById('sidebar-preview-canvas');
        if (!canvas) return;
        
        isPreviewUpdating = true;
        const container = canvas.parentElement;
        const requestData = collectFormData();
        
        try {
            const API_URL = '';
            const response = await fetch(`${API_URL}/api/v1/documents/upd/preview`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData)
            });
            
            if (response.ok) {
                const html = await response.text();
                
                // Создаём временный контейнер для рендеринга
                const tempDiv = document.createElement('div');
                tempDiv.style.position = 'absolute';
                tempDiv.style.left = '-9999px';
                tempDiv.style.width = '1200px';
                tempDiv.innerHTML = html;
                document.body.appendChild(tempDiv);
                
                // Уменьшили задержку с 500мс до 100мс
                await new Promise(resolve => setTimeout(resolve, 100));
                
                // Рендерим в canvas с пониженным scale для ускорения
                const renderedCanvas = await html2canvas(tempDiv, {
                    scale: 3, // Было 4, стало 3 для ускорения
                    useCORS: true,
                    logging: false,
                    backgroundColor: '#ffffff'
                });
                
                // Удаляем временный контейнер
                document.body.removeChild(tempDiv);
                
                // Устанавливаем canvas в полное разрешение (без даунскейла)
                canvas.width = renderedCanvas.width;
                canvas.height = renderedCanvas.height;
                
                // Копируем изображение в полном разрешении
                const ctx = canvas.getContext('2d');
                ctx.drawImage(renderedCanvas, 0, 0);
                
                // Через CSS масштабируем только отображение
                canvas.style.width = '100%';
                canvas.style.height = 'auto';
                canvas.style.display = 'block';
            }
        } catch (error) {
            console.log('Ошибка загрузки предпросмотра:', error);
        } finally {
            isPreviewUpdating = false;
        }
    }
    
    // Кнопка обновления предпросмотра
    $('#refresh-preview').on('click', function() {
        loadSidebarPreview();
    });
    
    // ===== Clear Highlights =====
    $('#clear-highlights-btn').on('click', function() {
        clearPreviewHighlights();
        $(this).removeClass('d-flex').addClass('d-none');
    });
    
    // ===== AI Analysis =====
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
        
        // Prepare request - используем правильную структуру из collectFormData
        const analysisData = {
            upd_status: String(formData.status || '1'),
            upd_number: formData.document_number || '',
            upd_date: formData.document_date || '',
            correction_number: formData.correction_number,
            correction_date: formData.correction_date,
            seller_name: formData.seller?.name || '',
            seller_inn: formData.seller?.inn || '',
            seller_kpp: formData.seller?.kpp || '',
            seller_address: formData.seller?.address || '',
            buyer_name: formData.buyer?.name || '',
            buyer_inn: formData.buyer?.inn || '',
            buyer_kpp: formData.buyer?.kpp || '',
            buyer_address: formData.buyer?.address || '',
            shipper_name: formData.consignor || '',
            consignee_name: formData.consignee || '',
            items: formData.items || [],
            total_amount: formData.total_amount_with_vat || 0,
            total_vat: formData.total_vat_amount || 0
        };
        
        console.log('AI Analysis: sending request...', analysisData);
        
        try {
            const response = await fetch('/api/v1/ai/analyze-upd', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify(analysisData)
            });
            
            console.log('AI Analysis: response status', response.status);
            
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Ошибка анализа');
            }
            
            const result = await response.json();
            console.log('AI Analysis: result', result);
            renderAnalysisResult(result);
            
            // Apply highlights to preview iframe
            applyHighlightsToPreview(result);
            
            // Show clear highlights button
            $('#clear-highlights-btn').removeClass('d-none').addClass('d-flex');
            
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
    
    // Загрузка предпросмотра при загрузке страницы (с небольшой задержкой)
    setTimeout(loadSidebarPreview, 500);
    
    // ========== Highlight Functions for Preview ==========
    
    function applyHighlightsToPreview(analysisResult) {
        const iframe = document.getElementById('sidebar-preview-iframe');
        if (!iframe || !iframe.contentDocument) {
            console.log('Preview iframe not ready for highlighting');
            return;
        }
        
        const doc = iframe.contentDocument;
        
        // Inject highlight styles into iframe
        const styleId = 'ai-highlight-styles';
        if (!doc.getElementById(styleId)) {
            const style = doc.createElement('style');
            style.id = styleId;
            style.textContent = `
                .ai-highlight-error {
                    background: rgba(220, 38, 38, 0.3) !important;
                    outline: 2px solid #dc2626 !important;
                    outline-offset: 1px;
                    animation: pulse-error 2s infinite;
                }
                .ai-highlight-warning {
                    background: rgba(245, 158, 11, 0.3) !important;
                    outline: 2px solid #f59e0b !important;
                    outline-offset: 1px;
                    animation: pulse-warning 2s infinite;
                }
                @keyframes pulse-error {
                    0%, 100% { background: rgba(220, 38, 38, 0.3); }
                    50% { background: rgba(220, 38, 38, 0.5); }
                }
                @keyframes pulse-warning {
                    0%, 100% { background: rgba(245, 158, 11, 0.3); }
                    50% { background: rgba(245, 158, 11, 0.5); }
                }
            `;
            doc.head.appendChild(style);
        }
        
        // Clear previous highlights
        doc.querySelectorAll('.ai-highlight-error, .ai-highlight-warning').forEach(el => {
            el.classList.remove('ai-highlight-error', 'ai-highlight-warning');
        });
        
        const cells = doc.querySelectorAll('td, th');
        
        // Field mapping - keywords that might appear in issues
        const fieldMappings = {
            'инн': ['инн'],
            'кпп': ['кпп'],
            'номер': ['номер', '№'],
            'дата': ['дата'],
            'название': ['название', 'наименование'],
            'наименование': ['наименование', 'название'],
            'адрес': ['адрес'],
            'бик': ['бик'],
            'счет': ['счет', 'счёт'],
            'количество': ['количество', 'кол-во', 'кол.'],
            'цена': ['цена'],
            'сумма': ['сумма', 'итого'],
            'ндс': ['ндс', 'налог'],
            'грузоотправитель': ['грузоотправитель'],
            'грузополучатель': ['грузополучатель'],
            'продавец': ['продавец'],
            'покупатель': ['покупатель'],
            'огрн': ['огрн'],
            'окпо': ['окпо'],
            'договор': ['договор'],
            'платеж': ['платеж', 'платёж']
        };
        
        // Process errors
        if (analysisResult.errors && analysisResult.errors.length > 0) {
            analysisResult.errors.forEach(error => {
                const errorText = (typeof error === 'string' ? error : (error.message || '')).toLowerCase();
                const fieldName = (typeof error === 'object' ? error.field : '').toLowerCase();
                highlightMatchingCells(cells, errorText, fieldName, fieldMappings, 'ai-highlight-error');
            });
        }
        
        // Process warnings
        if (analysisResult.warnings && analysisResult.warnings.length > 0) {
            analysisResult.warnings.forEach(warning => {
                const warningText = (typeof warning === 'string' ? warning : (warning.message || '')).toLowerCase();
                const fieldName = (typeof warning === 'object' ? warning.field : '').toLowerCase();
                highlightMatchingCells(cells, warningText, fieldName, fieldMappings, 'ai-highlight-warning');
            });
        }
    }
    
    function highlightMatchingCells(cells, issueText, fieldName, fieldMappings, highlightClass) {
        // First try to highlight by field name
        if (fieldName) {
            const fieldLower = fieldName.toLowerCase();
            cells.forEach(cell => {
                const cellText = cell.innerText.toLowerCase();
                if (cellText.includes(fieldLower)) {
                    if (highlightClass === 'ai-highlight-warning' && cell.classList.contains('ai-highlight-error')) {
                        return;
                    }
                    cell.classList.add(highlightClass);
                }
            });
        }
        
        // Then try to match by keywords in issue text
        for (const [keyword, patterns] of Object.entries(fieldMappings)) {
            if (issueText.includes(keyword)) {
                cells.forEach(cell => {
                    const cellText = cell.innerText.toLowerCase();
                    if (patterns.some(p => cellText.includes(p))) {
                        if (highlightClass === 'ai-highlight-warning' && cell.classList.contains('ai-highlight-error')) {
                            return;
                        }
                        cell.classList.add(highlightClass);
                    }
                });
            }
        }
        
        // Highlight empty/suspicious values
        if (issueText.includes('не заполнен') || issueText.includes('пуст') || issueText.includes('отсутствует')) {
            cells.forEach(cell => {
                const cellText = cell.innerText.trim();
                if (cellText === '' || cellText === '-' || cellText === '—') {
                    const parentRow = cell.parentElement;
                    if (parentRow) {
                        const rowText = parentRow.innerText.toLowerCase();
                        for (const keyword of Object.keys(fieldMappings)) {
                            if (issueText.includes(keyword) && rowText.includes(keyword)) {
                                if (highlightClass === 'ai-highlight-warning' && cell.classList.contains('ai-highlight-error')) {
                                    return;
                                }
                                cell.classList.add(highlightClass);
                                break;
                            }
                        }
                    }
                }
            });
        }
    }
    
    function clearPreviewHighlights() {
        const iframe = document.getElementById('sidebar-preview-iframe');
        if (!iframe || !iframe.contentDocument) return;
        
        iframe.contentDocument.querySelectorAll('.ai-highlight-error, .ai-highlight-warning').forEach(el => {
            el.classList.remove('ai-highlight-error', 'ai-highlight-warning');
        });
    }
    
    // ============== GUEST REGISTRATION HANDLER ==============
    
    $('#guest-registration-form').on('submit', async function(e) {
        e.preventDefault();
        
        const submitBtn = $('#guest-reg-submit-btn');
        const alertBox = $('#guest-reg-alert');
        const originalBtnText = submitBtn.html();
        
        // Валидация
        const email = $('#guest-email').val().trim();
        const password = $('#guest-password').val();
        const name = $('#guest-name').val().trim();
        const termsAccepted = $('#guest-terms').is(':checked');
        
        if (!email || !password) {
            alertBox.removeClass('d-none').text('Заполните email и пароль');
            return;
        }
        
        if (password.length < 6) {
            alertBox.removeClass('d-none').text('Пароль должен содержать минимум 6 символов');
            return;
        }
        
        if (!termsAccepted) {
            alertBox.removeClass('d-none').text('Необходимо принять условия использования');
            return;
        }
        
        // Блокируем кнопку
        submitBtn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm me-8"></span>Регистрация...');
        alertBox.addClass('d-none');
        
        try {
            const response = await fetch(`${API_URL}/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    email: email,
                    password: password,
                    name: name || null
                })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || 'Ошибка регистрации');
            }
            
            // Успешная регистрация - сохраняем токен
            localStorage.setItem('documatica_token', data.access_token);
            localStorage.setItem('documatica_user', JSON.stringify(data.user));
            
            // Устанавливаем cookie для httponly
            document.cookie = `access_token=${data.access_token}; path=/; max-age=${24*60*60}; SameSite=Lax`;
            
            // Закрываем модалку
            $('#guestRegistrationModal').modal('hide');
            
            // Показываем уведомление
            alertBox.removeClass('alert-danger').addClass('alert-success')
                .removeClass('d-none').text('Регистрация успешна! Сохраняем документ...');
            
            // Привязываем черновик к новому аккаунту и конвертируем в документ
            const draftToken = localStorage.getItem('documatica_draft_token');
            if (draftToken) {
                try {
                    const claimResponse = await fetch('/api/v1/drafts/claim', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${data.access_token}`
                        },
                        body: JSON.stringify({ draft_token: draftToken })
                    });
                    
                    if (claimResponse.ok) {
                        const claimData = await claimResponse.json();
                        console.log('[DRAFT] Claimed and converted:', claimData.document_id);
                        // Очищаем токен черновика
                        localStorage.removeItem('documatica_draft_token');
                        localStorage.removeItem('pending_upd_data');
                        localStorage.removeItem('documatica_pending_document');
                        
                        // Редиректим в дашборд где виден документ
                        alertBox.text('Документ сохранён! Переход в личный кабинет...');
                        setTimeout(() => {
                            window.location.href = '/dashboard/';
                        }, 1000);
                        return;
                    }
                } catch (claimError) {
                    console.error('[DRAFT] Claim error:', claimError);
                }
            }
            
            // Fallback - старое поведение если нет черновика
            const pendingData = localStorage.getItem('pending_upd_data');
            if (pendingData) {
                const requestData = JSON.parse(pendingData);
                localStorage.removeItem('pending_upd_data');
                await generateAndDownloadPDF(requestData);
            }
            
            // Перезагружаем страницу
            setTimeout(() => {
                window.location.href = '/dashboard/';
            }, 1000);
            
        } catch (error) {
            console.error('Registration error:', error);
            alertBox.removeClass('d-none').text(error.message || 'Ошибка при регистрации. Попробуйте снова.');
            submitBtn.prop('disabled', false).html(originalBtnText);
        }
    });
    
    // ============== END GUEST REGISTRATION HANDLER ==============
    
    // ============== AUTO-FIT PREVIEW ==============
    function fitPreview() {
        const $iframe = $('#sidebar-preview-iframe');
        const $container = $iframe.parent();
        
        if ($iframe.length === 0) return;
        
        const containerWidth = $container.width();
        const containerHeight = $container.height();
        
        // Размеры УПД (альбомная)
        const docWidth = 1500;
        const docHeight = 1000;
        
        // Вычисляем масштаб чтобы влезло всё
        const scaleW = containerWidth / docWidth;
        const scaleH = containerHeight / docHeight;
        const scale = Math.min(scaleW, scaleH) * 0.95; // 0.95 для отступа
        
        // Устанавливаем оригинальные размеры и масштабируем через transform
        $iframe.css({
            'width': docWidth + 'px',
            'height': docHeight + 'px',
            'transform': `scale(${scale})`,
            'transform-origin': 'center center'
        });
    }
    
    // Применяем при загрузке и изменении размера
    setTimeout(fitPreview, 500);
    $(window).on('resize', fitPreview);
    // ============== END AUTO-FIT PREVIEW ==============
    
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
    
    // ============== XLS EXPORT ==============
    $('#export-xls-btn').on('click', async function() {
        if (!window.savedDocumentId) {
            toastError('Сначала создайте документ (нажмите "Скачать PDF")');
            return;
        }
        
        const btn = $(this);
        const originalText = btn.html();
        btn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm me-8"></span>Генерация XLS...');
        
        try {
            const token = localStorage.getItem('documatica_token') || getCookie('access_token');
            const response = await fetch(`/api/v1/documents/saved/${window.savedDocumentId}/export-excel?format=xls`, {
                method: 'GET',
                headers: {
                    'Authorization': token ? `Bearer ${token}` : ''
                },
                credentials: 'include'
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `УПД_${window.savedDocumentId.substring(0, 8)}.xls`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                toastSuccess('XLS файл успешно скачан!');
            } else {
                const err = await response.json();
                toastError(err.detail || 'Ошибка экспорта в XLS');
            }
        } catch (error) {
            toastError('Ошибка: ' + error.message);
        } finally {
            btn.prop('disabled', false).html(originalText);
        }
    });
    // ============== END XLS EXPORT ==============
    
    // ============== DEVELOPER MODE ==============
    // Маппинг frontend селекторов на backend field names
    const FIELD_MAPPING = {
        '#upd-number': 'document_number',
        '#upd-date': 'document_date',
        '#correction-number': 'correction_number',
        '#correction-date': 'correction_date',
        'input[name="upd-status"]': 'status',
        '#seller-name': 'seller.name',
        '#seller-inn': 'seller.inn',
        '#seller-kpp': 'seller.kpp',
        '#seller-address': 'seller.address',
        '#buyer-name': 'buyer.name',
        '#buyer-inn': 'buyer.inn',
        '#buyer-kpp': 'buyer.kpp',
        '#buyer-address': 'buyer.address',
        '#consignor-address': 'consignor',
        '#consignee-address': 'consignee',
        '#currency-code': 'currency_code',
        '#currency-name': 'currency_name',
        '#gov-contract-id': 'gov_contract_id',
        '#payment-document': 'payment_document',
        '#shipping-document': 'shipping_document',
        '#transfer-basis': 'contract_info',
        '#transport-info': 'transport_info',
        '#shipping-date': 'shipping_date',
        '#receiving-date': 'receiving_date',
        '#other-shipping-info': 'other_shipping_info',
        '#other-receiving-info': 'other_receiving_info',
        '#released-by': 'seller_signer.full_name',
        '#released-position': 'seller_signer.position',
        '#responsible-position': 'seller_responsible.position',
        '#responsible-name': 'seller_responsible.full_name',
        '#economic-entity': 'economic_entity',
        '#received-by': 'buyer_signer.full_name',
        '#received-position': 'buyer_signer.position',
        '#buyer-responsible-position': 'buyer_responsible.position',
        '#buyer-responsible-name': 'buyer_responsible.full_name',
        '#buyer-economic-entity': 'buyer_economic_entity',
        // Default values for items (not saved to backend directly)
        '#default-vat': 'default_vat_rate',
        '#default-vat-type': 'default_vat_type',
        '#default-country': 'default_country',
        '#default-country-code': 'default_country_code'
    };

    // Функция переключения Developer Mode
    function toggleDevMode() {
        const isActive = localStorage.getItem('devMode') === 'true';
        
        if (isActive) {
            // Выключить
            $('.dev-field-id').remove();
            localStorage.setItem('devMode', 'false');
            console.log('🔧 Developer Mode: OFF');
        } else {
            // Включить
            let foundCount = 0;
            let addedCount = 0;
            
            Object.keys(FIELD_MAPPING).forEach(selector => {
                const fieldId = FIELD_MAPPING[selector];
                const $field = $(selector);
                
                if ($field.length > 0) {
                    foundCount++;
                    
                    // Создаём badge с ID
                    const $badge = $(`<span class="dev-field-id" style="display: inline-block; margin-left: 8px; padding: 2px 8px; background: #e2e8f0; color: #475569; font-size: 11px; font-family: 'Courier New', monospace; border-radius: 4px; user-select: all; vertical-align: middle;">${fieldId}</span>`);
                    
                    // Проверяем, не добавлен ли уже
                    if ($field.next('.dev-field-id').length === 0) {
                        $field.after($badge);
                        addedCount++;
                    }
                }
            });
            
            localStorage.setItem('devMode', 'true');
            console.log('🔧 Developer Mode: ON');
            console.log(`📋 Fields found: ${foundCount}, Badges added: ${addedCount}`);
        }
    }

    // Hotkey: Ctrl+Shift+D
    $(document).on('keydown', function(e) {
        if (e.ctrlKey && e.shiftKey && e.key === 'D') {
            e.preventDefault();
            toggleDevMode();
        }
    });

    // Автовключение если был активен
    if (localStorage.getItem('devMode') === 'true') {
        // Увеличенная задержка для полной загрузки DOM
        setTimeout(function() {
            console.log('🔧 Auto-enabling Developer Mode...');
            toggleDevMode();
        }, 1500);
    }
    // ============== END DEVELOPER MODE ==============
    
});
