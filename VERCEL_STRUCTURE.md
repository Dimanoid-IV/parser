# Структура проекта для Vercel

## Правильная структура файлов

Для работы на Vercel файлы должны быть расположены следующим образом:

```
parser/
├── api/
│   ├── index.py          ← Serverless функция (главный файл)
│   └── requirements.txt  ← Зависимости для Vercel
├── database.py           ← В КОРНЕ проекта (не в api/)
├── parser.py             ← В КОРНЕ проекта (не в api/)
├── templates/
│   └── index.html        ← В КОРНЕ проекта (не в api/)
├── vercel.json           ← Конфигурация Vercel
└── .vercelignore         ← Файлы для исключения
```

## Критически важно:

1. **`database.py` и `parser.py` ДОЛЖНЫ быть в корне проекта**, не в папке `api/`
2. **`templates/` ДОЛЖНА быть в корне проекта**, не в папке `api/`
3. Только `api/index.py` и `api/requirements.txt` находятся в папке `api/`

## Проверка структуры перед деплоем

Перед деплоем на Vercel убедитесь:

```bash
# Проверьте структуру
ls -la
# Должны увидеть: database.py, parser.py, templates/, api/

ls api/
# Должны увидеть: index.py, requirements.txt

ls templates/
# Должны увидеть: index.html
```

## Диагностика на Vercel

После деплоя проверьте:

1. **Тестовый endpoint:**
   ```
   https://your-project.vercel.app/test
   ```
   Должен показать информацию о путях и загруженных модулях.

2. **Health endpoint:**
   ```
   https://your-project.vercel.app/api/health
   ```
   Покажет детальную диагностическую информацию.

3. **Проверьте логи в Vercel Dashboard:**
   - Deployments → Functions → Logs
   - Найдите ошибки импорта или пути

## Если модули не загружаются

Если в логах видите `ModuleNotFoundError`:

1. Убедитесь, что файлы в правильных местах (см. структуру выше)
2. Проверьте, что файлы закоммичены в Git
3. Передеплойте проект:
   ```bash
   vercel --prod
   ```

## Если шаблоны не найдены

Если видите ошибку `Template not found`:

1. Убедитесь, что папка `templates/` в корне проекта
2. Убедитесь, что файл `templates/index.html` существует
3. Проверьте через `/test` endpoint, что `template_exists: true`
