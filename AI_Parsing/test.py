# test_auth.py
from gigachat import GigaChat
import os
from dotenv import load_dotenv

load_dotenv()
key = os.getenv('GIGACHAT_CREDENTIALS')

print(f"Длина ключа: {len(key) if key else 0} символов")
print(f"Начало ключа: {key[:20]}...")

try:
    # Создаем клиент с отключенной проверкой SSL для Windows
    client = GigaChat(
        credentials=key,
        verify_ssl_certs=False,  # Важно для Windows!
        model="GigaChat"
    )

    # Пробуем получить токен (это проверит ключ)
    token = client.get_token()
    print("✅ Ключ работает! Токен получен")

except Exception as e:
    print(f"❌ Ошибка: {e}")