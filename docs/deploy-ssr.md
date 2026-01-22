# Деплой SSR версии Documatica

## Что изменилось

Сайт переведён с статических HTML на **FastAPI + Jinja2 SSR**:
- Все страницы теперь рендерятся на сервере
- Новая иерархическая структура URL
- SEO-оптимизированный контент через YAML-файлы
- Редиректы со старых URL на новые

## Файлы для деплоя

```
docker-compose.ssr.yml    # Новый docker-compose с nginx проксированием
nginx/nginx-ssr.conf      # Nginx конфиг с редиректами и проксированием
```

## Шаги деплоя

### 1. Бэкап

```bash
# Сохраняем текущую конфигурацию
cp docker-compose.yml docker-compose.old.yml
cp nginx/nginx.conf nginx/nginx.old.conf
```

### 2. Подготовка статики

```bash
# Убедиться что статика скопирована
cp -r documatica/assets/* backend/static/

# Создать папку для бланков
mkdir -p backend/static/blanks
# Добавить файлы бланков (upd-blank-2026.xlsx, upd-blank-2026.docx)
```

### 3. Деплой

```bash
# Остановить текущие контейнеры
docker-compose down

# Запустить новую версию
docker-compose -f docker-compose.ssr.yml up -d --build

# Проверить логи
docker-compose -f docker-compose.ssr.yml logs -f
```

### 4. Проверка

После деплоя проверить:

1. **Главная страница**: https://new.oplatanalogov.ru/
2. **УПД хаб**: https://new.oplatanalogov.ru/upd/
3. **УПД для ООО**: https://new.oplatanalogov.ru/upd/ooo/
4. **Редирект**: https://new.oplatanalogov.ru/upd-s-nds → /upd/s-nds/
5. **Dashboard**: https://new.oplatanalogov.ru/dashboard/
6. **API**: https://new.oplatanalogov.ru/api/v1/organizations/

### 5. Откат (если что-то пошло не так)

```bash
docker-compose -f docker-compose.ssr.yml down
docker-compose -f docker-compose.old.yml up -d
```

## Редиректы

| Старый URL | Новый URL |
|------------|-----------|
| /upd-s-nds | /upd/s-nds/ |
| /upd-bez-nds | /upd/bez-nds/ |
| /upd-dlya-ooo | /upd/ooo/ |
| /upd-dlya-ip | /upd/ip/ |
| /upd-samozanyatye | /upd/samozanyatye/ |
| /upd-usn | /upd/usn/ |
| /upd-xml-edo | /upd/xml-edo/ |
| /upd-create | /dashboard/upd/create/ |
| /dashboard | /dashboard/ |
| /organizations | /dashboard/organizations/ |
| /contractors | /dashboard/contractors/ |
| /products | /dashboard/products/ |
| /documents | /dashboard/documents/ |

## Структура новых URL

```
/                           # Главная
/upd/                       # УПД хаб
/upd/ooo/                   # УПД для ООО
/upd/ip/                    # УПД для ИП
/upd/s-nds/                 # УПД с НДС
/upd/bez-nds/               # УПД без НДС
/upd/samozanyatye/          # УПД для самозанятых
/upd/usn/                   # УПД на УСН
/upd/2026/                  # УПД форма 2026
/upd/obrazec-zapolneniya/   # Образец заполнения
/upd/xml-edo/               # XML для ЭДО
/upd/blank-excel/           # Скачать Excel
/upd/blank-word/            # Скачать Word

/login/                     # Вход
/register/                  # Регистрация

/dashboard/                 # Личный кабинет
/dashboard/upd/create/      # Создать УПД
/dashboard/documents/       # Мои документы
/dashboard/organizations/   # Организации
/dashboard/contractors/     # Контрагенты
/dashboard/products/        # Товары/услуги
```
