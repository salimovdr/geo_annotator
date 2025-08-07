import os
import json
import requests
from tqdm import tqdm
from xml.etree import ElementTree as ET
import time

INPUT_FILE = "GSM_GSE_dict.json"       # Входной JSON со списком словарей {GSM_id, GSE_id, UID}
OUTPUT_DIR = "batch_chunks_miniml"     # Папка, куда писать чанки JSONL для batch API
CHUNK_SIZE = 20000
MODEL = "gpt-4"
TEMPERATURE = 0.3

os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(INPUT_FILE) as f:
    gsm_list = json.load(f)

def get_miniml_xml(gsm_id, max_retries=5, base_delay=0.5):
    url = f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={gsm_id}&targ=self&form=xml&view=full"

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            if attempt == max_retries:
                print(f"⚠️ [{gsm_id}] Ошибка после {max_retries} попыток: {e}")
                return None
            else:
                delay = base_delay * (2 ** (attempt - 1))
                time.sleep(delay)

def build_prompt(gsm_id, gse_id, miniml_text):
    return f"""Ты биоинформатик. Проанализируй метаданные GEO-эксперимента ниже и верни строго JSON со следующими полями:

- GSM_id
- GSE_id
- taxon: вид животного (например, "Mus musculus", "Rattus norvegicus")
- strain: линия или штамм животного (например, "C57BL/6J", "Wistar", "Sprague-Dawley")
- age_weeks: возраст в неделях (целое или дробное число, если можно извлечь)
- age_bin: одна из категорий возраста: "<4w", "4–8w", "8–20w", ">20w", либо "unknown"
- disease_status: "healthy", "diseased" или "unknown"
- disease_name: если animal diseased — название заболевания (например, "diabetes", "cancer", "asthma"); иначе "none"
- tissue_or_cell_type: тип ткани или клеточной линии (например, "liver", "fibroblast", "bone marrow")
- sc_RNA_seq: True или False — является ли эксперимент single-cell RNA-seq

Если в карточке нет точной информации, логично догадывайся из текста.

=== GEO MINiML START ===
{miniml_text}
=== GEO MINiML END ===
"""

chunk_index = 1
sample_in_chunk = 0
out_path = os.path.join(OUTPUT_DIR, f"batch_chunk_{chunk_index}.jsonl")
out_file = open(out_path, "w", encoding="utf-8")

for entry in tqdm(gsm_list, desc="Скачивание и сохранение"):
    gsm = entry["GSM_id"]
    gse = entry["GSE_id"]
    miniml_text = get_miniml_xml(gsm)
    if not miniml_text:
        continue

    prompt = build_prompt(gsm, gse, miniml_text)
    jsonl_obj = {
        "custom_id": gsm,
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": TEMPERATURE,
            "response_format": "json"
        }
    }

    out_file.write(json.dumps(jsonl_obj, ensure_ascii=False) + "\n")
    sample_in_chunk += 1

    if sample_in_chunk >= CHUNK_SIZE:
        out_file.close()
        chunk_index += 1
        sample_in_chunk = 0
        out_path = os.path.join(OUTPUT_DIR, f"batch_chunk_{chunk_index}.jsonl")
        out_file = open(out_path, "w", encoding="utf-8")

out_file.close()
print(f"✅ Сохранено {chunk_index} чанков в папке {OUTPUT_DIR}")
