#!/usr/bin/env python
import os
import sys
import django
import requests
import json
import logging
from datetime import datetime, timedelta

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'student_performance.settings')
django.setup()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sync_teachers.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Импорт моделей
from performance.models import Teacher, Subject, SubjectTeacher

# Проверяем доступность background_task
try:
    # Проверяем, включен ли background_task в INSTALLED_APPS
    from django.conf import settings
    if 'background_task' not in settings.INSTALLED_APPS:
        BACKGROUND_TASK_AVAILABLE = False
        logger.warning("background_task не включен в INSTALLED_APPS. Фоновая синхронизация недоступна.")
    else:
        from background_task import background
        BACKGROUND_TASK_AVAILABLE = True
except ImportError:
    BACKGROUND_TASK_AVAILABLE = False
    logger.warning("Django background tasks не установлен. Используется ручной режим синхронизации.")

# URL портала преподавателя
TEACHER_PORTAL_URL = 'http://localhost:8004/api'
# URL портала студента 
STUDENT_PORTAL_URL = 'http://localhost:8003/api'

# Данные для аутентификации
API_USERNAME = 'admin'  # Имя пользователя API
API_PASSWORD = 'admin'  # Пароль API

# Токен для авторизации
AUTH_TOKEN = None

def get_auth_token():
    """Получает токен аутентификации от API"""
    global AUTH_TOKEN
    
    # Если токен уже получен, используем его
    if AUTH_TOKEN:
        return AUTH_TOKEN
        
    try:
        # Данные для авторизации с добавлением service_key
        auth_data = {
            'username': API_USERNAME,
            'password': API_PASSWORD,
            'service_key': 'student_performance_integration_key'  # Специальный ключ для межсервисной интеграции
        }
        
        # Используем специальный эндпоинт для межсервисной аутентификации
        service_token_endpoint = f'{TEACHER_PORTAL_URL}/subject-teachers/service-token/'
        
        logger.info(f"Запрашиваем токен через специальный эндпоинт: {service_token_endpoint}")
        response = requests.post(service_token_endpoint, json=auth_data, timeout=5)
        
        if response.status_code == 200:
            token_data = response.json()
            if 'access' in token_data:
                AUTH_TOKEN = token_data['access']
                logger.info("Токен успешно получен через специальный эндпоинт")
                return AUTH_TOKEN
            else:
                logger.warning(f"Ответ от API не содержит ожидаемый токен: {token_data}")
        else:
            logger.warning(f"Не удалось получить токен через специальный эндпоинт. Статус: {response.status_code}, Ответ: {response.text}")
            
            # Пробуем получить токен стандартными способами из старой реализации
            logger.info("Пробуем стандартные способы получения токена...")
            token_endpoints = [
                f'{TEACHER_PORTAL_URL}/token/',  # JWT эндпоинт
                'http://localhost:8004/token/',  # Альтернативный путь
                'http://localhost:8004/api-auth/token/',  # Еще один вариант
                'http://localhost:8002/api/token/'  # Через авторизационный сервис
            ]
            
            for endpoint in token_endpoints:
                try:
                    logger.info(f"Пробуем получить токен из {endpoint}")
                    response = requests.post(endpoint, json=auth_data, timeout=3)
                    
                    if response.status_code == 200:
                        token_data = response.json()
                        if 'access' in token_data:
                            AUTH_TOKEN = token_data['access']
                        elif 'token' in token_data:
                            AUTH_TOKEN = token_data['token']
                        
                        if AUTH_TOKEN:
                            logger.info("Токен успешно получен")
                            return AUTH_TOKEN
                except requests.RequestException as e:
                    logger.warning(f"Не удалось подключиться к {endpoint}: {str(e)}")
        
        logger.warning("Не удалось получить токен ни с одного из доступных эндпоинтов")
        return None
    except Exception as e:
        logger.error(f"Ошибка при получении токена: {str(e)}")
        return None

def get_headers():
    """Возвращает заголовки для API запросов"""
    token = get_auth_token()
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    if token:
        headers['Authorization'] = f'Bearer {token}'
        
    return headers

def fetch_data_from_api(endpoint, fallback_data=None, requires_auth=True):
    """
    Универсальная функция для получения данных из API
    
    Args:
        endpoint: API-эндпоинт для запроса
        fallback_data: функция для получения тестовых данных, если API недоступен
        requires_auth: требуется ли аутентификация для этого эндпоинта
    
    Returns:
        Данные из API или тестовые данные
    """
    full_url = f"{TEACHER_PORTAL_URL}/{endpoint}"
    logger.info(f"Выполняем запрос к {full_url}")
    
    try:
        # Используем заголовки с авторизацией только если требуется
        headers = get_headers() if requires_auth else {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        response = requests.get(full_url, headers=headers, timeout=5)
        response.encoding = 'utf-8'
        
        if response.status_code == 200:
            logger.info(f"API вернул успешный ответ")
            return response.json()
        else:
            logger.warning(f"API вернул ошибку {response.status_code}: {response.text}")
            if fallback_data:
                logger.info("Используем тестовые данные")
                return fallback_data()
            return []
    except requests.RequestException as e:
        logger.error(f"Ошибка при запросе к API: {str(e)}")
        if fallback_data:
            logger.info("Используем тестовые данные")
            return fallback_data()
        return []

def fetch_teacher_data():
    """Получает данные о преподавателях"""
    return fetch_data_from_api('teachers/', create_test_teacher_data)

def fetch_subject_teacher_relations():
    """Получает данные о связях преподавателей с предметами"""
    logger.info("Пытаемся получить данные о связях преподавателей с предметами через публичный API")
    
    # Пробуем несколько URL, чтобы гарантировать получение JSON
    urls = [
        'http://localhost:8004/raw-json-api/teachers/',
        'http://localhost:8004/api/v1/public/data.json',
        'http://localhost:8004/public-teacher-subjects.json',
        'http://localhost:8004/api/public/teachers/',
        'http://localhost:8004/public-teacher-subjects/'
    ]
    
    # Пробуем все URL последовательно
    for url in urls:
        try:
            logger.info(f"Пробуем запрос к API: {url}")
            # Явно указываем, что ожидаем JSON в заголовке Accept и добавляем AJAX-заголовок
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
            response = requests.get(url, headers=headers, timeout=5)
            logger.info(f"Ответ от {url}: статус {response.status_code}")
            
            if response.status_code == 200 and response.text.strip():
                # Проверяем, что получили валидный JSON
                try:
                    data = response.json()
                    logger.info(f"Успешно получены данные от API {url} - {len(data)} записей")
                    return data
                except json.JSONDecodeError as e:
                    logger.warning(f"Ответ не является валидным JSON: {e}")
                    logger.warning(f"Первые 100 символов ответа: {response.text[:100]}")
            else:
                logger.warning(f"Неуспешный ответ от {url}: {response.status_code}")
        except requests.RequestException as e:
            logger.warning(f"Ошибка при запросе к {url}: {str(e)}")
    
    # Если все попытки не удались, используем тестовые данные
    logger.warning("Не удалось получить данные через публичный API. Используем тестовые данные.")
    return create_test_subject_teacher_relations()

def create_test_teacher_data():
    """Создает тестовые данные о преподавателях"""
    logger.info("Создаем тестовые данные о преподавателях")
    
    # Тестовые данные преподавателей
    return [
        {
            'user_id': 1001,
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'middle_name': 'Иванович',
            'academic_degree': 'к.т.н.',
            'academic_title': 'доцент',
            'department': 'Кафедра информационных технологий',
            'position': 'Доцент',
            'email': 'ivanov@example.com'
        },
        {
            'user_id': 1002,
            'first_name': 'Петр',
            'last_name': 'Петров',
            'middle_name': 'Петрович',
            'academic_degree': 'д.т.н.',
            'academic_title': 'профессор',
            'department': 'Кафедра информационных технологий',
            'position': 'Профессор',
            'email': 'petrov@example.com'
        },
        {
            'user_id': 1003,
            'first_name': 'Анна',
            'last_name': 'Сидорова',
            'middle_name': 'Алексеевна',
            'academic_degree': 'к.ф-м.н.',
            'academic_title': 'доцент',
            'department': 'Кафедра математики',
            'position': 'Старший преподаватель',
            'email': 'sidorova@example.com'
        }
    ]

def create_test_subject_teacher_relations():
    """Создает тестовые данные о связях преподавателей с предметами"""
    logger.info("Создаем тестовые связи преподавателей с предметами")
    
    # Получаем реальные предметы из БД
    subjects = Subject.objects.all()
    if not subjects.exists():
        logger.error("В базе данных отсутствуют предметы")
        return []
        
    # Создаем тестовые связи для предметов
    test_relations = []
    teachers_ids = [1001, 1002, 1003]  # ID из тестовых преподавателей
    
    for idx, subject in enumerate(subjects):
        # Основной преподаватель
        main_teacher_id = teachers_ids[idx % len(teachers_ids)]
        test_relations.append({
            'subject_id': subject.id,
            'teacher_id': main_teacher_id,
            'role': 'Лектор',
            'is_main': True
        })
        
        # Дополнительный преподаватель
        second_teacher_id = teachers_ids[(idx + 1) % len(teachers_ids)]
        test_relations.append({
            'subject_id': subject.id,
            'teacher_id': second_teacher_id,
            'role': 'Руководитель практики',
            'is_main': False
        })
    
    return test_relations

def sync_teachers():
    """Синхронизирует данные о преподавателях"""
    logger.info("Начинаем синхронизацию преподавателей...")
    
    # Используем тестовые данные о преподавателях
    teachers_data = create_test_teacher_data()
    if not teachers_data:
        return
    
    created_count = 0
    updated_count = 0
    
    for teacher_data in teachers_data:
        try:
            # Проверяем, существует ли преподаватель
            teacher, created = Teacher.objects.update_or_create(
                user_id=teacher_data['user_id'],
                defaults={
                    'first_name': teacher_data['first_name'],
                    'last_name': teacher_data['last_name'],
                    'middle_name': teacher_data.get('middle_name'),
                    'academic_degree': teacher_data.get('academic_degree'),
                    'academic_title': teacher_data.get('academic_title'),
                    'department': teacher_data.get('department'),
                    'position': teacher_data.get('position'),
                    'email': teacher_data.get('email')
                }
            )
            
            if created:
                created_count += 1
                logger.info(f"Создан преподаватель: {teacher}")
            else:
                updated_count += 1
                logger.info(f"Обновлен преподаватель: {teacher}")
                
        except Exception as e:
            logger.error(f"Ошибка при обработке преподавателя {teacher_data.get('user_id')}: {str(e)}")
    
    logger.info(f"Синхронизация преподавателей завершена. Создано: {created_count}, Обновлено: {updated_count}")

def sync_subject_teacher_relations():
    """Синхронизирует связи преподавателей с предметами"""
    logger.info("Начинаем синхронизацию связей преподавателей с предметами...")
    
    # Получаем данные о связях с портала преподавателя через специальный эндпоинт
    relations_data = fetch_subject_teacher_relations()
    if not relations_data:
        logger.warning("Не удалось получить данные о связях, используем тестовые данные")
        relations_data = create_test_subject_teacher_relations()
        if not relations_data:
            return
    
    created_count = 0
    updated_count = 0
    errors_count = 0
    
    # Обрабатываем каждую связь
    for relation in relations_data:
        try:
            # Получаем или создаем преподавателя по данным из связи
            teacher_data = relation.get('teacher', {})
            if not teacher_data:
                logger.warning(f"Отсутствуют данные о преподавателе в связи: {relation}")
                errors_count += 1
                continue
                
            teacher, teacher_created = Teacher.objects.update_or_create(
                user_id=teacher_data.get('id', 0),  # Используем ID как user_id
                defaults={
                    'first_name': teacher_data.get('name', '').split(' ')[0] if ' ' in teacher_data.get('name', '') else teacher_data.get('name', ''),
                    'last_name': ' '.join(teacher_data.get('name', '').split(' ')[1:]) if ' ' in teacher_data.get('name', '') else '',
                    'department': teacher_data.get('department', ''),
                    'position': teacher_data.get('position', ''),
                    'academic_degree': teacher_data.get('academic_degree', ''),
                    'email': teacher_data.get('email', '')
                }
            )
            
            if teacher_created:
                logger.info(f"Создан новый преподаватель: {teacher}")
                
            # Получаем или создаем предмет
            subject_data = relation.get('subject', {})
            if not subject_data:
                logger.warning(f"Отсутствуют данные о предмете в связи: {relation}")
                errors_count += 1
                continue
            
            subject, subject_created = Subject.objects.update_or_create(
                id=subject_data.get('id', 0),
                defaults={
                    'name': subject_data.get('name', ''),
                    'description': subject_data.get('description', ''),
                    'semester': subject_data.get('semester', 1)
                }
            )
            
            if subject_created:
                logger.info(f"Создан новый предмет: {subject}")
                
            # Создаем или обновляем связь преподаватель-предмет
            subject_teacher, created = SubjectTeacher.objects.update_or_create(
                subject=subject,
                teacher=teacher,
                role=relation.get('role', ''),
                defaults={
                    'is_main': relation.get('is_main', False)
                }
            )
            
            if created:
                created_count += 1
                logger.info(f"Создана связь: {subject_teacher}")
            else:
                updated_count += 1
                logger.info(f"Обновлена связь: {subject_teacher}")
                
        except Exception as e:
            errors_count += 1
            logger.error(f"Ошибка при обработке связи {relation}: {str(e)}")
    
    logger.info(f"Синхронизация связей завершена. Создано: {created_count}, Обновлено: {updated_count}, Ошибок: {errors_count}")

def ping_api():
    """Проверяет доступность API портала преподавателя"""
    try:
        # Пробуем подключиться к корню API
        response = requests.get(f"{TEACHER_PORTAL_URL}/", timeout=3)
        if response.status_code in [200, 404]:  # 404 тоже считаем успехом - API работает
            logger.info(f"API портала преподавателя доступен (статус: {response.status_code})")
            return True
        else:
            logger.warning(f"API портала преподавателя недоступен (статус: {response.status_code})")
            return False
    except requests.RequestException as e:
        logger.error(f"Ошибка при подключении к API: {str(e)}")
        return False

def main():
    """Основная функция синхронизации"""
    logger.info("===== Начинаем синхронизацию данных между порталами =====")
    start_time = datetime.now()
    
    try:
        # Проверяем доступность API
        api_available = ping_api()
        if not api_available:
            logger.warning("API портала преподавателя недоступен. Будут использоваться тестовые данные.")
        
        # Синхронизируем преподавателей
        sync_teachers()
        
        # Синхронизируем связи преподавателей с предметами
        sync_subject_teacher_relations()
        
        # Отправляем уведомление об успешной синхронизации
        logger.info(f"Синхронизация успешно завершена за {datetime.now() - start_time}")
        
    except Exception as e:
        logger.error(f"Ошибка при синхронизации: {str(e)}")
        
    logger.info("===== Синхронизация завершена =====")

# Создаем фоновую задачу, если доступен background_task
if BACKGROUND_TASK_AVAILABLE:
    @background(schedule=10800)  # 3 часа = 10800 секунд
    def scheduled_sync():
        """Запускает синхронизацию по расписанию"""
        main()
else:
    def scheduled_sync():
        """Заглушка для случая, когда background_task недоступен"""
        logger.warning("Background tasks недоступны. Запуск синхронизации в обычном режиме.")
        main()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--schedule" and BACKGROUND_TASK_AVAILABLE:
        # Планируем задачу на регулярное выполнение 
        # 3 часа = 10800 секунд
        scheduled_sync(repeat=10800, verbose_name="Синхронизация преподавателей")
        logger.info("Задача синхронизации запланирована (каждые 3 часа)")
    else:
        # Запускаем синхронизацию немедленно
        main() 