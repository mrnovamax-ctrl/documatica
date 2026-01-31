/**
 * UPD Wizard v12.0 - Быстрое заполнение
 * Пошаговый визард для упрощенного создания УПД
 */

(function() {
    'use strict';
    
    const API_URL = window.UPD_CONFIG?.apiUrl || '/api/v1';
    
    // Wizard State
    const wizardData = {
        currentStep: 1,
        totalSteps: 7,
        seller: null,
        buyer: null,
        products: [],
        additionalInfo: {},
        sellerSignatory: {},
        buyerSignatory: {}
    };
    
    // Prevent page scroll when modal opens
    let savedScrollPosition = 0;
    
    $('#wizardModal').on('show.bs.modal', function(e) {
        // Save current scroll position
        savedScrollPosition = $(window).scrollTop();
    });
    
    $('#wizardModal').on('shown.bs.modal', function(e) {
        // Initialize wizard
        initWizard();
        
        // Prevent autofocus from scrolling
        $(this).find('input:first').blur();
        
        // Restore page scroll position
        $(window).scrollTop(savedScrollPosition);
        
        // Ensure modal content is at top
        $('.wizard-step-container').scrollTop(0);
        $(this).find('.modal-body').scrollTop(0);
        
        // Pre-fill document parameters
        const today = new Date();
        const dateStr = `${String(today.getDate()).padStart(2, '0')}.${String(today.getMonth() + 1).padStart(2, '0')}.${today.getFullYear()}`;
        $('#wizard-upd-date').val(dateStr);
        
        // Generate UPD number
        const timestamp = Date.now().toString().slice(-6);
        $('#wizard-upd-number').val(`УПД-${timestamp}`);
    });
    
    // Also prevent scroll on hidden
    $('#wizardModal').on('hidden.bs.modal', function() {
        $(window).scrollTop(savedScrollPosition);
    });
    
    // Initialize wizard
    function initWizard() {
        wizardData.currentStep = 1;
        updateStepperUI();
        updateProgressBar();
        showStep(1);
        updateNavigationButtons();
    }
    
    // Navigation
    $('#wizard-btn-next').on('click', function() {
        if (validateCurrentStep()) {
            if (wizardData.currentStep < wizardData.totalSteps) {
                wizardData.currentStep++;
                goToStep(wizardData.currentStep);
            }
        }
    });
    
    $('#wizard-btn-back').on('click', function() {
        if (wizardData.currentStep > 1) {
            wizardData.currentStep--;
            goToStep(wizardData.currentStep);
        }
    });
    
    $('#wizard-btn-skip').on('click', function() {
        if (wizardData.currentStep < wizardData.totalSteps) {
            wizardData.currentStep++;
            goToStep(wizardData.currentStep);
        }
    });
    
    // Close wizard with confirmation
    $('#wizard-close-btn').on('click', function() {
        if (hasWizardData()) {
            if (confirm('Вы уверены? Все введённые данные будут потеряны.')) {
                resetWizard();
                $('#wizardModal').modal('hide');
            }
        } else {
            resetWizard();
            $('#wizardModal').modal('hide');
        }
    });
    
    function goToStep(step) {
        showStep(step);
        updateStepperUI();
        updateProgressBar();
        updateNavigationButtons();
        
        // Update summary on final step
        if (step === 7) {
            updateSummary();
        }
    }
    
    function showStep(step) {
        $('.wizard-step').removeClass('active');
        $(`.wizard-step[data-step="${step}"]`).addClass('active');
    }
    
    function updateStepperUI() {
        $('.wizard-step-item').each(function() {
            const stepNum = parseInt($(this).data('step'));
            $(this).removeClass('active completed');
            
            if (stepNum === wizardData.currentStep) {
                $(this).addClass('active');
            } else if (stepNum < wizardData.currentStep) {
                $(this).addClass('completed');
            }
        });
    }
    
    function updateProgressBar() {
        const progress = (wizardData.currentStep / wizardData.totalSteps) * 100;
        $('.wizard-progress-fill').css('width', progress + '%');
    }
    
    function updateNavigationButtons() {
        // Back button
        if (wizardData.currentStep === 1) {
            $('#wizard-btn-back').hide();
        } else {
            $('#wizard-btn-back').show();
        }
        
        // Skip button (show on steps 4, 5, 6)
        if ([4, 5, 6].includes(wizardData.currentStep)) {
            $('#wizard-btn-skip').show();
        } else {
            $('#wizard-btn-skip').hide();
        }
        
        // Next button
        if (wizardData.currentStep === 7) {
            $('#wizard-btn-next').hide();
        } else {
            $('#wizard-btn-next').show();
        }
    }
    
    function validateCurrentStep() {
        switch(wizardData.currentStep) {
            case 1: // Продавец
                if (!wizardData.seller) {
                    alert('Пожалуйста, найдите продавца по ИНН');
                    return false;
                }
                return true;
                
            case 2: // Покупатель
                if (!wizardData.buyer) {
                    alert('Пожалуйста, найдите покупателя по ИНН');
                    return false;
                }
                return true;
                
            case 3: // Товары
                if (wizardData.products.length === 0) {
                    alert('Добавьте хотя бы один товар или услугу');
                    return false;
                }
                // Check that at least one product has a name
                const hasValidProduct = wizardData.products.some(p => p.name && p.name.trim() !== '');
                if (!hasValidProduct) {
                    alert('Укажите наименование товара или услуги');
                    return false;
                }
                return true;
                
            default:
                return true;
        }
    }
    
    function hasWizardData() {
        return wizardData.seller !== null || 
               wizardData.buyer !== null || 
               wizardData.products.length > 0;
    }
    
    function resetWizard() {
        wizardData.currentStep = 1;
        wizardData.seller = null;
        wizardData.buyer = null;
        wizardData.products = [];
        wizardData.additionalInfo = {};
        wizardData.sellerSignatory = {};
        wizardData.buyerSignatory = {};
        
        // Reset form fields
        $('#wizard-seller-inn').val('');
        $('#wizard-seller-card').removeClass('show');
        $('#wizard-buyer-inn').val('');
        $('#wizard-buyer-card').removeClass('show');
        
        // Reset products
        $('#wizard-products-container').html(`
            <div class="wizard-product-row">
                <div>
                    <label class="form-label">Наименование <span class="text-danger">*</span></label>
                    <input type="text" class="form-control wizard-product-name" placeholder="Название товара или услуги">
                </div>
                <div>
                    <label class="form-label">Кол-во</label>
                    <input type="number" class="form-control wizard-product-qty" value="1" min="0.01" step="0.01">
                </div>
                <div>
                    <label class="form-label">Ед. изм.</label>
                    <select class="form-select wizard-product-unit">
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
                <div>
                    <label class="form-label">Цена</label>
                    <input type="number" class="form-control wizard-product-price" value="0" min="0" step="0.01">
                </div>
                <div>
                    <label class="form-label">Сумма</label>
                    <input type="text" class="form-control wizard-product-total" value="0 ₽" readonly>
                </div>
                <div>
                    <button type="button" class="btn remove-product wizard-remove-product" title="Удалить">
                        <iconify-icon icon="mdi:trash-can-outline"></iconify-icon>
                    </button>
                </div>
            </div>
        `);
        
        updateTotals();
    }
    
    // ============== STEP 1-2: DADATA INTEGRATION ==============
    
    $('#wizard-seller-search').on('click', function() {
        const inn = $('#wizard-seller-inn').val().trim();
        searchCompany(inn, 'seller');
    });
    
    $('#wizard-buyer-search').on('click', function() {
        const inn = $('#wizard-buyer-inn').val().trim();
        searchCompany(inn, 'buyer');
    });
    
    async function searchCompany(inn, type) {
        if (!inn || inn.length < 10) {
            alert('ИНН должен содержать минимум 10 символов');
            return;
        }
        
        const loadingEl = $(`#wizard-${type}-loading`);
        const searchBtn = $(`#wizard-${type}-search`);
        
        try {
            loadingEl.removeClass('d-none');
            searchBtn.prop('disabled', true);
            
            const response = await fetch(`${API_URL}/dadata/company/by-inn`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ inn: inn, branch_type: 'MAIN' })
            });
            
            if (!response.ok) {
                if (response.status === 404) {
                    alert('Компания с таким ИНН не найдена');
                    return;
                }
                throw new Error('Ошибка при поиске');
            }
            
            const company = await response.json();
            displayCompanyData(company, type);
            
            if (type === 'seller') {
                wizardData.seller = company;
            } else {
                wizardData.buyer = company;
            }
            
        } catch (error) {
            console.error('Dadata search error:', error);
            alert('Ошибка при поиске компании');
        } finally {
            loadingEl.addClass('d-none');
            searchBtn.prop('disabled', false);
        }
    }
    
    function displayCompanyData(company, type) {
        $(`#wizard-${type}-name`).text(company.name || '');
        $(`#wizard-${type}-inn-display`).text(company.inn || '');
        $(`#wizard-${type}-address`).text(company.address_full || company.address || '');
        
        if (company.kpp) {
            $(`#wizard-${type}-kpp-display`).text(company.kpp);
            $(`#wizard-${type}-kpp-container`).show();
        } else {
            $(`#wizard-${type}-kpp-container`).hide();
        }
        
        $(`#wizard-${type}-card`).addClass('show');
    }
    
    // ============== STEP 3: PRODUCTS ==============
    
    $('#wizard-add-product').on('click', function() {
        addProductRow();
    });
    
    $(document).on('click', '.wizard-remove-product', function() {
        if ($('.wizard-product-row').length > 1) {
            $(this).closest('.wizard-product-row').remove();
            calculateProducts();
        }
    });
    
    $(document).on('input', '.wizard-product-qty, .wizard-product-price', function() {
        const row = $(this).closest('.wizard-product-row');
        updateProductTotal(row);
        calculateProducts();
    });
    
    // Update totals when VAT settings change
    $(document).on('change', '#wizard-seller-vat, #wizard-seller-vat-type', function() {
        updateTotals();
    });
    
    function addProductRow() {
        const newRow = `
            <div class="wizard-product-row">
                <div>
                    <label class="form-label">Наименование <span class="text-danger">*</span></label>
                    <input type="text" class="form-control wizard-product-name" placeholder="Название товара или услуги">
                </div>
                <div>
                    <label class="form-label">Кол-во</label>
                    <input type="number" class="form-control wizard-product-qty" value="1" min="0.01" step="0.01">
                </div>
                <div>
                    <label class="form-label">Ед. изм.</label>
                    <select class="form-select wizard-product-unit">
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
                <div>
                    <label class="form-label">Цена</label>
                    <input type="number" class="form-control wizard-product-price" value="0" min="0" step="0.01">
                </div>
                <div>
                    <label class="form-label">Сумма</label>
                    <input type="text" class="form-control wizard-product-total" value="0 ₽" readonly>
                </div>
                <div>
                    <button type="button" class="btn remove-product wizard-remove-product" title="Удалить">
                        <iconify-icon icon="mdi:trash-can-outline"></iconify-icon>
                    </button>
                </div>
            </div>
        `;
        $('#wizard-products-container').append(newRow);
    }
    
    function updateProductTotal(row) {
        const qty = parseFloat(row.find('.wizard-product-qty').val()) || 0;
        const price = parseFloat(row.find('.wizard-product-price').val()) || 0;
        const total = qty * price;
        row.find('.wizard-product-total').val(total.toFixed(2) + ' ₽');
    }
    
    function calculateProducts() {
        wizardData.products = [];
        let subtotal = 0;
        
        $('.wizard-product-row').each(function() {
            const name = $(this).find('.wizard-product-name').val();
            const qty = parseFloat($(this).find('.wizard-product-qty').val()) || 0;
            const unit = $(this).find('.wizard-product-unit').val();
            const price = parseFloat($(this).find('.wizard-product-price').val()) || 0;
            const total = qty * price;
            
            wizardData.products.push({ name, qty, unit, price, total });
            subtotal += total;
        });
        
        updateTotals();
    }
    
    function updateTotals() {
        let subtotal = 0;
        wizardData.products.forEach(p => {
            subtotal += p.total || 0;
        });
        
        // Get VAT rate from seller settings
        const vatValue = $('#wizard-seller-vat').val();
        const vatType = $('#wizard-seller-vat-type').val();
        
        let vatRate = 0;
        if (vatValue && vatValue !== 'none') {
            vatRate = parseFloat(vatValue) / 100;
        }
        
        let vat = 0;
        let total = subtotal;
        
        if (vatType === 'on-top') {
            // НДС сверху
            vat = subtotal * vatRate;
            total = subtotal + vat;
        } else {
            // НДС включен в цену
            vat = subtotal * (vatRate / (1 + vatRate));
            total = subtotal;
            subtotal = subtotal - vat;
        }
        
        $('#wizard-total-without-vat').text(subtotal.toFixed(2) + ' ₽');
        $('#wizard-total-vat').text(vat.toFixed(2) + ' ₽');
        $('#wizard-total-with-vat').text(total.toFixed(2) + ' ₽');
    }
    
    // ============== STEP 4-6: COLLECT DATA ==============
    
    function collectAdditionalInfo() {
        wizardData.additionalInfo = {
            paymentDoc: $('#wizard-payment-doc').val(),
            shippingDoc: $('#wizard-shipping-doc').val()
        };
    }
    
    function collectSellerSignatory() {
        wizardData.sellerSignatory = {
            transferBasis: $('#wizard-transfer-basis').val(),
            transportInfo: $('#wizard-transport-info').val(),
            position: $('#wizard-seller-position').val(),
            fio: $('#wizard-seller-fio').val(),
            shippingDate: $('#wizard-shipping-date').val(),
            otherInfo: $('#wizard-other-shipping').val(),
            responsiblePosition: $('#wizard-seller-resp-position').val(),
            responsibleFio: $('#wizard-seller-resp-fio').val()
        };
    }
    
    function collectBuyerSignatory() {
        wizardData.buyerSignatory = {
            position: $('#wizard-buyer-position').val(),
            fio: $('#wizard-buyer-fio').val(),
            receivingDate: $('#wizard-receiving-date').val(),
            otherInfo: $('#wizard-other-receiving').val(),
            responsiblePosition: $('#wizard-buyer-resp-position').val(),
            responsibleFio: $('#wizard-buyer-resp-fio').val()
        };
    }
    
    // ============== STEP 7: SUMMARY & ACTIONS ==============
    
    function updateSummary() {
        // Collect all data before showing summary
        calculateProducts();
        collectAdditionalInfo();
        collectSellerSignatory();
        collectBuyerSignatory();
        
        // Update summary
        $('#summary-seller-name').text(wizardData.seller?.name || '—');
        $('#summary-seller-inn').text(wizardData.seller?.inn || '—');
        $('#summary-buyer-name').text(wizardData.buyer?.name || '—');
        $('#summary-buyer-inn').text(wizardData.buyer?.inn || '—');
        $('#summary-products-count').text(wizardData.products.length);
        
        let total = 0;
        wizardData.products.forEach(p => {
            total += p.total || 0;
        });
        const vat = total * 0.20;
        const totalWithVat = total + vat;
        $('#summary-total').text(totalWithVat.toFixed(2) + ' ₽');
        
        const today = new Date().toLocaleDateString('ru-RU');
        $('#summary-date').text(today);
    }
    
    $('#wizard-open-form').on('click', function() {
        fillMainForm();
        $('#wizardModal').modal('hide');
        
        // Scroll to action buttons at bottom
        setTimeout(() => {
            const actionsSection = $('#preview-btn').closest('.card');
            if (actionsSection.length) {
                $('html, body').animate({
                    scrollTop: actionsSection.offset().top - 100
                }, 800, 'swing');
            }
        }, 300);
        
        // Show success toast
        if (typeof toastSuccess === 'function') {
            toastSuccess('Данные заполнены! Проверьте форму и добавьте недостающие детали.');
        }
    });
    
    $('#wizard-download-pdf').on('click', function() {
        fillMainForm();
        
        // Wait a bit for form to be filled, then trigger submit
        setTimeout(function() {
            $('#wizardModal').modal('hide');
            $('#upd-form').submit();
        }, 500);
    });
    
    function fillMainForm() {
        // Document parameters
        const updNumber = $('#wizard-upd-number').val();
        const updDate = $('#wizard-upd-date').val();
        const currencyName = $('#wizard-currency-name').val();
        const currencyCode = $('#wizard-currency-code').val();
        
        if (updNumber) {
            $('#upd-number').val(updNumber);
        }
        if (updDate) {
            $('#upd-date').val(updDate);
        }
        if (currencyName) {
            $('#currency-name').val(currencyName);
        }
        if (currencyCode) {
            $('#currency-code').val(currencyCode);
        }
        
        // Seller
        if (wizardData.seller) {
            $('#seller-name').val(wizardData.seller.name || '');
            $('#seller-inn').val(wizardData.seller.inn || '');
            $('#seller-kpp').val(wizardData.seller.kpp || '');
            $('#seller-address').val(wizardData.seller.address_full || wizardData.seller.address || '');
            
            // НДС и страна
            const vat = $('#wizard-seller-vat').val();
            const vatType = $('#wizard-seller-vat-type').val();
            const country = $('#wizard-seller-country').val();
            const countryCode = $('#wizard-seller-country-code').val();
            
            if (vat) {
                $('#default-vat').val(vat);
            }
            if (vatType) {
                $('#default-vat-type').val(vatType);
            }
            if (country) {
                $('#default-country').val(country);
            }
            if (countryCode) {
                $('#default-country-code').val(countryCode);
            }
        }
        
        // Buyer
        if (wizardData.buyer) {
            $('#buyer-name').val(wizardData.buyer.name || '');
            $('#buyer-inn').val(wizardData.buyer.inn || '');
            $('#buyer-kpp').val(wizardData.buyer.kpp || '');
            $('#buyer-address').val(wizardData.buyer.address_full || wizardData.buyer.address || '');
        }
        
        // Products
        // Clear existing products except first
        $('.product-row').not(':first').remove();
        
        wizardData.products.forEach((product, index) => {
            let row;
            if (index === 0) {
                row = $('.product-row').first();
            } else {
                // Add new row using existing addProduct function if available
                if (typeof addProduct === 'function') {
                    addProduct();
                    row = $('.product-row').last();
                }
            }
            
            if (row) {
                row.find('.product-name').val(product.name || '');
                row.find('.product-qty').val(product.qty || 1);
                row.find('.product-unit').val(product.unit || 'шт');
                row.find('.product-price').val(product.price || 0);
                row.find('.product-total').val((product.total || 0).toFixed(2) + ' ₽');
            }
        });
        
        // Additional info
        if (wizardData.additionalInfo.paymentDoc) {
            $('#payment-document').val(wizardData.additionalInfo.paymentDoc);
        }
        if (wizardData.additionalInfo.shippingDoc) {
            $('#shipping-document').val(wizardData.additionalInfo.shippingDoc);
        }
        
        // Seller signatory
        if (wizardData.sellerSignatory.transferBasis) {
            $('#transfer-basis').val(wizardData.sellerSignatory.transferBasis);
        }
        if (wizardData.sellerSignatory.transportInfo) {
            $('#transport-info').val(wizardData.sellerSignatory.transportInfo);
        }
        if (wizardData.sellerSignatory.position) {
            $('#released-position').val(wizardData.sellerSignatory.position);
        }
        if (wizardData.sellerSignatory.fio) {
            $('#released-by').val(wizardData.sellerSignatory.fio);
        }
        if (wizardData.sellerSignatory.shippingDate) {
            $('#shipping-date').val(wizardData.sellerSignatory.shippingDate);
        }
        if (wizardData.sellerSignatory.otherInfo) {
            $('#other-shipping-info').val(wizardData.sellerSignatory.otherInfo);
        }
        if (wizardData.sellerSignatory.responsiblePosition) {
            $('#responsible-position').val(wizardData.sellerSignatory.responsiblePosition);
        }
        if (wizardData.sellerSignatory.responsibleFio) {
            $('#responsible-name').val(wizardData.sellerSignatory.responsibleFio);
        }
        
        // Buyer signatory
        if (wizardData.buyerSignatory.position) {
            $('#received-position').val(wizardData.buyerSignatory.position);
        }
        if (wizardData.buyerSignatory.fio) {
            $('#received-by').val(wizardData.buyerSignatory.fio);
        }
        if (wizardData.buyerSignatory.receivingDate) {
            $('#receiving-date').val(wizardData.buyerSignatory.receivingDate);
        }
        if (wizardData.buyerSignatory.otherInfo) {
            $('#other-receiving-info').val(wizardData.buyerSignatory.otherInfo);
        }
        if (wizardData.buyerSignatory.responsiblePosition) {
            $('#buyer-responsible-position').val(wizardData.buyerSignatory.responsiblePosition);
        }
        if (wizardData.buyerSignatory.responsibleFio) {
            $('#buyer-responsible-name').val(wizardData.buyerSignatory.responsibleFio);
        }
        
        // Trigger recalculation if available
        if (typeof recalculateAll === 'function') {
            recalculateAll();
        }
    }
    
})();
