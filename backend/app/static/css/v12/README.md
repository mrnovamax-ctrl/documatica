# Terminal v12 Design System

- **core.css** — полный файл стилей из скилла `.cursor/skills/terminal-v12/src/styles/core.css`.  
  При обновлении дизайн-системы в скилле достаточно скопировать его сюда заново:
  ```bash
  cp .cursor/skills/terminal-v12/src/styles/core.css backend/app/static/css/v12/core.css
  ```
- Подключение: `base.html` подключает `core.css` до `documatica.css` для всего сайта (кроме страниц, переопределяющих блок стилей). Дашборд тоже получает core; общий хедер — на публичных страницах.
