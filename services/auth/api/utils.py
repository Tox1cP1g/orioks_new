import requests
import logging
import json
import time

logger = logging.getLogger(__name__)

def create_student_profile(user):
    """Создаёт профиль пользователя в студенческом портале"""
    if not user:
        logger.error("Не передан пользователь для создания профиля")
        return False
    
    try:
        # Подготавливаем данные пользователя
        user_data = {
            'user_id': user.id,
            'username': user.username,
            'full_name': f"{user.first_name} {user.last_name}".strip(),
            'role': getattr(user, 'role', 'student'),
            'email': getattr(user, 'email', '')
        }
        
        logger.debug(f"Отправка запроса на создание профиля для пользователя {user.username}")
        logger.debug(f"Данные отправляемые в запросе: {user_data}")
        
        # Используем имя сервиса в Docker-сети, но запрос делаем без порта в URL
        # и устанавливаем отдельный заголовок Host
        headers = {
            'Host': 'student_portal:8003',
            'User-Agent': 'auth-service/1.0',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        response = requests.post(
            'http://student_portal:8003/api/create-profile/',
            json=user_data,
            headers=headers,
            timeout=5
        )
        
        # Проверяем ответ
        if response.status_code == 200:
            result = response.json()
            if result.get('status') in ['success', 'exists']:
                logger.info(f"Профиль для пользователя {user.username} успешно создан/подтвержден")
                return True
            else:
                logger.warning(f"Ошибка при создании профиля: {result.get('message')}")
                return False
        elif response.status_code == 400:
            try:
                error_data = response.json()
                logger.error(f"Ошибка 400 Bad Request: {error_data}")
            except:
                logger.error(f"Ошибка 400 Bad Request, не удалось прочитать JSON ответа: {response.text}")
            return False
        else:
            logger.error(f"Ошибка API студенческого портала: HTTP {response.status_code}")
            return False
            
    except requests.RequestException as e:
        logger.error(f"Ошибка соединения со студенческим порталом: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при создании профиля: {str(e)}")
        return False

def create_student_profile_with_retry(user, max_retries=3):
    """Пытается создать профиль с повторными попытками"""
    for attempt in range(max_retries):
        success = create_student_profile(user)
        if success:
            return True
        
        # Задержка перед повторной попыткой
        if attempt < max_retries - 1:
            time.sleep(1)  # 1 секунда задержки
    
    return False 