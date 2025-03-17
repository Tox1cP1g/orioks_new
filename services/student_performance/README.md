# Student Performance Service

Сервис для управления успеваемостью студентов в системе ОРИОКС

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

## Запуск

```bash
python manage.py runserver 8001
```

## API Endpoints

### Курсы
- `GET /api/courses/` - Список всех курсов
- `POST /api/courses/` - Создание нового курса
- `GET /api/courses/{id}/` - Детали курса
- `PUT /api/courses/{id}/` - Обновление курса
- `DELETE /api/courses/{id}/` - Удаление курса

### Студенты
- `GET /api/students/` - Список всех студентов
- `POST /api/students/` - Добавление нового студента
- `GET /api/students/{id}/` - Детали студента
- `PUT /api/students/{id}/` - Обновление данных студента
- `DELETE /api/students/{id}/` - Удаление студента
- `GET /api/students/{id}/performance/` - Успеваемость студента
- `GET /api/students/{id}/statistics/` - Статистика успеваемости

### Оценки
- `GET /api/grades/` - Список всех оценок
- `POST /api/grades/` - Добавление новой оценки
- `GET /api/grades/{id}/` - Детали оценки
- `PUT /api/grades/{id}/` - Обновление оценки
- `DELETE /api/grades/{id}/` - Удаление оценки

### Успеваемость
- `GET /api/performance/` - Список всех показателей успеваемости
- `POST /api/performance/` - Добавление показателя успеваемости
- `GET /api/performance/{id}/` - Детали показателя
- `PUT /api/performance/{id}/` - Обновление показателя
- `DELETE /api/performance/{id}/` - Удаление показателя
- `GET /api/performance/semester_summary/` - Сводка за семестр

## Параметры фильтрации

### Grades
- `student` - ID студента
- `course` - ID курса
- `type` - Тип оценки (HW, TEST, EXAM, PROJECT)

### Performance
- `semester` - Номер семестра
- `year` - Год
- `student` - ID студента 