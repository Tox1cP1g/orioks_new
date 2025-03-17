*** ЭТО ЛАБОРАТОРНАЯ ПО КПО – НЕ ТРОГАТЬ ***

# ОРИОКС Микросервисы

Микросервисная архитектура системы ОРИОКС для управления успеваемостью студентов.

## Структура проекта

```
services/
├── auth/                 # Сервис аутентификации
├── student_performance/  # Сервис успеваемости студентов
└── api_gateway/         # API Gateway
```

## Сервисы

### Auth Service (Порт: 8000)
- Управление пользователями
- Аутентификация и авторизация
- JWT токены

### Student Performance Service (Порт: 8001)
- Управление курсами
- Оценки студентов
- Статистика успеваемости
- Отчеты по семестрам

### API Gateway (Порт: 8080)
- Единая точка входа
- Маршрутизация запросов
- Проверка токенов
- CORS

## Установка и запуск

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd orioks-microservices
```

2. Создайте и активируйте виртуальные окружения для каждого сервиса:
```bash
# Auth Service
cd services/auth
python -m venv venv
source venv/bin/activate  # для Linux/Mac
# или
venv\Scripts\activate  # для Windows
pip install -r requirements.txt
cd ../..

# Student Performance Service
cd services/student_performance
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ../..

# API Gateway
cd services/api_gateway
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ../..
```

3. Настройте переменные окружения:
- Скопируйте `.env.example` в `.env` в каждом сервисе
- Настройте необходимые параметры в файлах `.env`

4. Запустите сервисы:
```bash
# В разных терминалах:

# Auth Service
cd services/auth
python manage.py migrate
python manage.py runserver 8000

# Student Performance Service
cd services/student_performance
python manage.py migrate
python manage.py runserver 8001

# API Gateway
cd services/api_gateway
uvicorn main:app --reload --port 8080
```

## API Documentation

- Auth Service: http://localhost:8000/api/docs/
- Student Performance Service: http://localhost:8001/api/docs/
- API Gateway: http://localhost:8080/docs

## Разработка

### Добавление нового сервиса

1. Создайте новую директорию в `services/`
2. Создайте виртуальное окружение и установите зависимости
3. Реализуйте API сервиса
4. Добавьте маршруты в API Gateway
5. Обновите документацию

### Тестирование

Каждый сервис содержит свои модульные тесты. Для запуска:

```bash
# В директории сервиса:
python manage.py test  # для Django сервисов
# или
pytest  # для FastAPI сервисов
```

## Безопасность

- Все запросы между сервисами используют JWT токены
- API Gateway проверяет токены для всех защищенных эндпоинтов
- Используется HTTPS в продакшене
- Применяются best practices безопасности Django и FastAPI
