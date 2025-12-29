"""
Модуль для планирования автоматического парсинга (2 раза в сутки)
"""
import schedule
import time
import threading
from parser import run_all_parsers
from database import Database
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_parsing_job():
    """Задача парсинга, которая выполняется по расписанию"""
    logger.info("Запуск запланированного парсинга...")
    db = Database()
    
    try:
        results = run_all_parsers()
        added = db.add_products(results)
        logger.info(f"Парсинг завершен. Найдено: {len(results)}, Добавлено новых: {added}")
    except Exception as e:
        logger.error(f"Ошибка при выполнении парсинга: {e}")
    finally:
        db.close()


def start_scheduler():
    """Запускает планировщик задач"""
    # Парсинг в 9:00 и 21:00 каждый день
    schedule.every().day.at("09:00").do(run_parsing_job)
    schedule.every().day.at("21:00").do(run_parsing_job)
    
    logger.info("Планировщик запущен. Парсинг будет выполняться в 09:00 и 21:00 каждый день")
    
    # Запускаем сразу один раз для теста
    logger.info("Запуск начального парсинга...")
    run_parsing_job()
    
    # Бесконечный цикл для выполнения запланированных задач
    while True:
        schedule.run_pending()
        time.sleep(60)  # Проверяем каждую минуту


def run_scheduler_in_thread():
    """Запускает планировщик в отдельном потоке"""
    scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
    scheduler_thread.start()
    return scheduler_thread


if __name__ == "__main__":
    # Запуск планировщика напрямую
    start_scheduler()

