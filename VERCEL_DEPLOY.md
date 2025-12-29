# Инструкция по деплою на Vercel

## Решение ошибки 500: INTERNAL_SERVER_ERROR

Если вы видите ошибку 500 на Vercel, выполните следующие шаги:

### 1. Проверьте структуру проекта

Убедитесь, что у вас есть:
- `api/index.py` - serverless функция
- `api/requirements.txt` - зависимости для Vercel
- `vercel.json` - конфигурация Vercel
- `templates/index.html` - HTML шаблон

### 2. Проверьте логи в Vercel Dashboard

1. Перейдите в ваш проект на Vercel
2. Откройте вкладку "Functions"
3. Посмотрите логи последних вызовов
4. Найдите конкретную ошибку

### 3. Частые проблемы и решения

#### Проблема: Импорт модулей не работает
**Решение:** Убедитесь, что все файлы (parser.py, database.py) находятся в корне проекта, а не в папке api/

#### Проблема: База данных не работает
**Решение:** SQLite на Vercel работает только в `/tmp`. Если проблема сохраняется, рассмотрите использование внешней БД:
- Vercel Postgres
- MongoDB Atlas
- Supabase

#### Проблема: Шаблоны не найдены
**Решение:** Проверьте, что папка `templates/` находится в корне проекта

### 4. Передеплой проекта

```bash
# Удалите старый деплой
vercel remove

# Задеплойте заново
vercel --prod
```

### 5. Проверка локально

Перед деплоем проверьте локально:
```bash
vercel dev
```

Откройте http://localhost:3000 и проверьте, что все работает.

### 6. Настройка Cron Jobs

После успешного деплоя:
1. Перейдите в Vercel Dashboard → Settings → Cron Jobs
2. Добавьте новую задачу:
   - Path: `/api/cron`
   - Schedule: `0 9,21 * * *` (9:00 и 21:00 каждый день)

### 7. Переменные окружения (опционально)

Если хотите защитить cron endpoint:
1. Перейдите в Settings → Environment Variables
2. Добавьте `CRON_SECRET` с любым секретным значением
3. Vercel автоматически передаст его в заголовке Authorization

## Альтернативное решение: Использование внешней БД

Для продакшена рекомендуется использовать внешнюю БД вместо SQLite:

### Вариант 1: Vercel Postgres
```bash
vercel postgres create
```

### Вариант 2: MongoDB Atlas
1. Создайте бесплатный кластер на mongodb.com
2. Получите connection string
3. Добавьте в Environment Variables как `MONGODB_URI`

### Вариант 3: Supabase
1. Создайте проект на supabase.com
2. Получите connection string
3. Используйте PostgreSQL вместо SQLite

## Проверка работоспособности

После деплоя проверьте:
- ✅ Главная страница открывается: `https://your-project.vercel.app/`
- ✅ API работает: `https://your-project.vercel.app/api/products`
- ✅ Парсинг запускается: `POST https://your-project.vercel.app/api/refresh`

