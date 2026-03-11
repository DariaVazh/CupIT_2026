# view_full_response.py
from gigachat import GigaChat
import os
from dotenv import load_dotenv
import json

# Загружаем ключ
load_dotenv()
key = os.getenv('GIGACHAT_CREDENTIALS')

print("🔷 Просмотр полного ответа GigaChat 🔷")
print("=" * 60)

# Создаем клиента
client = GigaChat(
    credentials=key,
    verify_ssl_certs=False,
    model="GigaChat",
    timeout=60
)

# Твой запрос (можешь изменить на любой)
query = "Найди в интернете информацию о новых моделях Oral-B, вышедших в 2025 году. Используй поиск и обязательно укажи ссылки на источники в формате [sources=[url1, url2, ...]]"
print(f"\n📝 Запрос: {query}")
print("\n" + "=" * 60)

try:
    # Отправляем запрос
    response = client.chat(query)

    # Получаем полный ответ
    full_response = response.choices[0].message.content

    print("\n📄 ПОЛНЫЙ ОТВЕТ МОДЕЛИ:")
    print("=" * 60)
    print(full_response)
    print("=" * 60)

    # Дополнительно: показываем сырой ответ, если есть структура
    print("\n🔧 Сырой ответ (если есть доп. поля):")
    print(json.dumps(response.choices[0].message.dict(), ensure_ascii=False, indent=2))

    # Анализируем наличие ссылок
    print("\n🔍 АНАЛИЗ ССЫЛОК:")
    print("=" * 60)

    # Ищем паттерн [sources=[...]]
    import re

    sources_pattern = r'\[sources=\[(.*?)\]\]'
    matches = re.findall(sources_pattern, full_response, re.DOTALL)

    if matches:
        print(f"✅ Найден блок sources: {len(matches)} шт.")
        for i, match in enumerate(matches):
            print(f"\n   Блок {i + 1}:")
            # Извлекаем URL из блока
            urls = re.findall(r'https?://[^\s,\]]+', match)
            for j, url in enumerate(urls):
                print(f"      {j + 1}. {url}")
    else:
        print("❌ Блок sources не найден")

        # Ищем обычные URL
        all_urls = re.findall(r'https?://[^\s<>"\'\]\)]+', full_response)
        if all_urls:
            print(f"\n✅ Найдены обычные URL: {len(all_urls)} шт.")
            for i, url in enumerate(all_urls[:10]):  # покажем первые 10
                print(f"   {i + 1}. {url}")
        else:
            print("❌ Ссылки не найдены")

except Exception as e:
    print(f"❌ Ошибка: {e}")