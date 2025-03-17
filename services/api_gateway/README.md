# API Gateway

API Gateway для системы ОРИОКС, обеспечивающий единую точку входа для всех микросервисов.

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

3. Создайте файл .env со следующими переменными:
```
AUTH_SERVICE_URL=http://localhost:8000
PERFORMANCE_SERVICE_URL=http://localhost:8001
CORS_ORIGINS=http://localhost:3000
```

## Запуск

```bash
uvicorn main:app --reload --port 8080
```

## API Endpoints

### Здоровье сервиса
- `GET /api/health` - Проверка состояния сервиса

### Аутентификация
- `POST /api/auth/token` - Получение JWT токена
- `POST /api/auth/register` - Регистрация нового пользователя

### Успеваемость
- `GET /api/performance/students/{student_id}` - Получение успеваемости студента
- `GET /api/performance/students/{student_id}/statistics` - Статистика успеваемости студента
- `GET /api/performance/courses` - Список всех курсов
- `GET /api/performance/grades` - Список оценок с возможностью фильтрации

## Параметры запросов

### GET /api/performance/students/{student_id}/statistics
- `semester` (опционально) - Номер семестра
- `year` (опционально) - Год

### GET /api/performance/grades
- `student_id` (опционально) - ID студента
- `course_id` (опционально) - ID курса
- `grade_type` (опционально) - Тип оценки (HW, TEST, EXAM, PROJECT)

## Аутентификация

Все запросы (кроме /api/health, /api/auth/token и /api/auth/register) требуют JWT токен в заголовке:
```
Authorization: Bearer <token>
``` 