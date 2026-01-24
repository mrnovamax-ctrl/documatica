#!/usr/bin/env python3
"""
Скрипт импорта WordPress pages (страниц) в articles.json
Извлекает страницы, которые отсутствуют как статьи
"""

import json
import re
import uuid
from datetime import datetime
import html

# Целевые слаги страниц для импорта
TARGET_SLUGS = [
    'kak_likvidirovat_ip', 
    'kak_likvidirovat_ooo', 
    'forma_p13014', 
    'nulevaya-deklaraciya-zapolnit'
]

def clean_html(content):
    """Очистка HTML от лишних пробелов"""
    if not content:
        return ""
    # Декодируем HTML entities
    content = html.unescape(content)
    # Убираем лишние переносы
    content = re.sub(r'\n\s+', '\n', content)
    return content.strip()

def parse_sql_pages(sql_file):
    """Парсинг WordPress pages из SQL дампа"""
    pages = []
    
    with open(sql_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Ищем INSERT для wp_posts
    pattern = r"INSERT INTO `wp_posts` VALUES \(([^;]+)\);"
    matches = re.findall(pattern, content, re.DOTALL)
    
    print(f"Найдено INSERT блоков: {len(matches)}")
    
    for match in matches:
        # Разбиваем на отдельные записи
        # Формат: (id,author,date,date_gmt,content,title,excerpt,status,...,post_name,...,post_type,...)
        # Ищем записи с нужными слагами
        for slug in TARGET_SLUGS:
            if f"'{slug}'" in match and "'publish'" in match and "'page'" in match:
                # Пробуем извлечь данные
                try:
                    # Ищем slug в match
                    record_pattern = rf"\((\d+),(\d+),'([^']+)','([^']+)','((?:[^']|'')*?)','([^']+)','(?:[^']|'')*?','publish','[^']*','[^']*','','{re.escape(slug)}'"
                    record_match = re.search(record_pattern, match)
                    
                    if record_match:
                        post_id = record_match.group(1)
                        post_date = record_match.group(3)
                        post_content = record_match.group(5).replace("''", "'")
                        post_title = record_match.group(6).replace("''", "'")
                        
                        pages.append({
                            'id': post_id,
                            'slug': slug.replace('_', '-'),  # Нормализуем слаг
                            'title': html.unescape(post_title),
                            'content': clean_html(post_content),
                            'date': post_date
                        })
                        print(f"  Найдена страница: {slug} (ID: {post_id})")
                except Exception as e:
                    print(f"  Ошибка парсинга {slug}: {e}")
    
    return pages

def main():
    sql_file = 'u2149247_oplatanalogov.sql'
    articles_file = 'backend/data/articles.json'
    
    # Загружаем существующие статьи
    with open(articles_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    existing_slugs = {a['slug'] for a in data['articles']}
    print(f"Существующих статей: {len(data['articles'])}")
    
    # Парсим страницы из SQL
    print("\nПоиск страниц в SQL...")
    pages = parse_sql_pages(sql_file)
    
    # Добавляем недостающие
    added = 0
    for page in pages:
        if page['slug'] not in existing_slugs:
            new_article = {
                'id': str(uuid.uuid4()),
                'title': page['title'],
                'slug': page['slug'],
                'content': page['content'],
                'excerpt': page['content'][:200] + '...' if len(page['content']) > 200 else page['content'],
                'category': 'Сервисы',
                'status': 'published',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'meta_title': page['title'],
                'meta_description': page['title'],
                'featured_image': None,
                'author': 'admin',
                'views': 0,
                'source': 'wordpress_page'
            }
            data['articles'].append(new_article)
            added += 1
            print(f"  Добавлена: {page['slug']}")
    
    # Сохраняем
    with open(articles_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n=== Результат ===")
    print(f"Добавлено страниц: {added}")
    print(f"Всего статей: {len(data['articles'])}")

if __name__ == '__main__':
    main()
