/**
 * UPD Constructor - Utility Functions
 * Вспомогательные функции общего назначения
 */

import { CURRENCY_FORMAT, STORAGE_KEYS } from './config.js';

/**
 * Форматирование суммы в рубли
 */
export function formatCurrency(amount) {
  return parseFloat(amount || 0).toLocaleString('ru-RU', {
    style: 'decimal',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
}

/**
 * Конвертация даты из формата DD.MM.YYYY в ISO
 */
export function convertDateToISO(dateStr) {
  if (!dateStr) return null;
  const parts = dateStr.split('.');
  if (parts.length === 3) {
    return `${parts[2]}-${parts[1]}-${parts[0]}`;
  }
  return dateStr;
}

/**
 * Конвертация даты из ISO в формат DD.MM.YYYY
 */
export function convertDateFromISO(isoStr) {
  if (!isoStr) return '';
  const parts = isoStr.split('-');
  if (parts.length === 3) {
    return `${parts[2]}.${parts[1]}.${parts[0]}`;
  }
  return isoStr;
}

/**
 * Получение cookie по имени
 */
export function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) {
    return parts.pop().split(';').shift();
  }
  return null;
}

/**
 * Проверка авторизации пользователя
 */
export function isUserAuthenticated() {
  const token = localStorage.getItem(STORAGE_KEYS.TOKEN) || getCookie('access_token');
  return !!token;
}

/**
 * Показать уведомление (toast)
 */
export function showNotification(message, type = 'success') {
  const bgClass = type === 'success' ? 'bg-success-100 text-success-main' : 'bg-danger-100 text-danger-main';
  const icon = type === 'success' ? 'mdi:check-circle' : 'mdi:alert-circle';
  
  const toast = $(`
    <div class="position-fixed top-0 end-0 m-24 p-16 ${bgClass} shadow-lg" style="z-index: 9999; border-radius: 1rem;">
      <div class="d-flex align-items-center gap-8">
        <iconify-icon icon="${icon}" class="text-xl"></iconify-icon>
        <span>${message}</span>
      </div>
    </div>
  `);
  
  $('body').append(toast);
  setTimeout(() => {
    toast.fadeOut(300, function() {
      $(this).remove();
    });
  }, 3000);
}

/**
 * Установить сегодняшнюю дату в поле
 */
export function setTodayDate(inputSelector) {
  const today = new Date();
  const formattedDate = today.toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  });
  $(inputSelector).val(formattedDate);
}
