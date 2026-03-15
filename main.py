import os
import time
from urllib.parse import urlparse
import requests
import base64
import xml.etree.ElementTree as ET
import csv
from bs4 import BeautifulSoup
from API_key import *


def get_response_by_yandexAPI(query, folder_id, api_key, page=0):
    url = "https://searchapi.api.cloud.yandex.net/v2/web/search"

    headers = {
        "Authorization": f"Api-Key {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "query": {
            "searchType": "SEARCH_TYPE_RU",
            "queryText": query,
            "page": page
        },
        "groupSpec": {
            "groupMode": "GROUP_MODE_FLAT",
            "groupsOnPage": 20,
            "docsInGroup": 1
        },
        "folderId": folder_id,
        # "responseFormat": "FORMAT_XML"
        "responseFormat": "FORMAT_HTML"
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        print(response.status_code)
        # return response.json()

        if response.status_code != 200:
            print(f"Ошибка запроса: ({response.status_code}) для запроса '{query}': {response.text}")
            return None

        data = response.json()

        # if "rawData" not in data:
        #     print(f"Нет rawData для запроса '{query}'")
        #     return None

        raw_base64 = data["rawData"]
        response = base64.b64decode(raw_base64).decode("utf-8")
        return response

    except Exception as e:
        print(f"❌ Сетевая ошибка при обработке '{query}': {e}")
        return None


def parse_xml(xml_data):
    root = ET.fromstring(xml_data)
    results = []

    for position, doc in enumerate(root.findall(".//doc"), start=1):
        title = doc.findtext("title")
        url = doc.findtext("url")
        domain = doc.findtext("domain")

        snippet = ""
        passages = doc.findall(".//passage")

        if passages:
            snippet = passages[0].text

        results.append({
            "position": position,
            "title": title,
            "url": url,
            "domain": domain,
            "snippet": snippet
        })

    return results


def get_response_by_scraper(query, api_key):
    # Тот самый сайт, который мы хотим «ограбить» (обязательно кодируем пробелы в +, но requests сделает это за нас)
    target_url = f"https://yandex.ru/search/?text={query}"

    # Точка входа ScraperAPI
    scraper_url = "http://api.scraperapi.com"

    # Настройки для наших наемников
    payload = {
        "api_key": api_key,
        "url": target_url,
        "render": "true",
        "premium": "true"# Включи, если Яндекс начнет отдавать пустой JS (запускает реальный браузер на их стороне)
        # "country_code": "ru"  # Очень важно для Яндекса, чтобы выдача была российской, а не глобальной
    }

    print("Отправляем запросы в матрицу... Это может занять 10-20 секунд.")

    try:
        response = requests.get(scraper_url, params=payload)  #, timeout=60
        print(response.status_code)

        if response.status_code == 200:
            print("Данные успешно захвачены! Начинаем препарирование.\n")

            return response


        else:
            print(f"Провал миссии. Сервер вернул код: {response.status_code}")
            return None

    except Exception as e:
        print(f"Глобальный сбой реальности: {e}")
        return None


def parse_html(response, query):
    soup = BeautifulSoup(response, "lxml")
    items = soup.find_all("li", class_="serp-item")
    results = []
    index = 1

    for item in items:
        if item.get("data-fast-name") is not None:
            continue

        title = item.find("h2").get_text()

        url_tag = item.find("a", class_="OrganicTitle-Link")
        url = url_tag.get("href") if url_tag and "href" in url_tag.attrs else "-"

        domain = "-"
        if url.startswith('http'):
            parsed_uri = urlparse(url)
            domain = parsed_uri.netloc

        snippet_tag = item.find("div", class_="OrganicText")
        snippet = snippet_tag.get_text(separator=" ", strip=True) if snippet_tag else "-"

        results.append({
            "query": query,
            "position": index,
            "title": title,
            "domain": domain,
            "url": url,
            "snippet": snippet
        })

        index += 1

    return results


def save_to_csv(results, filename):
    if not results:
        return

    file_exists = os.path.isfile(filename)

    with open(filename, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["query", "position", "title", "domain", "url", "snippet"],
            delimiter=";"
        )
        if not file_exists:
            writer.writeheader()
        writer.writerows(results)


def load_queries_from_file(filepath):
    queries = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            clean_line = line.strip()
            queries.append(clean_line)
    return queries


def main(filename, i):
    input_file = f"queries/{filename}"
    output_file = f"results/{i}_parsed_{filename[2:-4]}.csv"

    print(f"Чтение запросов из {input_file}...")
    queries = load_queries_from_file(input_file)

    for i, query in enumerate(queries, 1):
        print(f"[{i}/{len(queries)}] Парсинг выдачи по запросу: {query}")

        html_data = get_response_by_yandexAPI(query, MY_FOLDER_ID, MY_API_KEY)

        if html_data:
            parsed_data = parse_html(html_data, query)
            if parsed_data:
                save_to_csv(parsed_data, output_file)
                print(f"  └ Сохранено результатов: {len(parsed_data)}")
            else:
                print(f"  └ Результатов не найдено (возможно, пустая выдача).")

        time.sleep(1)

    print(f"\n✅ Работа завершена. Все данные сохранены в {output_file}")


if __name__ == "__main__":
    files = os.listdir("queries")
    files = [f for f in files if f[0] == "2"]
    for i, filename in enumerate(files):
        main(filename, i + 1)