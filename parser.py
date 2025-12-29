"""
Парсер для проверки лизинга с 0% на сайтах продажи электроники в Эстонии
"""
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LeasingParser:
    """Базовый класс для парсинга сайтов на наличие лизинга с 0%"""
    
    def __init__(self, site_name: str, base_url: str):
        self.site_name = site_name
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def parse(self) -> List[Dict]:
        """Основной метод парсинга. Возвращает список товаров с лизингом 0%"""
        raise NotImplementedError("Метод parse должен быть реализован в подклассе")
    
    def search_leasing_keywords(self, text: str) -> bool:
        """Проверяет наличие ключевых слов о лизинге с 0%"""
        text_lower = text.lower()
        
        # Ищем упоминание лизинга
        has_leasing = any(keyword in text_lower for keyword in ['leasing', 'liising'])
        
        # Ищем 0% процент
        has_zero_percent = any([
            '0%' in text,
            '0 protsenti' in text_lower,
            'null protsenti' in text_lower,
            re.search(r'\b0\s*%', text),
            re.search(r'null\s*%', text_lower)
        ])
        
        return has_leasing and has_zero_percent
    
    def extract_leasing_period(self, text: str) -> Optional[str]:
        """Извлекает срок лизинга из текста. Особое внимание к 48 месяцам."""
        text_lower = text.lower()
        
        # Паттерны для поиска срока лизинга
        patterns = [
            # 48 месяцев (приоритет)
            (r'48\s*(месяц|kuud?|мес|месяцев|kuud)', '48 месяцев'),
            (r'48\s*(мес\.|kuud\.)', '48 месяцев'),
            # Другие сроки
            (r'(\d+)\s*(месяц|kuud?|мес|месяцев|kuud)', None),  # Любое количество месяцев
            (r'(\d+)\s*(мес\.|kuud\.)', None),
        ]
        
        # Сначала проверяем на 48 месяцев (приоритет)
        for pattern, period in patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                if period:
                    return period
                else:
                    # Извлекаем число из паттерна
                    numbers = re.findall(r'\d+', match.group(0))
                    if numbers:
                        months = numbers[0]
                        return f"{months} месяцев"
        
        return None
    
    def get_page(self, url: str) -> Optional[BeautifulSoup]:
        """Получает и парсит страницу"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            # Используем html.parser вместо lxml (не требует компиляции)
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            logger.error(f"Ошибка при получении страницы {url}: {e}")
            return None


class RDEParser(LeasingParser):
    """Парсер для rde.ee"""
    
    def __init__(self):
        super().__init__("RDE", "https://www.rde.ee")
    
    def parse(self) -> List[Dict]:
        """Парсит rde.ee на наличие лизинга с 0%"""
        results = []
        
        # Парсим главную страницу
        url = f"{self.base_url}/"
        soup = self.get_page(url)
        
        if not soup:
            logger.warning(f"Не удалось загрузить главную страницу {self.base_url}")
            return results
        
        # Ищем все ссылки на странице, которые могут вести к товарам
        all_links = soup.find_all('a', href=True)
        product_links = []
        
        for link in all_links:
            href = link.get('href', '')
            link_text = link.get_text(strip=True).lower()
            
            # Ищем ссылки, которые могут быть товарами
            if any(keyword in link_text for keyword in ['leasing', 'liising', '0%', '0 protsenti']):
                if href.startswith('/') or self.base_url in href:
                    if not href.startswith('http'):
                        href = self.base_url + href
                    product_links.append((href, link_text))
        
        # Также ищем упоминания лизинга в тексте страницы
        page_text = soup.get_text()
        if self.search_leasing_keywords(page_text):
            # Ищем ближайшие ссылки к тексту о лизинге
            leasing_elements = soup.find_all(string=re.compile(r'leasing|liising|0\s*%', re.I))
            
            for elem in leasing_elements:
                # Ищем родительский элемент с ссылкой
                parent = elem.find_parent(['div', 'article', 'section', 'li'])
                if parent:
                    link_elem = parent.find('a', href=True)
                    if link_elem:
                        href = link_elem.get('href', '').strip()
                        
                        # Пропускаем невалидные ссылки
                        if not href or href == '#' or href.startswith('javascript:') or href.startswith('mailto:'):
                            continue
                        
                        # Нормализуем URL
                        if href.startswith('/'):
                            href = self.base_url + href
                        elif not href.startswith('http'):
                            href = self.base_url + '/' + href.lstrip('/')
                        
                        # Извлекаем информацию о товаре
                        title_elem = parent.find(['h1', 'h2', 'h3', 'h4', 'a'])
                        title = title_elem.get_text(strip=True) if title_elem else "Товар с лизингом 0%"
                        
                        # Если название слишком короткое, берем текст ссылки
                        if len(title) < 10:
                            title = link_elem.get_text(strip=True) or title
                        
                        price_elem = parent.find(['span', 'div'], class_=re.compile(r'price|hind', re.I))
                        price = price_elem.get_text(strip=True) if price_elem else "Цена не указана"
                        
                        # Извлекаем срок лизинга
                        parent_text = parent.get_text()
                        leasing_period = self.extract_leasing_period(parent_text)
                        
                        # Проверяем, что это новый товар
                        if not any(r['url'] == href for r in results):
                            results.append({
                                'site': self.site_name,
                                'title': title[:500],  # Ограничиваем длину
                                'price': price,
                                'url': href,
                                'category': '/',
                                'leasing_period': leasing_period,
                                'found_at': datetime.now().isoformat()
                            })
        
        logger.info(f"RDE: найдено {len(results)} товаров с лизингом 0%")
        return results


class KlickParser(LeasingParser):
    """Парсер для klick.ee"""
    
    def __init__(self):
        super().__init__("Klick", "https://www.klick.ee")
    
    def parse(self) -> List[Dict]:
        """Парсит klick.ee на наличие лизинга с 0%"""
        results = []
        
        # Парсим главную страницу
        url = f"{self.base_url}/"
        soup = self.get_page(url)
        
        if not soup:
            logger.warning(f"Не удалось загрузить главную страницу {self.base_url}")
            return results
        
        # Ищем упоминания лизинга в тексте страницы
        page_text = soup.get_text()
        if self.search_leasing_keywords(page_text):
            # Ищем элементы с упоминанием лизинга
            leasing_elements = soup.find_all(string=re.compile(r'leasing|liising|0\s*%', re.I))
            
            for elem in leasing_elements:
                parent = elem.find_parent(['div', 'article', 'section', 'li', 'a'])
                if parent:
                    link_elem = parent.find('a', href=True) if parent.name != 'a' else parent
                    if link_elem and link_elem.get('href'):
                        href = link_elem.get('href', '').strip()
                        
                        # Пропускаем невалидные ссылки
                        if not href or href == '#' or href.startswith('javascript:') or href.startswith('mailto:'):
                            continue
                        
                        # Нормализуем URL
                        if href.startswith('/'):
                            href = self.base_url + href
                        elif not href.startswith('http'):
                            href = self.base_url + '/' + href.lstrip('/')
                        
                        title_elem = parent.find(['h1', 'h2', 'h3', 'h4']) or link_elem
                        title = title_elem.get_text(strip=True) if title_elem else "Товар с лизингом 0%"
                        
                        if len(title) < 10:
                            title = link_elem.get_text(strip=True) or title
                        
                        price_elem = parent.find(['span', 'div'], class_=re.compile(r'price|hind', re.I))
                        price = price_elem.get_text(strip=True) if price_elem else "Цена не указана"
                        
                        parent_text = parent.get_text()
                        leasing_period = self.extract_leasing_period(parent_text)
                        
                        if not any(r['url'] == href for r in results):
                            results.append({
                                'site': self.site_name,
                                'title': title[:500],
                                'price': price,
                                'url': href,
                                'category': '/',
                                'leasing_period': leasing_period,
                                'found_at': datetime.now().isoformat()
                            })
        
        logger.info(f"Klick: найдено {len(results)} товаров с лизингом 0%")
        return results


class ArvutitarkParser(LeasingParser):
    """Парсер для arvutitark.ee"""
    
    def __init__(self):
        super().__init__("Arvutitark", "https://www.arvutitark.ee")
    
    def parse(self) -> List[Dict]:
        """Парсит arvutitark.ee на наличие лизинга с 0%"""
        results = []
        
        # Парсим главную страницу
        url = f"{self.base_url}/"
        soup = self.get_page(url)
        
        if not soup:
            logger.warning(f"Не удалось загрузить главную страницу {self.base_url}")
            return results
        
        # Ищем упоминания лизинга в тексте страницы
        page_text = soup.get_text()
        if self.search_leasing_keywords(page_text):
            # Ищем элементы с упоминанием лизинга
            leasing_elements = soup.find_all(string=re.compile(r'leasing|liising|0\s*%', re.I))
            
            for elem in leasing_elements:
                parent = elem.find_parent(['div', 'article', 'section', 'li', 'a'])
                if parent:
                    link_elem = parent.find('a', href=True) if parent.name != 'a' else parent
                    if link_elem and link_elem.get('href'):
                        href = link_elem.get('href', '').strip()
                        
                        # Пропускаем невалидные ссылки
                        if not href or href == '#' or href.startswith('javascript:') or href.startswith('mailto:'):
                            continue
                        
                        # Нормализуем URL
                        if href.startswith('/'):
                            href = self.base_url + href
                        elif not href.startswith('http'):
                            href = self.base_url + '/' + href.lstrip('/')
                        
                        title_elem = parent.find(['h1', 'h2', 'h3', 'h4']) or link_elem
                        title = title_elem.get_text(strip=True) if title_elem else "Товар с лизингом 0%"
                        
                        if len(title) < 10:
                            title = link_elem.get_text(strip=True) or title
                        
                        price_elem = parent.find(['span', 'div'], class_=re.compile(r'price|hind', re.I))
                        price = price_elem.get_text(strip=True) if price_elem else "Цена не указана"
                        
                        parent_text = parent.get_text()
                        leasing_period = self.extract_leasing_period(parent_text)
                        
                        if not any(r['url'] == href for r in results):
                            results.append({
                                'site': self.site_name,
                                'title': title[:500],
                                'price': price,
                                'url': href,
                                'category': '/',
                                'leasing_period': leasing_period,
                                'found_at': datetime.now().isoformat()
                            })
        
        logger.info(f"Arvutitark: найдено {len(results)} товаров с лизингом 0%")
        return results


def run_all_parsers() -> List[Dict]:
    """Запускает все парсеры и возвращает объединенные результаты"""
    parsers = [
        RDEParser(),
        KlickParser(),
        ArvutitarkParser()
    ]
    
    all_results = []
    for parser in parsers:
        try:
            results = parser.parse()
            all_results.extend(results)
        except Exception as e:
            logger.error(f"Ошибка при парсинге {parser.site_name}: {e}")
    
    return all_results


if __name__ == "__main__":
    # Тестирование парсеров
    results = run_all_parsers()
    print(f"Всего найдено товаров: {len(results)}")
    for result in results:
        print(f"{result['site']}: {result['title']} - {result['url']}")

