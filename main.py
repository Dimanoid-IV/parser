"""
Главный файл для запуска приложения с веб-сервером и планировщиком
"""
from app import app, db
from scheduler import run_scheduler_in_thread
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


if __name__ == '__main__':
    # Запускаем планировщик в отдельном потоке
    logger.info("Запуск планировщика парсинга...")
    scheduler_thread = run_scheduler_in_thread()
    
    # Запускаем веб-сервер
    logger.info("Запуск веб-сервера на http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

