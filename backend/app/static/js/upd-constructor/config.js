/**
 * UPD Constructor - Configuration
 * Константы и настройки приложения
 */

// API endpoints
export const API_URL = '/api/v1';

// Налоговые ставки
export const VAT_RATES = {
  WITH_VAT: 20,
  WITHOUT_VAT: 0
};

// Настройки форматирования
export const CURRENCY_FORMAT = {
  locale: 'ru-RU',
  currency: 'RUB',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2
};

// Настройки автосохранения
export const AUTOSAVE_DELAY = 2000; // ms

// LocalStorage ключи
export const STORAGE_KEYS = {
  TOKEN: 'documatica_token',
  USER: 'documatica_user',
  ORGANIZATIONS: 'organizations',
  CONTRACTORS: 'contractors',
  PRODUCTS: 'products',
  PENDING_UPD: 'pending_upd_data'
};

// Лимиты
export const LIMITS = {
  MAX_PRODUCTS: 50,
  MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
  INN_LENGTH_IP: 12,
  INN_LENGTH_OOO: 10
};
