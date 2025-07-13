# Аннотация GSM в GEO database

Нас интересуют данные sc RNA seq экспериментов на мышах и крысах. Необходимо единообразно аннотировать данные, включая информацию о:
- виде;
- линии организма;
- возраст;
- болен организм или здоровый;
- градации возраста;
- типе ткани или клеточной линии.

## Первонаяальная фильтрация

Идентификаторы GSM для мышей или крыс с данными sc RNA seq экспериментов продилась в веб-интерфейсе GEO с помощью запроса:

`("Mus musculus"[Organism] OR "Rattus norvegicus"[Organism]) AND ("single cell"[All Fields] OR "single-cell"[All Fields] OR "scRNA-seq"[All Fields] OR "sc RNA-seq"[All Fields] OR "scRNA seq"[All Fields] OR "sc RNA seq"[All Fields] OR "scRNAseq"[All Fields] OR "sc-rna-seq"[All Fields] OR "single-cell RNA"[All Fields] OR "single cell RNA seq"[All Fields] OR "single-cell transcriptome"[All Fields] OR "10x"[All Fields] OR "10x Genomics"[All Fields] OR "Smart-seq"[All Fields] OR "Drop-seq"[All Fields] OR "sci-RNA-seq"[All Fields] OR "Seq-Well"[All Fields] OR "MARS-seq"[All Fields] OR "Microwell-seq"[All Fields])`

Результат запроса (список уникальных id) был сохранён в файл UID_list.txt.
