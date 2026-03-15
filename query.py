import json
import random
import re
import time
import requests


def get_suggestions(query):
    url = "https://suggest.yandex.ru/suggest-ya.cgi"

    params = {
        "part": query,
        "n": 10,
        "format": "json"
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/119.0.0.0 Safari/537.36"
    }

    try:
        r = requests.get(url, params=params, headers=headers, timeout=5)
        match = re.search(r'\[".*?",\[(.*?)\]', r.text)
        if match:
            suggestions_str = "[" + match.group(1) + "]"
            return json.loads(suggestions_str)
    except Exception as e:
        print(f"Ошибка запроса для '{query}': {e}")

    return []


def collect_queries_to_file(filename, query_type):
    target_count = 300

    print(f"\n--- Начинаем сбор: {query_type} ---")

    query_types = {
        "Branded": PRODUCTS,
        "Categorical": CATEGORIES,
        "Comparative": COMPETITORS,
        "Consultative": CATEGORIES
    }

    for i in query_types[query_type]:
        brand_results = set()

        for letter in ALPHABET:
            if len(brand_results) >= target_count:
                break

            if query_type == "Branded":
                prefix = f"{i} {letter}"

            elif query_type == "Categorical":
                prefix = f"{i} {letter}"

            elif query_type == "Consultative":
                # templates = [f"как выбрать {i} {letter}", f"какой {i} лучше {letter}",
                #              f"{i} для {letter}"]
                # prefix = random.choice(templates)

                templates = [f"как выбрать {i} {letter}", f"какой {i} лучше {letter}",
                             f"{i} для {letter}"]
                for t in templates:
                    suggestions = get_suggestions(t)

                    for sug in suggestions:
                        # Фильтруем мусор и слишком короткие ответы
                        if len(sug) > 3:
                            brand_results.add(sug)

                    time.sleep(random.uniform(0.2, 0.5))

            elif query_type == "Comparative":
                templates = [f"{i} или {comp} {letter}" for comp in COMPETITORS[i]]
                templates.extend([f"{i} vs {letter}", f"{i} сравнение {letter}"])
                for t in templates:
                    suggestions = get_suggestions(t)

                    for sug in suggestions:
                        # Фильтруем мусор и слишком короткие ответы
                        if len(sug) > 3:
                            brand_results.add(sug)

                    time.sleep(random.uniform(0.2, 0.5))

            if query_type not in ("Comparative", "Consultative"):
                suggestions = get_suggestions(prefix)

                for sug in suggestions:
                    # Фильтруем мусор и слишком короткие ответы
                    if len(sug) > 3:
                        brand_results.add(sug)

            # Небольшая пауза, чтобы Яндекс не забанил за частые запросы (DDoS)
            time.sleep(random.uniform(0.2, 0.5))

        print(f"Собрано {len(brand_results)} запросов для {i} ({query_type})")

        # Сохраняем в файл
        with open(f"queries/{filename}_{i}.txt", 'w', encoding='utf-8') as f:
            for item in sorted(brand_results):
                f.write(f"{item}\n")

        print(f"Сохранено в файл {filename}")


# Наш алфавит для перебора "хвостов" запросов
ALPHABET = "абвгдежзийклмнопрстуфхцчшщэюя"

# Словарь: Бренд -> Категорийный запрос (для генерации 2 и 4 типа)
PRODUCTS = ["Oral-B", "Blend-a-Med", "Pampers", "Head & Shoulders", "Pantene", "Herbal Essences", "Old Spice"]
CATEGORIES = ["зубные щетки", "зубная паста", "уход за полостью рта", "подгузники", "шампуни", "бальзамы", "дезодоранты"]
COMPETITORS = {
    "Oral-B": [
        "Colgate",
        "Splat",
        "R.O.C.S",
        "Лесной бальзам",
        "Новый жемчуг",
        "President",
        "Elmex / Meridol",
        "Lacalut",
        "Curaprox",
        "Philips Sonicare",
        "Revyline"
    ],
    "Blend-a-Med": [
        "Colgate",
        "Splat",
        "R.O.C.S.",
        "Лесной бальзам",
        "Новый жемчуг",
        "Biomed",
        "Parodontax"
    ],
    "Pampers": [
        "Huggies",
        "Merries",
        "Moony",
        "Ушастый нянь",
        "Mepsi",
        "Little Swimmers",
        "Bella Baby Happy",
        "Helen Harper",
        "Lupilu"
    ],
    "Head & Shoulders": [
        "Clear",
        "Nizoral",
        "Friderm",
        "Vichy Dercos",
        "Себорин",
        "Librederm",
        "Рецепты бабушки Агафьи"
    ],
    "Pantene": [
        "Dove",
        "TRESemmé",
        "Elseve",
        "Gliss Kur",
        "Schauma",
        "Natura Siberica",
        "Levrana",
        "Botavikos",
        "Mulsan Cosmetic",
        "Estel",
        "Kapous",
        "Concept"
    ],
    "Herbal Essences": [
        "Love Beauty and Planet",
        "Natura Siberica",
        "Levrana",
        "Botanicals",
        "Рецепты бабушки Агафьи",
        "Organic Shop",
        "Planeta Organica",
        "Чистая линия"
    ],
    "Old Spice": [
        "Axe",
        "Dove Men+Care",
        "Nivea Men",
        "Gillette",
        "Palmolive Men",
        "L'Oreal Men Expert",
        "Old O'Clock",
        "Red Line"
    ]
}


if __name__ == "__main__":
    # collect_queries_to_file("1_branded_queries", "Branded")
    collect_queries_to_file("2_categorical_queries.txt", "Categorical")
    # collect_queries_to_file("3_comparative_queries.txt", "Comparative")
    # collect_queries_to_file("4_consultative_queries.txt", "Consultative")