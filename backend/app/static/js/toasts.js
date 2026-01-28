/**
 * Documatica Toast Notifications v12.0
 * Система нативных уведомлений в инженерной эстетике
 */

(function() {
    'use strict';

    // Создаем контейнер для уведомлений если его нет
    function ensureContainer() {
        let container = document.getElementById('notification-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notification-container';
            document.body.appendChild(container);
        }
        return container;
    }

    // Конфигурации типов уведомлений
    const toastConfigs = {
        success: {
            label: 'Verified',
            icon: '<svg class="toast-icon-svg" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24"><path d="M5 13l4 4L19 7"></path></svg>',
            colorClass: 'toast--success'
        },
        error: {
            label: 'Critical Fault',
            icon: '<svg class="toast-icon-svg" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24"><path d="M6 18L18 6M6 6l12 12"></path></svg>',
            colorClass: 'toast--error'
        },
        warning: {
            label: 'AI Advisory',
            icon: '<svg class="toast-icon-svg" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24"><path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>',
            colorClass: 'toast--warning'
        },
        info: {
            label: 'System Status',
            icon: '<svg class="toast-icon-svg" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24"><path d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>',
            colorClass: 'toast--info'
        }
    };

    /**
     * Создает и показывает уведомление
     * @param {string} type - Тип: 'success', 'error', 'warning', 'info'
     * @param {string} message - Текст сообщения
     * @param {object} options - Дополнительные опции
     * @param {string} options.title - Заголовок (опционально)
     * @param {number} options.duration - Время показа в мс (по умолчанию 5000)
     */
    function spawnToast(type, message, options = {}) {
        const container = ensureContainer();
        const config = toastConfigs[type] || toastConfigs.info;
        const duration = options.duration || 5000;
        const title = options.title || getDefaultTitle(type);

        const toast = document.createElement('div');
        toast.className = `toast-v12 ${config.colorClass}`;
        
        toast.innerHTML = `
            <div class="toast-icon">
                ${config.icon}
            </div>
            <div class="toast-content">
                <span class="toast-label">${config.label}</span>
                <h4 class="toast-title">${escapeHtml(title)}</h4>
                <p class="toast-text">${escapeHtml(message)}</p>
            </div>
            <button type="button" class="toast-close" aria-label="Закрыть">
                <svg fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24"><path d="M6 18L18 6M6 6l12 12"></path></svg>
            </button>
            <div class="toast-progress" style="animation-duration: ${duration}ms"></div>
        `;

        // Обработчик закрытия
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => removeToast(toast));

        container.appendChild(toast);

        // Автоматическое удаление
        setTimeout(() => removeToast(toast), duration);

        return toast;
    }

    function removeToast(toast) {
        if (!toast || toast.classList.contains('toast--removing')) return;
        
        toast.classList.add('toast--removing');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 500);
    }

    function getDefaultTitle(type) {
        const titles = {
            success: 'Операция выполнена',
            error: 'Произошла ошибка',
            warning: 'Внимание',
            info: 'Информация'
        };
        return titles[type] || 'Уведомление';
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Короткие алиасы для удобства
    function toastSuccess(message, options = {}) {
        return spawnToast('success', message, options);
    }

    function toastError(message, options = {}) {
        return spawnToast('error', message, options);
    }

    function toastWarning(message, options = {}) {
        return spawnToast('warning', message, options);
    }

    function toastInfo(message, options = {}) {
        return spawnToast('info', message, options);
    }

    // Экспорт в глобальную область
    window.spawnToast = spawnToast;
    window.toastSuccess = toastSuccess;
    window.toastError = toastError;
    window.toastWarning = toastWarning;
    window.toastInfo = toastInfo;

    // Инициализация контейнера при загрузке DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', ensureContainer);
    } else {
        ensureContainer();
    }

})();
