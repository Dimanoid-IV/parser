"""
Веб-приложение Flask для отображения результатов парсинга
"""
from flask import Flask, render_template, jsonify
from database import Database
from parser import run_all_parsers
import logging

app = Flask(__name__)
db = Database()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route('/')
def index():
    """Главная страница с результатами парсинга"""
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
    
    return render_template('index.html', 
                         products_by_site=products_by_site,
                         products_48_by_site=products_48_by_site,
                         total_count=len(products),
                         count_48_months=len(products_48_months))


@app.route('/api/products')
def api_products():
    """API endpoint для получения всех товаров"""
    products = db.get_all_products(limit=200)
    return jsonify(products)


@app.route('/api/products/<site>')
def api_products_by_site(site):
    """API endpoint для получения товаров по сайту"""
    products = db.get_products_by_site(site)
    return jsonify(products)


@app.route('/api/recent')
def api_recent():
    """API endpoint для получения недавно найденных товаров"""
    products = db.get_recent_products(hours=24)
    return jsonify(products)


@app.route('/api/products/48months')
def api_products_48_months():
    """API endpoint для получения товаров с лизингом на 48 месяцев"""
    products = db.get_products_48_months()
    return jsonify(products)


@app.route('/api/refresh', methods=['POST'])
def api_refresh():
    """API endpoint для ручного запуска парсинга"""
    try:
        results = run_all_parsers()
        added = db.add_products(results)
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

