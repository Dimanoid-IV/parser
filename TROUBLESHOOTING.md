# Устранение ошибки 500 на Vercel

## Шаг 1: Проверьте логи в Vercel Dashboard

Это самый важный шаг для диагностики проблемы!

1. Откройте https://vercel.com
2. Войдите в свой аккаунт
3. Выберите проект `parser`
4. Перейдите в **Deployments** (Деплои)
5. Выберите последний деплой (самый верхний)
6. Нажмите на деплой, чтобы открыть детали
7. Перейдите во вкладку **Functions** (Функции)
8. Найдите `api/index.py` или `/api/index`
9. Нажмите на него
10. Посмотрите **Logs** (Логи)

В логах вы увидите конкретную ошибку, например:
- `ModuleNotFoundError: No module named 'database'`
- `FileNotFoundError: [Errno 2] No such file or directory: '/var/task/templates/index.html'`
- Или другую ошибку

## Шаг 2: Проверьте тестовый endpoint

Откройте в браузере:
```
https://your-project.vercel.app/test
```

Если этот endpoint работает, значит Flask приложение запускается, и проблема в конкретных модулях.

Если не работает - проблема в базовой настройке.

## Шаг 3: Проверьте health endpoint

Откройте:
```
https://your-project.vercel.app/api/health
```

Этот endpoint покажет информацию о путях и поможет понять, что не так.

## Шаг 4: Частые ошибки и решения

### Ошибка: `ModuleNotFoundError: No module named 'database'`

**Причина:** Модули не найдены в пути импорта.

**Решение:**
1. Убедитесь, что файлы `database.py` и `parser.py` находятся в **корне проекта**, а не в папке `api/`
2. Структура должна быть:
   ```
   parser/
   ├── api/
   │   ├── index.py
   │   └── requirements.txt
   ├── database.py
   ├── parser.py
   ├── templates/
   │   └── index.html
   └── vercel.json
   ```

### Ошибка: `FileNotFoundError: templates/index.html`

**Причина:** Шаблоны не найдены.

**Решение:**
1. Убедитесь, что папка `templates/` находится в корне проекта
2. Убедитесь, что файл `templates/index.html` существует

### Ошибка: `ImportError` или другие ошибки импорта

**Решение:**
1. Проверьте, что все зависимости указаны в `api/requirements.txt`
2. Убедитесь, что версии пакетов совместимы
3. Попробуйте передеплоить проект

### Ошибка при работе с базой данных

**Решение:**
1. На Vercel SQLite работает только в `/tmp`
2. Код уже настроен на использование `/tmp/leasing_products.db`
3. Если проблема сохраняется, рассмотрите использование внешней БД

## Шаг 5: Передеплой проекта

После исправлений:

```bash
# Удалите старый деплой (опционально)
vercel remove

# Задеплойте заново
vercel --prod
```

## Шаг 6: Проверка локально

Перед деплоем проверьте локально:

```bash
# Установите Vercel CLI (если еще не установлен)
npm i -g vercel

# Запустите локальный сервер
vercel dev
```

Откройте http://localhost:3000 и проверьте:
- `/test` - должен вернуть JSON с информацией
- `/api/health` - должен показать пути
- `/` - главная страница

## Шаг 7: Если ничего не помогает

1. **Проверьте структуру проекта:**
   Убедитесь, что все файлы на месте:
   - `api/index.py`
   - `api/requirements.txt`
   - `database.py` (в корне)
   - `parser.py` (в корне)
   - `templates/index.html`
   - `vercel.json`

2. **Проверьте версии зависимостей:**
   Убедитесь, что версии в `api/requirements.txt` совместимы

3. **Создайте минимальный тест:**
   Попробуйте создать простой `api/test.py`:
   ```python
   from flask import Flask
   app = Flask(__name__)
   
   @app.route('/')
   def hello():
       return {'status': 'ok'}
   ```
   
   И проверьте, работает ли он.

4. **Обратитесь в поддержку Vercel:**
   Если проблема не решается, обратитесь в поддержку Vercel с логами ошибок.

## Полезные ссылки

- Vercel Python Runtime: https://vercel.com/docs/functions/runtimes/python
- Vercel Functions Logs: https://vercel.com/docs/observability/logs
- Flask на Vercel: https://vercel.com/guides/deploying-flask-with-vercel
