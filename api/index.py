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
# На Vercel файлы находятся в /var/task, но структура может отличаться
try:
    # Текущая директория файла (api/)
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    # Родительская директория (корень проекта)
    project_root = os.path.dirname(current_file_dir)
    
    # Проверяем разные возможные пути
    possible_roots = [
        '/var/task',  # Vercel production
        project_root,  # Локальная разработка
        os.getcwd(),  # Текущая рабочая директория
    ]
    
    root_dir = None
    for possible_root in possible_roots:
        # Проверяем наличие ключевых файлов
        if os.path.exists(possible_root) and (
            os.path.exists(os.path.join(possible_root, 'parser.py')) or
            os.path.exists(os.path.join(possible_root, 'database.py'))
        ):
            root_dir = possible_root
            break
    
    # Если не нашли, используем родительскую директорию
    if not root_dir:
        root_dir = project_root
    
    # Добавляем все возможные пути в sys.path
    for path in possible_roots + [root_dir]:
        if path and os.path.exists(path) and path not in sys.path:
            sys.path.insert(0, path)
    
    # Ищем шаблоны в разных местах
    template_dirs = [
        os.path.join(root_dir, 'templates'),
        os.path.join(project_root, 'templates'),
        os.path.join('/var/task', 'templates'),
        'templates',
    ]
    
    template_dir = None
    for td in template_dirs:
        if os.path.exists(td):
            template_dir = td
            break
    
    if not template_dir:
        template_dir = os.path.join(root_dir, 'templates')
    
    logger.info(f"Root dir: {root_dir}")
    logger.info(f"Template dir: {template_dir}")
    logger.info(f"Template exists: {os.path.exists(template_dir)}")
    logger.info(f"Current dir: {os.getcwd()}")
    logger.info(f"Files in root: {os.listdir(root_dir)[:10] if os.path.exists(root_dir) else 'N/A'}")
    
except Exception as e:
    logger.error(f"Ошибка при настройке путей: {e}")
    logger.error(traceback.format_exc())
    # Продолжаем с дефолтными значениями
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_dir = os.path.join(root_dir, 'templates')

# Импорт модулей с обработкой ошибок
try:
    from flask import Flask, render_template, jsonify, request
    logger.info("Flask импортирован успешно")
except ImportError as e:
    logger.error(f"Ошибка импорта Flask: {e}")
    logger.error(traceback.format_exc())
    raise

# Импортируем модули проекта
Database = None
run_all_parsers = None

try:
    from database import Database
    logger.info("Database импортирован успешно")
except ImportError as e:
    logger.error(f"Ошибка импорта Database: {e}")
    logger.error(f"sys.path: {sys.path}")
    logger.error(f"Проверяемые пути: {[p for p in sys.path[:5] if os.path.exists(p)]}")
    logger.error(traceback.format_exc())
    # Создаем заглушку для диагностики
    class DatabaseStub:
        def __init__(self, *args, **kwargs):
            raise ImportError(f"Database module not found. sys.path: {sys.path[:5]}")
    Database = DatabaseStub

try:
    from parser import run_all_parsers
    logger.info("Parser импортирован успешно")
except ImportError as e:
    logger.error(f"Ошибка импорта Parser: {e}")
    logger.error(f"sys.path: {sys.path}")
    logger.error(traceback.format_exc())
    def run_all_parsers_stub():
        raise ImportError(f"Parser module not found. sys.path: {sys.path[:5]}")
    run_all_parsers = run_all_parsers_stub

# Настройка Flask приложения
try:
    # Если шаблоны не найдены, используем относительный путь
    if not os.path.exists(template_dir):
        logger.warning(f"Template dir не найден: {template_dir}, пробуем относительный путь")
        template_dir = 'templates'
    
    app = Flask(__name__, template_folder=template_dir)
    logger.info(f"Flask app создан. Template dir: {template_dir}")
    logger.info(f"Template dir существует: {os.path.exists(template_dir)}")
    
    # Проверяем наличие модулей
    if Database is None or run_all_parsers is None:
        logger.warning("Некоторые модули не загружены! Приложение может работать некорректно.")
        
except Exception as e:
    logger.error(f"Ошибка при создании Flask app: {e}")
    logger.error(traceback.format_exc())
    # Создаем минимальное приложение для диагностики
    app = Flask(__name__)

# Простой тестовый endpoint для проверки работоспособности
@app.route('/test', methods=['GET'])
def test():
    """Простой тест для проверки работоспособности"""
    try:
        files_in_root = []
        if os.path.exists(root_dir):
            try:
                files_in_root = [f for f in os.listdir(root_dir) if f.endswith('.py')][:5]
            except:
                pass
        
        return jsonify({
            'status': 'ok',
            'message': 'Serverless function работает!',
            'root_dir': root_dir,
            'template_dir': template_dir,
            'template_exists': os.path.exists(template_dir),
            'files_in_root': files_in_root,
            'sys_path': sys.path[:5],
            'cwd': os.getcwd(),
            'modules_loaded': {
                'Database': Database is not None,
                'run_all_parsers': run_all_parsers is not None
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

# Инициализация БД с путем для Vercel
def get_db():
    """Получает экземпляр базы данных"""
    if Database is None:
        raise ImportError("Database module not imported. Check logs for details.")
    
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
        # Проверяем, что модули загружены
        if Database is None:
            return jsonify({
                'error': 'Database module not loaded',
                'message': 'Проверьте логи сервера. Убедитесь, что database.py находится в корне проекта.',
                'sys_path': sys.path[:5],
                'root_dir': root_dir
            }), 500
        
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
        
        # Проверяем наличие шаблона
        template_path = os.path.join(template_dir, 'index.html')
        if not os.path.exists(template_path):
            logger.warning(f"Template not found: {template_path}")
            # Возвращаем JSON вместо HTML если шаблон не найден
            return jsonify({
                'error': 'Template not found',
                'template_path': template_path,
                'products_by_site': products_by_site,
                'total_count': len(products),
                'count_48_months': len(products_48_months)
            })
        
        return render_template('index.html', 
                             products_by_site=products_by_site,
                             products_48_by_site=products_48_by_site,
                             total_count=len(products),
                             count_48_months=len(products_48_months))
    except Exception as e:
        logger.error(f"Ошибка в index: {e}", exc_info=True)
        error_details = traceback.format_exc()
        logger.error(f"Traceback: {error_details}")
        return jsonify({
            'error': str(e), 
            'details': error_details,
            'root_dir': root_dir,
            'template_dir': template_dir,
            'sys_path': sys.path[:5]
        }), 500

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
        if run_all_parsers is None:
            return jsonify({
                'success': False,
                'error': 'Parser module not loaded. Check server logs.'
            }), 500
        
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
        logger.error(f"Ошибка при парсинге: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
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
            'sys_path': sys.path[:5],
            'cwd': os.getcwd(),
            'modules_loaded': {
                'Database': Database is not None,
                'run_all_parsers': run_all_parsers is not None
            }
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
        
        if run_all_parsers is None:
            logger.error("Parser module not loaded in cron job")
            return jsonify({
                'success': False,
                'error': 'Parser module not loaded'
            }), 500
        
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
        logger.error(f"Ошибка в cron job: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

# Vercel serverless handler
# Экспортируем app для Vercel
# Vercel автоматически использует переменную 'app' как WSGI приложение

