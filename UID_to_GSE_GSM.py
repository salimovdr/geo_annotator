from Bio import Entrez
from tqdm import tqdm
import time
import json
import logging

logging.basicConfig(filename='error_log.txt', level=logging.ERROR, format='%(asctime)s: %(levelname)s: %(message)s')

Entrez.email = "salimovdan1988@gmail.com"

with open("UID_list.txt") as f:
    uid_list = [line.strip() for line in f if line.strip().isdigit()]

def chunks(lst, n):
    """Разделяет список на части размером n."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

exp_list = []

for batch_number, batch in enumerate(tqdm(list(chunks(uid_list, 200)), desc="Fetching GSEs", unit="batch"), start=1):
    success = False
    for attempt in range(5):  # максимум 5 попыток
        try:
            handle = Entrez.esummary(db="gds", id=",".join(batch))
            summary = Entrez.read(handle)
            
            for doc in summary:
                exp_list.append({'UID': doc['Id'], 'GSM_id': doc["Accession"], 'GSE_id': doc.get('GSE', 'N/A')})
            
            with open('GSM_GSE_dict.json', 'w') as outfile:
                json.dump(exp_list, outfile)

            success = True
            break 

        except Exception as e:
            logging.error(f"Ошибка в батче {batch_number} (попытка {attempt + 1}): {e}")
            
            time.sleep(1 + attempt) 
            
    if not success:
        print(f"Не удалось обработать батч {batch_number} после 5 попыток.")

    time.sleep(0.2)  # Общая задержка между батчами

print('Преобразование из UID в GSM/GSE завершено.')