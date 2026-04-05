import requests
import json

API_URL = "http://127.0.0.1:8000/analyze-incident"

payload = {
    "description": (
        "В 14:30 по Москве мониторинг зафиксировал падение production-кластера PostgreSQL. "
        "Количество коннектов превысило лимит (max_connections), из-за чего API-серверы "
        "начали возвращать 500 ошибку. Загрузка CPU на сервере БД была на уровне 99%."
    )
}

print(f"Отправляем запрос на {API_URL}...\n")

try:
    response = requests.post(API_URL, json=payload, timeout=30)

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        print("Ответ успешно получен и распарсен (JSON):")
        print(json.dumps(response.json(), indent=4, ensure_ascii=False))
    else:
        print("Ошибка сервера:")
        print(response.text)

except requests.exceptions.ConnectionError:
    print("Ошибка соединения! Убедитесь, что FastAPI сервер запущен.")
except requests.exceptions.Timeout:
    print("Сервер слишком долго отвечает.")