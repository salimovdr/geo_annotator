#!/usr/bin/env python3

import asyncio
import time
import json
import argparse
from pathlib import Path
from openai import AsyncOpenAI

# === Настройки ===
BASE_URL = "http://80.209.242.40:8000/v1"
API_KEY = "dummy-key"
MODEL_NAME = "llama-3.3-70b-instruct"
MAX_CONCURRENT_REQUESTS = 50  # ≈3000 в минуту
REQUESTS_PER_MINUTE = 3000
DELAY_BETWEEN_BATCHES = 60 / (REQUESTS_PER_MINUTE / MAX_CONCURRENT_REQUESTS)

# === Отправка одного запроса ===
async def send_request(client, content, semaphore, idx, custom_id=None):
    async with semaphore:
        await asyncio.sleep(DELAY_BETWEEN_BATCHES)  # ограничение по RPS

        try:
            start_time = time.time()
            response = await client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": content}],
                max_tokens=512,
                temperature=0.3,
                response_format="json"
            )
            latency = time.time() - start_time
            return {
                "id": custom_id if custom_id else idx,
                "response": response.choices[0].message.content,
                "latency": latency,
            }
        except Exception as e:
            return {
                "id": custom_id if custom_id else idx,
                "response": None,
                "error": str(e),
            }

# === Главная функция ===
async def main(input_path):
    input_path = Path(input_path)
    output_path = input_path.with_name(input_path.stem + "_responses.jsonl")

    # Загружаем все строки из JSONL
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = [json.loads(line) for line in f]

    # Извлекаем запросы
    prompts = []
    for idx, line in enumerate(lines):
        try:
            content = line["body"]["messages"][0]["content"]
            custom_id = line.get("custom_id", f"id_{idx}")
            prompts.append((idx, custom_id, content))
        except Exception as e:
            print(f"❌ Ошибка в строке {idx}: {e}")
            continue

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    client = AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY)

    tasks = [
        send_request(client, content, semaphore, idx, custom_id)
        for idx, custom_id, content in prompts
    ]

    # Сохраняем по мере получения
    with open(output_path, 'w', encoding='utf-8') as out_file:
        for future in asyncio.as_completed(tasks):
            result = await future
            out_file.write(json.dumps(result, ensure_ascii=False) + '\n')
            print(f"✅ {result['id']}: {result['response'][:80] if result['response'] else result.get('error')}")

    print(f"\n📄 Все ответы сохранены в файл: {output_path}")

# === Точка входа ===
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Отправка запросов в LLM из .jsonl файла.")
    parser.add_argument("input_file", help="Путь к .jsonl файлу с запросами")
    args = parser.parse_args()

    asyncio.run(main(args.input_file))
