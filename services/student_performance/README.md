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

## Настройка фоновой синхронизации

Для настройки автоматической синхронизации данных о преподавателях между порталами:

1. Установите пакет django-background-tasks:

```bash
pip install django-background-tasks
```

2. Добавьте 'background_task' в INSTALLED_APPS в файле settings.py.

3. Примените миграции:

```bash
python manage.py migrate background_task
```

4. Запланируйте задачу синхронизации:

```bash
python sync_teachers.py --schedule
```

5. Запустите процессор фоновых задач в отдельном терминале или как демон:

```bash
python manage.py process_tasks
```

Для автоматического запуска при старте сервера, используйте скрипт:

```bash
./background_tasks.sh
```

## Проблемы и решения

Если вы столкнулись с ошибкой кодировки 'latin-1 codec can't encode characters', убедитесь, что:
- Заголовки не содержат кириллических символов
- Все строки корректно закодированы
- API-эндпоинты существуют и доступны 

## Синхронизация данных между порталами

### Синхронизация связей преподаватель-предмет

Система обеспечивает автоматическую синхронизацию связей преподавателей с предметами между порталом преподавателя и порталом студента.

1. Запуск синхронизации вручную:

```bash
python sync_teachers.py
```

2. Настройка автоматической синхронизации (каждые 3 часа):

```bash
python sync_teachers.py --schedule
```

### Принцип работы скрипта синхронизации

Скрипт `sync_teachers.py` выполняет следующие действия:

1. Устанавливает соединение с порталом преподавателя (по умолчанию http://localhost:8004/api/)
2. Вызывает специальный API-эндпоинт `subject-teachers/for-student-portal/` для получения данных о связях преподавателей с предметами в удобном формате
3. Обрабатывает полученные данные и обновляет соответствующие записи в базе данных портала студента
4. Ведет логирование действий в файл `sync_teachers.log`

Если соединение с порталом преподавателя недоступно, скрипт использует тестовые данные из функции `create_test_subject_teacher_relations()`.

### Конфигурация синхронизации

Настройки для синхронизации можно изменить в файле `sync_teachers.py`:

- `TEACHER_PORTAL_URL` - URL API портала преподавателя
- `API_USERNAME` и `API_PASSWORD` - учетные данные для аутентификации
- Параметр расписания в декораторе `@background(schedule=10800)` (значение в секундах)

### Использование с Django Background Tasks

Для использования фоновых задач необходимо:

1. Установить пакет django-background-tasks: `pip install django-background-tasks`
2. Добавить 'background_task' в INSTALLED_APPS в файле settings.py
3. Применить миграции: `python manage.py migrate background_task`
4. Запустить процессор фоновых задач: `python manage.py process_tasks`

### Запросы к API портала преподавателя

Для получения данных о связях преподаватель-предмет используется эндпоинт:
```
GET http://localhost:8004/api/subject-teachers/for-student-portal/
```

Данный эндпоинт доступен без аутентификации и возвращает структурированные данные в формате:
```json
[
  {
    "teacher": {
      "id": 1,
      "name": "Иванов Иван Иванович",
      "position": "Доцент",
      "department": "Кафедра ИУ",
      "academic_degree": "к.т.н.",
      "email": "ivanov@example.com"
    },
    "subject": {
      "id": 1,
      "name": "Алгоритмы и структуры данных",
      "semester": 3,
      "description": "Описание предмета"
    },
    "role": "LECTURER",
    "role_display": "Лектор",
    "is_main": true
  }
]
``` 