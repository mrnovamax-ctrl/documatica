#!/usr/bin/env python3
"""
Скрипт для импорта статей из WordPress SQL дампа в articles.json
"""

import re
import json
import uuid
from pathlib import Path
from datetime import datetime
from html import unescape

# Пути
SQL_FILE = Path("/opt/beget/documatica/u2149247_oplatanalogov.sql")
ARTICLES_FILE = Path("/opt/beget/documatica/backend/data/articles.json")

def extract_posts_from_sql(sql_file: Path) -> list:
    """Извлекает посты из SQL дампа"""
    print(f"Читаю SQL файл: {sql_file}")
    
    with open(sql_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Ищем INSERT INTO wp_posts
    # Формат: INSERT INTO `wp_posts` VALUES (id, author, date, content, title, ...)
    posts = []
    
    # Найдём структуру таблицы wp_posts
    create_match = re.search(r'CREATE TABLE `wp_posts` \((.*?)\) ENGINE', content, re.DOTALL)
    if create_match:
        print("Структура таблицы wp_posts найдена")
    
    # Ищем все INSERT INTO wp_posts
    pattern = r"INSERT INTO `wp_posts` VALUES\s*(.+?)(?=(?:INSERT INTO|CREATE TABLE|DROP TABLE|LOCK TABLES|UNLOCK TABLES|/\*!|$))"
    
    insert_matches = re.findall(pattern, content, re.DOTALL)
    print(f"Найдено {len(insert_matches)} блоков INSERT для wp_posts")
    
    for insert_block in insert_matches:
        # Парсим значения построчно
        # Каждая запись начинается с (id,...) и заканчивается ),
        # Используем более простой подход - ищем записи типа post
        
        # Паттерн для извлечения постов
        # Структура: (ID, post_author, post_date, post_date_gmt, post_content, post_title, post_excerpt, post_status, ...)
        
        row_pattern = r"\((\d+),\s*(\d+),\s*'([^']*)',\s*'([^']*)',\s*'((?:[^'\\]|\\.|'')*)',\s*'((?:[^'\\]|\\.|'')*)',\s*'((?:[^'\\]|\\.|'')*)',\s*'((?:[^'\\]|\\.|'')*)',\s*'[^']*',\s*'[^']*',\s*'[^']*',\s*'[^']*',\s*'((?:[^'\\]|\\.|'')*)',\s*'((?:[^'\\]|\\.|'')*)',\s*\d+,\s*\d+,\s*'[^']*',\s*\d+,\s*'((?:[^'\\]|\\.|'')*)',\s*''"
        
        # Более простой подход - ищем строки с 'publish' и 'post'
        pass
    
    return posts


def extract_posts_simple(sql_file: Path) -> list:
    """Более простой способ извлечения - через grep и парсинг"""
    import subprocess
    
    # Сначала извлечём только INSERT для wp_posts
    print("Извлекаю INSERT для wp_posts...")
    
    result = subprocess.run(
        ['grep', '-a', "INSERT INTO `wp_posts`", str(sql_file)],
        capture_output=True,
        text=True
    )
    
    insert_data = result.stdout
    print(f"Найдено {len(insert_data)} байт данных INSERT")
    
    posts = []
    
    # Паттерн для поиска опубликованных постов
    # Ищем: post_name (slug) и проверяем что post_status = 'publish' и post_type = 'post'
    
    # Разбиваем по ),( для получения отдельных записей
    # Формат записи в wp_posts:
    # ID, post_author, post_date, post_date_gmt, post_content, post_title, 
    # post_excerpt, post_status, comment_status, ping_status, post_password,
    # post_name, to_ping, pinged, post_modified, post_modified_gmt, 
    # post_content_filtered, post_parent, guid, menu_order, post_type, ...
    
    return posts


def load_current_articles() -> dict:
    """Загружает текущие статьи"""
    if ARTICLES_FILE.exists():
        with open(ARTICLES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Поддержка старого формата (массив)
        if isinstance(data, list):
            return {"articles": data, "categories": []}
        return data
    return {"articles": [], "categories": []}


def get_existing_slugs(articles: list) -> set:
    """Возвращает набор существующих slug"""
    return {a.get('slug', '') for a in articles}


def parse_wp_posts_from_sql():
    """Парсит wp_posts напрямую из SQL"""
    import subprocess
    
    print("Извлекаю данные постов из SQL...")
    
    # Извлекаем блок с INSERT INTO wp_posts
    with open(SQL_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Находим начало INSERT INTO wp_posts
    start = content.find("INSERT INTO `wp_posts` VALUES")
    if start == -1:
        print("INSERT INTO wp_posts не найден!")
        return []
    
    # Находим конец этого блока (до следующего CREATE TABLE или INSERT INTO другой таблицы)
    end = content.find("CREATE TABLE", start + 1)
    if end == -1:
        end = len(content)
    
    posts_sql = content[start:end]
    print(f"Блок wp_posts: {len(posts_sql)} символов")
    
    # Теперь парсим каждую запись
    # Записи разделены ),( или заканчиваются );
    posts = []
    
    # Ищем все опубликованные посты типа 'post' через регулярку
    # Паттерн: ,'publish',... ,'post-name',...,'post',
    
    # Используем более надёжный подход - ищем по post_status и post_type
    pattern = r"\((\d+),\d+,'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})','[^']*','((?:[^'\\]|\\.|'')*?)','((?:[^'\\]|\\.|'')*?)','((?:[^'\\]|\\.|'')*?)','publish','[^']*','[^']*','','([a-z0-9_-]+)','[^']*','[^']*','(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})','[^']*','[^']*',\d+,'[^']*',\d+,'post','[^']*',\d+\)"
    
    matches = re.findall(pattern, posts_sql)
    print(f"Найдено {len(matches)} опубликованных постов типа 'post'")
    
    for match in matches:
        post_id, post_date, content, title, excerpt, slug, modified_date = match
        
        # Очищаем экранирование
        title = unescape(title.replace("\\'", "'").replace("\\n", "\n").replace("\\r", ""))
        content = content.replace("\\'", "'").replace("\\n", "\n").replace("\\r", "").replace("\\t", "\t")
        excerpt = excerpt.replace("\\'", "'").replace("\\n", "\n").replace("\\r", "")
        
        posts.append({
            'wp_id': post_id,
            'slug': slug,
            'title': title,
            'content': content,
            'excerpt': excerpt if excerpt else title[:200],
            'created_at': post_date,
            'updated_at': modified_date
        })
    
    return posts


def main():
    print("=" * 60)
    print("Импорт статей из WordPress SQL")
    print("=" * 60)
    
    # Загружаем текущие статьи
    current_data = load_current_articles()
    current_articles = current_data.get('articles', [])
    existing_slugs = get_existing_slugs(current_articles)
    
    print(f"\nТекущих статей: {len(current_articles)}")
    print(f"Существующих slug: {len(existing_slugs)}")
    
    # Парсим WordPress посты
    wp_posts = parse_wp_posts_from_sql()
    print(f"\nНайдено постов в WordPress: {len(wp_posts)}")
    
    # Находим недостающие
    new_articles = []
    duplicates = []
    
    for post in wp_posts:
        slug = post['slug']
        if slug in existing_slugs:
            duplicates.append(slug)
        else:
            # Создаём новую статью
            new_article = {
                "id": str(uuid.uuid4()),
                "slug": slug,
                "title": post['title'],
                "excerpt": post['excerpt'][:500] if post['excerpt'] else post['title'],
                "content": post['content'],
                "category": "usn",  # По умолчанию категория УСН
                "image": "",
                "meta_title": post['title'],
                "meta_description": post['excerpt'][:160] if post['excerpt'] else post['title'][:160],
                "meta_keywords": "",
                "is_published": True,
                "views": 0,
                "created_at": post['created_at'],
                "updated_at": post['updated_at']
            }
            new_articles.append(new_article)
    
    print(f"\nДубликатов (уже есть): {len(duplicates)}")
    print(f"Новых статей для добавления: {len(new_articles)}")
    
    if duplicates:
        print("\nСуществующие статьи:")
        for d in duplicates[:10]:
            print(f"  - {d}")
        if len(duplicates) > 10:
            print(f"  ... и ещё {len(duplicates) - 10}")
    
    if new_articles:
        print("\nНовые статьи:")
        for a in new_articles[:10]:
            print(f"  + {a['slug']}: {a['title'][:50]}...")
        if len(new_articles) > 10:
            print(f"  ... и ещё {len(new_articles) - 10}")
    
    # Сохраняем
    if new_articles:
        all_articles = current_articles + new_articles
        new_data = {
            "articles": all_articles,
            "categories": current_data.get('categories', [])
        }
        
        # Бэкап
        if ARTICLES_FILE.exists():
            backup_file = ARTICLES_FILE.with_suffix('.json.backup')
            import shutil
            shutil.copy(ARTICLES_FILE, backup_file)
            print(f"\nБэкап создан: {backup_file}")
        
        with open(ARTICLES_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)
        
        print(f"\nСохранено! Всего статей: {len(all_articles)}")
    else:
        print("\nНечего добавлять - все статьи уже существуют")
    
    return new_articles


if __name__ == "__main__":
    main()
