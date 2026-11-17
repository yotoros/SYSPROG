# Legendary Task: обработчик файлов

Скрипт `processor.py` берёт файлы из папки `input_orders`, переименовывает
и перекладывает в `output_processed`.

Сделано на Python, только стандартные библиотеки (os, shutil, time, logging, pathlib, argparse).

## Что решает

Три проблемы из ТЗ:
- **одинаковые имена** — к имени добавляется timestamp в миллисекундах, два файла `order.txt` не столкнутся;
- **большие файлы** — `shutil.move` на одном диске это просто переименование, файл не читается целиком в память;
- **файл занят другим процессом** — перехватывается `PermissionError`, программа не падает, а пишет в лог и идёт дальше.

## Как проверить
python processor.py --generate
python processor.py --process

Подробности и скриншоты — в [report.md](report.md).