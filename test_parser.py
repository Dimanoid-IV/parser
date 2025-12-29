"""
Тестовый скрипт для проверки парсера и базы данных
"""
import sys
import io

# Настройка кодировки для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from parser import run_all_parsers
from database import Database
import logging

logging.basicConfig(level=logging.INFO)

print("=" * 50)
print("Тестирование парсера")
print("=" * 50)

# Тест парсера
print("\n1. Запуск парсера...")
try:
    results = run_all_parsers()
    print(f"[OK] Найдено товаров: {len(results)}")
    
    if results:
        print("\nПервые 3 товара:")
        for i, product in enumerate(results[:3], 1):
            print(f"  {i}. {product['site']}: {product['title'][:60]}...")
            print(f"     URL: {product['url']}")
            print(f"     Лизинг: {product.get('leasing_period', 'Не указан')}")
    else:
        print("[WARNING] Товары не найдены")
        print("\nВозможные причины:")
        print("- Сайты изменили структуру HTML")
        print("- Нет товаров с лизингом 0% на страницах")
        print("- Проблемы с доступом к сайтам")
        print("- Неправильные URL категорий")
        
except Exception as e:
    print(f"[ERROR] Ошибка при парсинге: {e}")
    import traceback
    traceback.print_exc()

# Тест базы данных
print("\n" + "=" * 50)
print("Тестирование базы данных")
print("=" * 50)

try:
    db = Database()
    
    # Проверяем существующие данные
    products = db.get_all_products()
    print(f"\n2. Товаров в базе данных: {len(products)}")
    
    if products:
        print("\nПоследние 3 товара в БД:")
        for i, product in enumerate(products[:3], 1):
            print(f"  {i}. {product['site']}: {product['title'][:60]}...")
    else:
        print("[WARNING] База данных пуста")
    
    # Добавляем результаты парсинга
    if results:
        print(f"\n3. Добавление {len(results)} товаров в БД...")
        added = db.add_products(results)
        print(f"[OK] Добавлено новых товаров: {added}")
        
        # Проверяем снова
        products_after = db.get_all_products()
        print(f"[OK] Товаров в БД после добавления: {len(products_after)}")
        
        # Проверяем товары с 48 месяцами
        products_48 = db.get_products_48_months()
        print(f"[OK] Товаров с лизингом 48 месяцев: {len(products_48)}")
    
    db.close()
    
except Exception as e:
    print(f"[ERROR] Ошибка при работе с БД: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("Тест завершен")
print("=" * 50)
