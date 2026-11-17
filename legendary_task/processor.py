import os
import shutil
import time
import logging
from pathlib import Path
import argparse

# Настройка логирования для отслеживания процесса
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_test_data(input_dir: Path, count: int = 500):
    """Генерирует тестовые данные: дубликаты, большой файл и файл для блокировки."""
    input_dir.mkdir(parents=True, exist_ok=True)
    
    for i in range(count):
        # Создаем намеренные дубликаты имен (каждый 10-й файл)
        name = "order.txt" if i % 10 == 0 else f"document_{i}.txt"
        file_path = input_dir / name
        
        # Один файл делаем большим (50 МБ) для проверки работы с объемом
        size = 50 * 1024 * 1024 if i == 5 else 1024 
        
        with open(file_path, "wb") as f:
            f.write(os.urandom(size))
            
    # Файл, который мы заблокируем вручную для проверки обработки ошибок
    locked_file = input_dir / "locked_document.txt"
    with open(locked_file, "w", encoding="utf-8") as f:
        f.write("Этот файл открыт в другом процессе.")

def process_files(input_dir: Path, output_dir: Path):
    """Обрабатывает файлы, решая проблемы дубликатов, размера и блокировок."""
    output_dir.mkdir(parents=True, exist_ok=True)
    files = list(input_dir.iterdir())
    
    success_count = 0
    error_count = 0
    
    for file_path in files:
        if not file_path.is_file():
            continue
            
        try:
            # Решение проблемы дубликатов: добавление уникального timestamp
            timestamp = int(time.time() * 1000)
            new_name = f"processed_{timestamp}_{file_path.name}"
            dest_path = output_dir / new_name
            
            # Решение проблемы больших файлов: shutil.move на одном диске 
            # является атомарной операцией переименования, не загружает RAM
            shutil.move(str(file_path), str(dest_path))
            success_count += 1
            
        except PermissionError:
            # Решение проблемы блокировки: программа не падает, а пропускает файл
            logging.warning(f"SKIPPED (file locked): {file_path.name}")
            error_count += 1
        except Exception as e:
            logging.error(f"ERROR {file_path.name}: {e}")
            error_count += 1
            
    logging.info(f"FINISHED. Success: {success_count}, Errors/Skipped: {error_count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Resilient file processor")
    parser.add_argument("--generate", action="store_true", help="Generate test files")
    parser.add_argument("--process", action="store_true", help="Process files")
    args = parser.parse_args()

    INPUT_DIR = Path("input_orders")
    OUTPUT_DIR = Path("output_processed")

    if args.generate:
        generate_test_data(INPUT_DIR, 550)
    elif args.process:
        process_files(INPUT_DIR, OUTPUT_DIR)
    else:
        print("Usage: python processor.py --generate OR python processor.py --process")