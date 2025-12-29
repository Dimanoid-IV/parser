"""
Модуль для работы с базой данных
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()


class LeasingProduct(Base):
    """Модель товара с лизингом 0%"""
    __tablename__ = 'leasing_products'
    
    id = Column(Integer, primary_key=True)
    site = Column(String(50), nullable=False)
    title = Column(String(500), nullable=False)
    price = Column(String(100))
    url = Column(Text, nullable=False)
    category = Column(String(200))
    leasing_period = Column(String(50))  # Срок лизинга (например, "48 месяцев")
    found_at = Column(DateTime, default=datetime.now)
    created_at = Column(DateTime, default=datetime.now)
    
    def to_dict(self):
        """Преобразует объект в словарь"""
        return {
            'id': self.id,
            'site': self.site,
            'title': self.title,
            'price': self.price,
            'url': self.url,
            'category': self.category,
            'leasing_period': self.leasing_period,
            'found_at': self.found_at.isoformat() if self.found_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Database:
    """Класс для работы с базой данных"""
    
    def __init__(self, db_path='leasing_products.db'):
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        
        # Обновляем схему базы данных (добавляем новые поля, если их нет)
        try:
            Base.metadata.create_all(self.engine)
            # Проверяем наличие поля leasing_period и добавляем его, если нужно
            from sqlalchemy import inspect, text
            inspector = inspect(self.engine)
            if inspector.has_table('leasing_products'):
                columns = [col['name'] for col in inspector.get_columns('leasing_products')]
                if 'leasing_period' not in columns:
                    with self.engine.connect() as conn:
                        conn.execute(text('ALTER TABLE leasing_products ADD COLUMN leasing_period VARCHAR(50)'))
                        conn.commit()
        except Exception as e:
            # Если таблицы нет, создаем её
            Base.metadata.create_all(self.engine)
        
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def add_products(self, products: list):
        """Добавляет товары в базу данных (избегая дубликатов)"""
        from dateutil import parser as date_parser
        
        added_count = 0
        for product_data in products:
            # Преобразуем found_at из строки в datetime, если нужно
            if 'found_at' in product_data and isinstance(product_data['found_at'], str):
                try:
                    product_data['found_at'] = date_parser.parse(product_data['found_at'])
                except:
                    product_data['found_at'] = datetime.now()
            
            # Проверяем, существует ли уже такой товар
            existing = self.session.query(LeasingProduct).filter_by(
                url=product_data['url'],
                title=product_data['title']
            ).first()
            
            if not existing:
                product = LeasingProduct(**product_data)
                self.session.add(product)
                added_count += 1
        
        self.session.commit()
        return added_count
    
    def get_all_products(self, limit=100):
        """Получает все товары из базы данных"""
        products = self.session.query(LeasingProduct).order_by(
            LeasingProduct.found_at.desc()
        ).limit(limit).all()
        return [p.to_dict() for p in products]
    
    def get_products_by_site(self, site: str):
        """Получает товары по сайту"""
        products = self.session.query(LeasingProduct).filter_by(
            site=site
        ).order_by(LeasingProduct.found_at.desc()).all()
        return [p.to_dict() for p in products]
    
    def get_recent_products(self, hours=24):
        """Получает товары, найденные за последние N часов"""
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(hours=hours)
        products = self.session.query(LeasingProduct).filter(
            LeasingProduct.found_at >= cutoff_time
        ).order_by(LeasingProduct.found_at.desc()).all()
        return [p.to_dict() for p in products]
    
    def get_products_48_months(self):
        """Получает товары с лизингом на 48 месяцев"""
        products = self.session.query(LeasingProduct).filter(
            LeasingProduct.leasing_period.contains('48')
        ).order_by(LeasingProduct.found_at.desc()).all()
        return [p.to_dict() for p in products]
    
    def close(self):
        """Закрывает сессию"""
        self.session.close()

