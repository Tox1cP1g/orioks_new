# Auth Service

Сервис аутентификации для системы ОРИОКС

## Установка

1. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
# или
venv\Scripts\activate  # для Windows
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл .env на основе .env.example и настройте переменные окружения

4. Примените миграции:
```bash
python manage.py migrate
```

5. Создайте суперпользователя:
```bash
python manage.py createsuperuser
```

## Запуск

```bash
python manage.py runserver
```

## API Endpoints

- `POST /api/token/` - Получение JWT токена
- `POST /api/token/refresh/` - Обновление JWT токена
- `POST /api/register/` - Регистрация нового пользователя
- `GET /api/user/` - Получение данных текущего пользователя
- `PUT /api/user/` - Обновление данных пользователя
- `GET /api/user/info/` - Получение информации о пользователе 