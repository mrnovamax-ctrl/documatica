/**
 * Auth-Download Module
 * Универсальный модуль для скачивания защищённых файлов (бланков/образцов)
 * с проверкой авторизации и показом модалки регистрации
 */

class AuthDownload {
  constructor(config) {
    this.config = {
      apiType: config.apiType || 'blanks',  // 'blanks' or 'samples'
      documentType: config.documentType || '',  // 'upd-blank-excel', 'schet-obrazec', etc.
      downloadFilename: config.downloadFilename || 'document',
      redirectUrl: config.redirectUrl || window.location.pathname,
      buttonIdleText: config.buttonIdleText || 'Скачать бесплатно',
      buttonLoadingText: config.buttonLoadingText || 'Скачивание...',
      buttonSuccessText: config.buttonSuccessText || '✓ Скачано',
      buttonErrorText: config.buttonErrorText || 'Ошибка',
      yandexMetrikaId: config.yandexMetrikaId || 76440544,
      ...config
    };
  }

  /**
   * Проверяет авторизацию и инициирует скачивание или показывает модалку
   */
  checkAuthAndDownload(button) {
    fetch('/api/v1/auth/check', { method: 'GET', credentials: 'include' })
      .then(r => r.json())
      .then(data => {
        if (data.authenticated) {
          this.download(button);
        } else {
          this.showAuthModal();
        }
      })
      .catch(() => this.showAuthModal());
  }

  /**
   * Показывает модалку авторизации и настраивает редиректы
   */
  showAuthModal() {
    const redirectUrl = this.config.redirectUrl;
    
    // Настраиваем ссылки в модалке
    const yandexBtn = document.getElementById('modal-yandex-btn');
    const registerBtn = document.getElementById('modal-register-btn');
    const loginBtn = document.getElementById('modal-login-btn');

    if (yandexBtn) {
      yandexBtn.href = `/auth/yandex/login?redirect_to=${encodeURIComponent(redirectUrl)}`;
    }
    if (registerBtn) {
      registerBtn.href = `/register?redirect=${encodeURIComponent(redirectUrl)}`;
    }
    if (loginBtn) {
      loginBtn.href = `/login?redirect=${encodeURIComponent(redirectUrl)}`;
    }

    // Проверяем, что Bootstrap доступен
    if (typeof bootstrap === 'undefined' || !bootstrap.Modal) {
      // Фоллбэк: редирект на регистрацию
      window.location.href = `/register?redirect=${encodeURIComponent(redirectUrl)}`;
      return;
    }

    // Показываем модалку
    const modalElement = document.getElementById('authRequiredModal');
    if (modalElement) {
      const modal = new bootstrap.Modal(modalElement);
      modal.show();
    }

    // Метрика: попытка скачивания
    this.sendMetrika('sample_download_attempt', { sample_type: this.config.documentType });
  }

  /**
   * Скачивает файл через API
   */
  download(button) {
    if (!this.config.documentType) {
      console.error('[AuthDownload] documentType не указан');
      return;
    }

    // Обновляем состояние кнопки
    if (button) {
      button.disabled = true;
      button.textContent = this.config.buttonLoadingText;
    }

    const apiUrl = `/api/v1/documents/${this.config.apiType}/${this.config.documentType}`;

    fetch(apiUrl, { method: 'GET', credentials: 'include' })
      .then(resp => {
        if (!resp.ok) throw new Error('Download failed');
        return resp.blob();
      })
      .then(blob => {
        // Создаём временную ссылку для скачивания
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = this.config.downloadFilename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();

        // Метрика: успешное скачивание
        this.sendMetrika('sample_downloaded', { sample_type: this.config.documentType });

        // Обновляем кнопку
        if (button) {
          button.textContent = this.config.buttonSuccessText;
          setTimeout(() => {
            button.textContent = this.config.buttonIdleText;
            button.disabled = false;
          }, 2000);
        }
      })
      .catch(error => {
        console.error('[AuthDownload] Ошибка скачивания:', error);

        // Обновляем кнопку
        if (button) {
          button.textContent = this.config.buttonErrorText;
          button.disabled = false;
          setTimeout(() => {
            button.textContent = this.config.buttonIdleText;
          }, 2500);
        }
      });
  }

  /**
   * Отправляет цель в Яндекс.Метрику
   */
  sendMetrika(goal, params = {}) {
    if (typeof ym !== 'undefined' && this.config.yandexMetrikaId) {
      ym(this.config.yandexMetrikaId, 'reachGoal', goal, params);
    }
  }

  /**
   * Проверяет параметр ?download= в URL и автоматически скачивает файл
   * (используется после редиректа с регистрации/логина)
   */
  autoDownloadIfRequested() {
    const urlParams = new URLSearchParams(window.location.search);
    const downloadParam = urlParams.get('download');

    if (downloadParam && downloadParam === this.config.documentType) {
      // Ждём, пока DOM полностью загрузится
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
          this.download(null);
        });
      } else {
        this.download(null);
      }
    }
  }
}

// Экспортируем для использования в модулях
if (typeof module !== 'undefined' && module.exports) {
  module.exports = AuthDownload;
}
