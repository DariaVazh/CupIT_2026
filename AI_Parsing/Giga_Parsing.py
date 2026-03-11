import json
import time
import re
from datetime import datetime
from typing import List, Dict
from urllib.parse import urlparse
import os
from dotenv import load_dotenv

# Установка: pip install gigachat python-dotenv
from gigachat import GigaChat
from gigachat.exceptions import GigaChatException, AuthenticationError, RateLimitError

from pathlib import Path

# Создаем базовые пути
BASE_DIR = Path(__file__).parent.absolute()
QUERIES_DIR = BASE_DIR / "queries"
ANSWERS_DIR = BASE_DIR / "answers"
ANALYSIS_DIR = BASE_DIR / "analysis"

# Создаем папки, если их нет
for dir_path in [QUERIES_DIR, ANSWERS_DIR, ANALYSIS_DIR]:
    dir_path.mkdir(exist_ok=True)
    print(f"📁 Папка готова: {dir_path}")

# ============================================
# 1. ФУНКЦИИ ДЛЯ ИЗВЛЕЧЕНИЯ ССЫЛОК ИЗ ОТВЕТА
# ============================================

def extract_gigachat_sources(response_text: str) -> Dict:
    """Извлекает ссылки из ответа GigaChat"""

    # Ищем паттерн [sources=[...]]
    sources_pattern = r'\[sources=\[(.*?)\]\]'
    sources_matches = re.findall(sources_pattern, response_text, re.DOTALL)

    extracted_sources = []
    for match in sources_matches:
        urls = re.findall(r'https?://[^\s,\]]+', match)
        extracted_sources.extend(urls)

    # Ищем все URL в тексте
    all_urls = re.findall(r'https?://[^\s<>"\'\]\)]+', response_text)

    # Объединяем и убираем дубликаты
    unique_sources = list(set(extracted_sources + all_urls))

    # Считаем домены
    domain_counts = {}
    for url in unique_sources:
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            domain = domain.replace('www.', '')
            if domain:
                domain_counts[domain] = domain_counts.get(domain, 0) + 1
        except:
            pass

    return {
        'sources_from_markers': extracted_sources,
        'all_urls': all_urls,
        'unique_sources': unique_sources,
        'domain_counts': domain_counts,
        'total_sources': len(unique_sources)  # ЭТО КЛЮЧЕВОЕ ПОЛЕ
    }


# В начале файла, после импортов, определи словарь с конкурентами
COMPETITORS_BY_CATEGORY = {
    'hair_care': [
        'l\'oreal', 'loreal', 'elseve', 'syoss', 'schwarzkopf', 'gliss kur',
        'nivea', 'dove', 'clear vita abe', 'clear', 'kerastase', 'wella',
        'matrix', 'redken', 'estel', 'constant delight', 'kapous'
    ],
    'baby_care': [
        'huggies', 'merries', 'moony', 'goo.n', 'libero', 'bella baby happy',
        'sun herbal', 'mepsi', 'muumi', 'yoko', 'fixies', 'happy'
    ],
    'oral_care': [
        'philips', 'sonicare', 'colgate', 'sensodyne', 'elmex', 'lacalut',
        'rox', 'splat', 'r.o.c.s.', 'parodontax', 'curaprox', 'reach',
        'aquafresh', 'president', 'biorepair', 'forest balsam', 'lesnoy balsam',
        'новый жемчуг', 'жемчуг'
    ]
}

# Создаем плоский список всех конкурентов
ALL_COMPETITORS = []
for cat_brands in COMPETITORS_BY_CATEGORY.values():
    ALL_COMPETITORS.extend(cat_brands)


def analyze_sources(response_text: str, query: str = None) -> Dict:
    """Анализирует источники и упоминания брендов"""

    # Получаем данные о ссылках
    sources_data = extract_gigachat_sources(response_text)

    # Бренды P&G
    pg_brands = ['oral-b', 'blendamed', 'blend-a-med', 'pampers',
                 'head & shoulders', 'head&shoulders', 'pantene',
                 'herbal essences', 'old spice']

    # Конкуренты
    all_competitors = [
        'loreal', 'l\'oreal', 'elseve', 'syoss', 'schwarzkopf', 'gliss kur',
        'nivea', 'dove', 'clear', 'huggies', 'merries', 'philips', 'sonicare',
        'colgate', 'sensodyne', 'elmex', 'lacalut', 'splat', 'rox'
    ]

    text_lower = response_text.lower()

    # Ищем бренды
    mentioned_pg = [b for b in pg_brands if b.lower() in text_lower]
    mentioned_competitors = [c for c in all_competitors if c.lower() in text_lower]

    # ВОЗВРАЩАЕМ ВСЕ НУЖНЫЕ ПОЛЯ
    return {
        # Данные из extract_gigachat_sources (ВСЕ поля!)
        'sources_from_markers': sources_data['sources_from_markers'],
        'all_urls': sources_data['all_urls'],
        'unique_sources': sources_data['unique_sources'],
        'domain_counts': sources_data['domain_counts'],
        'total_sources': sources_data['total_sources'],  # ЭТО ПОЛЕ ОБЯЗАТЕЛЬНО

        # Данные о брендах
        'mentioned_pg_brands': list(set(mentioned_pg)),
        'mentioned_competitors': list(set(mentioned_competitors)),
        'pg_brand_count': len(set(mentioned_pg)),
        'competitor_count': len(set(mentioned_competitors))
    }
# ============================================
# 2. ФУНКЦИЯ ДЛЯ ОПРЕДЕЛЕНИЯ ТИПА ЗАПРОСА
# ============================================

def get_query_type(query: str) -> str:
    """Определяет тип поискового запроса"""
    query_lower = query.lower()

    # Брендовые запросы
    brands = ['oral-b', 'pampers', 'head shoulders', 'pantene', 'blendamed']
    if any(brand in query_lower for brand in brands):
        return 'brand'

    # Сравнительные запросы
    compare_words = ['сравнение', 'vs', 'или', 'лучше', 'против']
    if any(word in query_lower for word in compare_words) and len(query_lower.split()) > 2:
        return 'comparison'

    # Вопросы/консультации
    question_words = ['как', 'какой', 'почему', 'что', 'сколько']
    if any(word in query_lower for word in question_words) and '?' in query_lower[-3:]:
        return 'consultation'

    # По умолчанию - категорийный
    return 'category'


# ============================================
# 3. СОЗДАНИЕ ЗАПИСИ ДЛЯ АНАЛИЗА
# ============================================

def create_record(query: str, response_text: str = None, error: str = None):
    """Создает структурированную запись для сохранения"""
    if error:
        return {
            'query': query,
            'query_type': get_query_type(query),
            'error': error,
            'timestamp': datetime.now().isoformat()
        }

    # Получаем данные
    sources_analysis = analyze_sources(response_text, query)

    # ✅ ПРАВИЛЬНО: берем значения из sources_analysis
    return {
        'query': query,
        'query_type': get_query_type(query),
        'response_text': response_text,
        'timestamp': datetime.now().isoformat(),

        # Источники - берем КОНКРЕТНЫЕ поля
        'sources_from_markers': sources_analysis['sources_from_markers'],
        'all_urls': sources_analysis['all_urls'],
        'unique_sources': sources_analysis['unique_sources'],
        'domain_counts': sources_analysis['domain_counts'],
        'total_sources': sources_analysis['total_sources'],  # ЭТО КЛЮЧЕВОЕ ПОЛЕ

        # Бренды
        'mentioned_pg_brands': sources_analysis['mentioned_pg_brands'],
        'mentioned_competitors': sources_analysis['mentioned_competitors'],
        'pg_brand_count': sources_analysis['pg_brand_count'],
        'competitor_count': sources_analysis['competitor_count']
    }

# ============================================
# 4. ОСНОВНАЯ ФУНКЦИЯ ДЛЯ ЗАПУСКА ИССЛЕДОВАНИЯ
# ============================================

def run_research(queries: List[str], credentials: str,
                 output_filename: str = 'answers') -> List:
    """
    Запускает исследование с сохранением в папку answers/

    Аргументы:
        queries: список запросов
        credentials: ключ GigaChat
        output_filename: имя для выходного файла (без .json)
    """
    results = []
    failed = []

    print(f"🚀 Начинаем обработку {len(queries)} запросов...")
    print("=" * 60)

    client = GigaChat(
        credentials=credentials,
        verify_ssl_certs=False,
        model="GigaChat",
        timeout=60
    )

    for i, query in enumerate(queries):
        print(f"\n📝 [{i + 1}/{len(queries)}] Запрос: {query[:80]}...")

        try:
            # Добавляем инструкцию для поиска
            enhanced_query = f"{query}\n\nВажно: Найди актуальную информацию в интернете и обязательно укажи ссылки на источники."

            response = client.chat(enhanced_query)
            answer = response.choices[0].message.content

            record = create_record(query, answer)
            results.append(record)

            print(f"   ✅ Успешно")
            print(f"   📊 Источников найдено: {record['total_sources']}")

            if record['mentioned_pg_brands']:
                print(f"   🏷️ Бренды P&G: {', '.join(record['mentioned_pg_brands'])}")

            # Сохраняем каждые 5 запросов
            if (i + 1) % 5 == 0:
                save_results_to_folder(results, failed, output_filename, "answers")

        except KeyboardInterrupt:
            print(f"\n⚠️ Прервано пользователем. Сохраняем...")
            save_results_to_folder(results, failed, output_filename, "answers")
            break

        except Exception as e:
            print(f"   ❌ Ошибка: {str(e)[:100]}")
            failed.append(create_record(query, error=str(e)))

        time.sleep(1)

    # Финальное сохранение
    final_path = save_results_to_folder(results, failed, output_filename, "answers")
    print(f"\n🎉 Готово! Результаты в: {final_path}")
    print(f"   Успешно: {len(results)}, Ошибок: {len(failed)}")

    return results

def save_results(results: List, failed: List, output_file: str):
    """Сохраняет результаты в JSON файл"""
    data = {
        'metadata': {
            'total_queries': len(results) + len(failed),
            'successful': len(results),
            'failed': len(failed),
            'timestamp': datetime.now().isoformat(),
            'model': 'GigaChat'
        },
        'results': results,
        'failed_queries': failed
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return data


# ============================================
# 5. ФУНКЦИЯ ДЛЯ ЗАГРУЗКИ ЗАПРОСОВ ИЗ ФАЙЛА
# ============================================

def load_queries(filename: str = 'Oral-B_Brand_Queries.txt') -> List[str]:
    """Загружает запросы из текстового файла"""
    if not os.path.exists(filename):
        # Создаем пример файла, если его нет
        example_queries = [
            "какой шампунь лучше от перхоти",
            "сравнение подгузников Pampers и Huggies",
            "Oral-B электрическая зубная щетка отзывы",
            "что лучше Pantene или Head Shoulders",
            "как выбрать зубную пасту"
        ]
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(example_queries))
        print(f"📄 Создан пример файла {filename} с {len(example_queries)} запросами")
        return example_queries

    with open(filename, 'r', encoding='utf-8') as f:
        queries = [line.strip() for line in f if line.strip()]
    print(f"📄 Загружено {len(queries)} запросов из {filename}")
    return queries


def load_queries_from_file(filename: str) -> List[str]:
    """
    Загружает запросы из файла в папке queries/

    Аргументы:
        filename: имя файла (например, 'oral_b_brand.txt')

    Возвращает:
        список запросов
    """
    file_path = QUERIES_DIR / filename

    if not file_path.exists():
        print(f"❌ Файл не найден: {file_path}")
        print("📝 Создаю пример файла...")

        # Создаем пример файла с тестовыми запросами
        example_queries = [
            "Какая новая модель Oral-B вышла в 2025 году?",
            "Обновленная линейка Oral-B iO в 2026 году отзывы",
            "Сравнение Oral-B iO10 и Philips Sonicare",
            "Как часто менять насадки Oral-B?",
            "Oral-B с искусственным интеллектом отзывы"
        ]

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(example_queries))

        print(f"✅ Создан пример файла: {file_path}")
        return example_queries

    with open(file_path, 'r', encoding='utf-8') as f:
        queries = [line.strip() for line in f if line.strip()]

    print(f"📄 Загружено {len(queries)} запросов из {file_path}")
    return queries


def load_all_queries_from_folder() -> Dict[str, List[str]]:
    """
    Загружает все .txt файлы из папки queries/

    Возвращает:
        словарь {имя_файла: список_запросов}
    """
    all_queries = {}

    # Ищем все .txt файлы в папке queries
    txt_files = list(QUERIES_DIR.glob("*.txt"))

    if not txt_files:
        print("❌ В папке queries нет .txt файлов")
        return all_queries

    for file_path in txt_files:
        filename = file_path.name
        queries = load_queries_from_file(filename)
        if queries:
            all_queries[filename] = queries

    return all_queries
# ============================================
# 6. ФУНКЦИЯ ДЛЯ АНАЛИЗА РЕЗУЛЬТАТОВ
# ============================================

def analyze_results(filename: str = 'pg_results.json'):
    """Анализирует собранные данные и выводит статистику"""
    import json
    from collections import Counter

    if not os.path.exists(filename):
        print(f"❌ Файл {filename} не найден")
        return

    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("\n" + "=" * 60)
    print("📊 АНАЛИЗ РЕЗУЛЬТАТОВ")
    print("=" * 60)

    results = data['results']

    if not results:
        print("❌ Нет данных для анализа")
        return

    # Общая статистика
    print(f"\n📈 Всего успешных запросов: {len(results)}")

    # Статистика по типам запросов
    query_types = {}
    for r in results:
        qtype = r.get('query_type', 'unknown')
        query_types[qtype] = query_types.get(qtype, 0) + 1

    print("\n🔍 Типы запросов:")
    for qtype, count in query_types.items():
        print(f"   {qtype}: {count} ({count / len(results) * 100:.1f}%)")

    # Топ платформ
    all_domains = []
    for r in results:
        all_domains.extend(r.get('domain_counts', {}).keys())

    top_domains = Counter(all_domains).most_common(10)

    print("\n🌐 Топ-10 платформ (источников):")
    if top_domains:
        for domain, count in top_domains:
            print(f"   {domain}: {count}")
    else:
        print("   (нет данных об источниках)")

    # Упоминания брендов P&G
    all_pg_brands = []
    for r in results:
        all_pg_brands.extend(r.get('mentioned_pg_brands', []))

    top_pg = Counter(all_pg_brands).most_common()

    print("\n🏷️ Упоминания брендов P&G:")
    if top_pg:
        for brand, count in top_pg:
            print(f"   ✅ {brand}: {count}")
    else:
        print("   Бренды P&G не найдены в ответах")

    # Упоминания конкурентов
    all_competitors = []
    for r in results:
        all_competitors.extend(r.get('mentioned_competitors', []))

    top_comp = Counter(all_competitors).most_common()

    print("\n🔄 Упоминания конкурентов:")
    if top_comp:
        for comp, count in top_comp:
            print(f"   🔴 {comp}: {count}")
    else:
        print("   Конкуренты не найдены в ответах")

    # Среднее количество источников
    total_sources = sum(r.get('total_sources', 0) for r in results)
    avg_sources = total_sources / len(results)
    print(f"\n🔗 Среднее количество источников на запрос: {avg_sources:.1f}")

    # Дополнительно: запросы без упоминаний P&G (слепые зоны)
    pg_mentions_count = sum(1 for r in results if r.get('pg_brand_count', 0) > 0)
    print(
        f"\n🎯 Запросы с упоминанием P&G: {pg_mentions_count}/{len(results)} ({pg_mentions_count / len(results) * 100:.1f}%)")

    competitor_mentions_count = sum(1 for r in results if r.get('competitor_count', 0) > 0)
    print(
        f"   Запросы с упоминанием конкурентов: {competitor_mentions_count}/{len(results)} ({competitor_mentions_count / len(results) * 100:.1f}%)")


def save_results_to_folder(results: List, failed: List,
                           base_filename: str,
                           subfolder: str = "answers") -> str:
    """
    Сохраняет результаты в указанную папку с временной меткой

    Аргументы:
        results: список успешных результатов
        failed: список ошибочных запросов
        base_filename: базовое имя файла (например, 'oral_b_brand')
        subfolder: подпапка ('answers' или 'analysis')

    Возвращает:
        полный путь к сохраненному файлу
    """

    # Выбираем папку
    if subfolder == "answers":
        target_dir = ANSWERS_DIR
    elif subfolder == "analysis":
        target_dir = ANALYSIS_DIR
    else:
        target_dir = BASE_DIR / subfolder

    target_dir.mkdir(exist_ok=True)

    # Добавляем временную метку
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{base_filename}_{timestamp}.json"
    file_path = target_dir / filename

    data = {
        'metadata': {
            'total_queries': len(results) + len(failed),
            'successful': len(results),
            'failed': len(failed),
            'timestamp': datetime.now().isoformat(),
            'model': 'GigaChat',
            'source_file': base_filename
        },
        'results': results,
        'failed_queries': failed
    }

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"💾 Результаты сохранены: {file_path}")
    return str(file_path)


def analyze_results_from_file(filename: str):
    """
    Анализирует результаты из файла в папке answers/

    Аргументы:
        filename: имя файла (например, 'oral_b_brand_20260310_143022.json')
    """
    file_path = ANSWERS_DIR / filename if not os.path.isabs(filename) else Path(filename)

    if not file_path.exists():
        print(f"❌ Файл не найден: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Сохраняем анализ в папку analysis
    analysis_filename = f"analysis_{file_path.stem}.json"
    analysis_path = ANALYSIS_DIR / analysis_filename

    # Здесь твой код анализа (как в analyze_results)
    # ...

    print(f"📊 Анализ сохранен: {analysis_path}")
# ============================================
# 7. ЗАПУСК
# ============================================

# Конкуренты P&G по категориям
competitors = {
    'hair_care': [
        'l\'oreal', 'loreal', 'elseve',  # L'Oreal
        'syoss',
        'schwarzkopf', 'gliss kur',
        'nivea',
        'dove',
        'clear vita abe', 'clear',
        'elseve',
        'kerastase',
        'wella',
        'matrix',
        'redken'
    ],
    'baby_care': [
        'huggies',
        'merries',
        'moony',
        'goo.n',
        'libero',
        'bella baby happy',
        'sun herbal',
        'mepsi',
        'muumi'
    ],
    'oral_care': [
        'philips', 'sonicare',  # Philips зубные щетки
        'colgate',
        'sensodyne',
        'elmex',
        'lacalut',
        'rox',
        'splat',
        'r.o.c.s.',
        'parodontax',
        'curaprox',
        'reach',
        'aquafresh'
    ]
}

# Также создадим общий плоский список для удобства поиска
all_competitors = []
for category_brands in competitors.values():
    all_competitors.extend(category_brands)

if __name__ == "__main__":
    print("🔷 P&G GigaChat Research Tool 🔷")
    print("=" * 60)

    # Загружаем ключ
    load_dotenv()
    GIGACHAT_CREDENTIALS = os.getenv("GIGACHAT_CREDENTIALS")

    if not GIGACHAT_CREDENTIALS:
        print("❌ ОШИБКА: Нет ключа в .env файле!")
        exit(1)

    # Выбираем режим работы
    print("\nВыберите режим работы:")
    print("1. Загрузить запросы из конкретного файла")
    print("2. Загрузить все файлы из папки queries/")
    print("3. Анализировать существующий файл с ответами")

    mode = input("\nВведите номер (1/2/3): ").strip()

    if mode == "1":
        # Показываем доступные файлы
        txt_files = list(QUERIES_DIR.glob("*.txt"))
        if txt_files:
            print("\nДоступные файлы запросов:")
            for i, f in enumerate(txt_files):
                print(f"   {i + 1}. {f.name}")

        filename = input("\nВведите имя файла (например, oral_b_brand.txt): ").strip()
        queries = load_queries_from_file(filename)

        if queries:
            # Имя для выходного файла (без .txt)
            output_name = filename.replace('.txt', '')
            run_research(queries, GIGACHAT_CREDENTIALS, output_name)

    elif mode == "2":
        # Загружаем все файлы
        all_queries = load_all_queries_from_folder()

        for filename, queries in all_queries.items():
            print(f"\n{'=' * 60}")
            print(f"Обработка файла: {filename}")
            print('=' * 60)

            output_name = filename.replace('.txt', '')
            run_research(queries, GIGACHAT_CREDENTIALS, output_name)

    elif mode == "3":
        # Показываем доступные файлы с ответами
        json_files = list(ANSWERS_DIR.glob("*.json"))
        if json_files:
            print("\nДоступные файлы с ответами:")
            for i, f in enumerate(json_files):
                print(f"   {i + 1}. {f.name}")

            filename = input("\nВведите имя файла для анализа: ").strip()
            analyze_results_from_file(filename)
        else:
            print("❌ В папке answers нет JSON файлов")

    else:
        print("❌ Неверный режим")
