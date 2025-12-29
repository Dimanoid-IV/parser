"""
Vercel serverless function для парсера лизинга
"""
import sys
import os
import traceback

# Настройка логирования в самом начале
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Определяем корневую директорию проекта
# На Vercel это будет /var/task, локально - родительская директория api/
try:
    if os.path.exists('/var/task'):
        # Vercel production
        root_dir = '/var/task'
    else:
        # Локальная разработка или другая среда
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    template_dir = os.path.join(root_dir, 'templates')
    
    # Добавляем корневую директорию в путь для импорта модулей
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
    
    logger.info(f"Root dir: {root_dir}")
    logger.info(f"Template dir: {template_dir}")
    logger.info(f"Template exists: {os.path.exists(template_dir)}")
    logger.info(f"Current dir: {os.getcwd()}")
    logger.info(f"Python path: {sys.path[:3]}")
    
except Exception as e:
    logger.error(f"Ошибка при настройке путей: {e}")
    logger.error(traceback.format_exc())
    raise

# Импорт модулей с обработкой ошибок
try:
    from flask import Flask, render_template, jsonify, request
    logger.info("Flask импортирован успешно")
except ImportError as e:
    logger.error(f"Ошибка импорта Flask: {e}")
    logger.error(traceback.format_exc())
    raise

try:
    from database import Database
    logger.info("Database импортирован успешно")
except ImportError as e:
    logger.error(f"Ошибка импорта Database: {e}")
    logger.error(f"sys.path: {sys.path}")
    logger.error(traceback.format_exc())
    raise

try:
    from parser import run_all_parsers
    logger.info("Parser импортирован успешно")
except ImportError as e:
    logger.error(f"Ошибка импорта Parser: {e}")
    logger.error(f"sys.path: {sys.path}")
    logger.error(traceback.format_exc())
    raise

# Настройка Flask приложения
try:
    app = Flask(__name__, template_folder=template_dir)
    logger.info(f"Flask app создан. Template dir: {template_dir}")
    logger.info(f"Template dir существует: {os.path.exists(template_dir)}")
except Exception as e:
    logger.error(f"Ошибка при создании Flask app: {e}")
    logger.error(traceback.format_exc())
    raise

# Простой тестовый endpoint для проверки работоспособности
@app.route('/test', methods=['GET'])
def test():
    """Простой тест для проверки работоспособности"""
    return jsonify({
        'status': 'ok',
        'message': 'Serverless function работает!',
        'root_dir': root_dir,
        'template_dir': template_dir
    })

# Инициализация БД с путем для Vercel
def get_db():
    """Получает экземпляр базы данных"""
    # На Vercel используем /tmp для записи файлов БД
    # /tmp доступен для записи в serverless функциях
    db_path = os.path.join('/tmp', 'leasing_products.db')
    try:
        return Database(db_path=db_path)
    except Exception as e:
        logger.error(f"Ошибка при создании БД: {e}", exc_info=True)
        raise

@app.route('/', methods=['GET'])
def index():
    """Главная страница с результатами парсинга"""
    try:
        db = get_db()
        products = db.get_all_products(limit=200)
        products_48_months = db.get_products_48_months()
        
        # Группируем по сайтам
        products_by_site = {}
        for product in products:
            site = product['site']
            if site not in products_by_site:
                products_by_site[site] = []
            products_by_site[site].append(product)
        
        # Группируем товары с 48 месяцами по сайтам
        products_48_by_site = {}
        for product in products_48_months:
            site = product['site']
            if site not in products_48_by_site:
                products_48_by_site[site] = []
            products_48_by_site[site].append(product)
        
        db.close()
        return render_template('index.html', 
                             products_by_site=products_by_site,
                             products_48_by_site=products_48_by_site,
                             total_count=len(products),
                             count_48_months=len(products_48_months))
    except Exception as e:
        logger.error(f"Ошибка в index: {e}", exc_info=True)
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Traceback: {error_details}")
        return jsonify({'error': str(e), 'details': error_details}), 500

@app.route('/api/products', methods=['GET'])
def api_products():
    """API endpoint для получения всех товаров"""
    try:
        db = get_db()
        products = db.get_all_products(limit=200)
        db.close()
        return jsonify(products)
    except Exception as e:
        logger.error(f"Ошибка в api_products: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<site>', methods=['GET'])
def api_products_by_site(site):
    """API endpoint для получения товаров по сайту"""
    try:
        db = get_db()
        products = db.get_products_by_site(site)
        db.close()
        return jsonify(products)
    except Exception as e:
        logger.error(f"Ошибка в api_products_by_site: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/recent', methods=['GET'])
def api_recent():
    """API endpoint для получения недавно найденных товаров"""
    try:
        db = get_db()
        products = db.get_recent_products(hours=24)
        db.close()
        return jsonify(products)
    except Exception as e:
        logger.error(f"Ошибка в api_recent: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/48months', methods=['GET'])
def api_products_48_months():
    """API endpoint для получения товаров с лизингом на 48 месяцев"""
    try:
        db = get_db()
        products = db.get_products_48_months()
        db.close()
        return jsonify(products)
    except Exception as e:
        logger.error(f"Ошибка в api_products_48_months: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/refresh', methods=['POST'])
def api_refresh():
    """API endpoint для ручного запуска парсинга"""
    try:
        db = get_db()
        results = run_all_parsers()
        added = db.add_products(results)
        db.close()
        return jsonify({
            'success': True,
            'found': len(results),
            'added': added,
            'message': f'Найдено {len(results)} товаров, добавлено {added} новых'
        })
    except Exception as e:
        logger.error(f"Ошибка при парсинге: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def api_health():
    """Health check endpoint для диагностики"""
    try:
        return jsonify({
            'status': 'ok',
            'root_dir': root_dir,
            'template_dir': template_dir,
            'template_exists': os.path.exists(template_dir),
            'sys_path': sys.path[:3],  # Первые 3 элемента
            'cwd': os.getcwd()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/cron', methods=['GET', 'POST'])
def api_cron():
    """Cron job для автоматического парсинга (2 раза в сутки)"""
    try:
        # Проверяем секретный ключ для безопасности
        auth_header = request.headers.get('Authorization', '')
        cron_secret = os.environ.get('CRON_SECRET', '')
        
        if cron_secret and auth_header != f'Bearer {cron_secret}':
            return jsonify({'error': 'Unauthorized'}), 401
        
        db = get_db()
        results = run_all_parsers()
        added = db.add_products(results)
        db.close()
        
        logger.info(f"Cron job выполнен. Найдено: {len(results)}, Добавлено: {added}")
        return jsonify({
            'success': True,
            'found': len(results),
            'added': added,
            'message': f'Найдено {len(results)} товаров, добавлено {added} новых'
        })
    except Exception as e:
        logger.error(f"Ошибка в cron job: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Vercel serverless handler
# Экспортируем app для Vercel
# Vercel автоматически использует переменную 'app' как WSGI приложение

