# Copilot Skills Pack

Набор скиллов для VS Code Copilot Agent. Автоматически улучшают работу AI-ассистента в проекте.

## Установленные скиллы

| Skill | Назначение | Триггеры |
|-------|------------|----------|
| **v12-style** | Documatica Design System v12.0 | `create UI`, `design component`, `style form` |
| **git-commit** | Conventional Commits | `commit changes`, `/commit` |
| **refactor** | Паттерны рефакторинга | `refactor this`, `clean up code` |
| **prd** | Product Requirements Documents | `write PRD`, `document requirements` |
| **webapp-testing** | Playwright UI тесты | `test frontend`, `capture screenshot` |
| **web-design-reviewer** | Ревью дизайна | `review design`, `check UI`, `fix layout` |

---

## Быстрый старт для нового проекта

### Вариант 1: Клонировать из GitHub

```bash
# Создать директорию
mkdir -p .github/skills

# Клонировать v12-style (наш дизайн)
git clone --depth 1 https://github.com/mrnovamax-ctrl/documatica-v12-skill.git /tmp/v12-skill
cp -r /tmp/v12-skill/.github/skills/v12-style .github/skills/

# Клонировать awesome-copilot (остальные скиллы)
git clone --depth 1 https://github.com/github/awesome-copilot.git /tmp/awesome-copilot
cp -r /tmp/awesome-copilot/skills/git-commit .github/skills/
cp -r /tmp/awesome-copilot/skills/refactor .github/skills/
cp -r /tmp/awesome-copilot/skills/prd .github/skills/
cp -r /tmp/awesome-copilot/skills/webapp-testing .github/skills/
cp -r /tmp/awesome-copilot/skills/web-design-reviewer .github/skills/

# Очистка
rm -rf /tmp/v12-skill /tmp/awesome-copilot
```

### Вариант 2: Скрипт автоустановки

Создай файл `scripts/install-copilot-skills.sh`:

```bash
#!/bin/bash
set -e

SKILLS_DIR=".github/skills"
mkdir -p "$SKILLS_DIR"

echo "Installing Copilot Skills Pack..."

# v12-style (Documatica Design System)
if [ ! -d "$SKILLS_DIR/v12-style" ]; then
  echo "  -> v12-style"
  git clone --depth 1 --quiet https://github.com/mrnovamax-ctrl/documatica-v12-skill.git /tmp/v12-skill
  cp -r /tmp/v12-skill/.github/skills/v12-style "$SKILLS_DIR/"
  rm -rf /tmp/v12-skill
fi

# awesome-copilot skills
AWESOME_SKILLS="git-commit refactor prd webapp-testing web-design-reviewer"
git clone --depth 1 --quiet https://github.com/github/awesome-copilot.git /tmp/awesome-copilot

for skill in $AWESOME_SKILLS; do
  if [ ! -d "$SKILLS_DIR/$skill" ]; then
    echo "  -> $skill"
    cp -r "/tmp/awesome-copilot/skills/$skill" "$SKILLS_DIR/"
  fi
done

rm -rf /tmp/awesome-copilot

echo "Done! Installed skills:"
ls -1 "$SKILLS_DIR"
```

Запуск:
```bash
chmod +x scripts/install-copilot-skills.sh
./scripts/install-copilot-skills.sh
```

### Вариант 3: Копировать из существующего проекта

```bash
# Из Documatica в новый проект
cp -r /path/to/documatica/.github/skills /path/to/new-project/.github/
```

---

## Структура скилла

```
.github/skills/
├── skill-name/
│   ├── SKILL.md          # Основной файл (обязательно)
│   └── references/       # Дополнительные файлы (опционально)
│       ├── example.html
│       └── example.css
```

### Формат SKILL.md

```yaml
---
name: skill-name
description: 'Описание когда использовать. Триггеры: слова активации.'
license: MIT
---

# Название

## When to Use
...

## Instructions
...
```

---

## Создание своего скилла

1. Создай директорию: `.github/skills/my-skill/`
2. Создай `SKILL.md` с frontmatter
3. Добавь references если нужны примеры
4. Перезапусти VS Code

---

## Полезные ссылки

- [awesome-copilot](https://github.com/github/awesome-copilot) - официальная коллекция
- [documatica-v12-skill](https://github.com/mrnovamax-ctrl/documatica-v12-skill) - наш дизайн
- [Copilot Skills docs](https://docs.github.com/en/copilot/using-github-copilot/using-copilot-customizations-in-your-organization/about-customizing-copilot-with-custom-instructions)
