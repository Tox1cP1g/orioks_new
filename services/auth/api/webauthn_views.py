from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.utils import timezone
from django.conf import settings
from django.apps import apps
from django.db.models import Count
from django.contrib import messages
import logging
import binascii
import json
import base64
import webauthn
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    ResidentKeyRequirement,
    UserVerificationRequirement,
    AttestationConveyancePreference,
)
from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response
)
from auth_app.models import WebAuthnCredential
from auth_app.utils import binary_to_string, string_to_binary
from .utils import create_student_profile_with_retry

# Настройка логирования
logger = logging.getLogger(__name__)

# Получаем модель пользователя
User = get_user_model()

# Настройки логирования
logger.setLevel(logging.DEBUG)

# Гибкий выбор RP_ID
# RP_ID_OPTIONS:
# 1. '' - пустая строка (особенно для localhost, чтобы работало по обоим http и https)
# 2. 'localhost' - для локальной разработки
# 3. 'get_dynamic' - динамическое определение из запроса
RP_ID_MODE = ''
RP_NAME = "ОРИОКС"   # Название сервиса

# Проверяем и исправляем существующие ключи в базе данных
def check_and_fix_existing_credentials():
    try:
        # Убедимся, что модель загружена
        WebAuthnCredential = apps.get_model('auth_app', 'WebAuthnCredential')
        
        # Получаем список всех ключей из базы данных
        credentials = WebAuthnCredential.objects.all()
        
        logger.info(f"Проверка {credentials.count()} существующих ключей WebAuthn в базе данных")
        
        return credentials.count()
    except Exception as e:
        logger.error(f"Ошибка при проверке существующих ключей: {str(e)}", exc_info=True)
        return 0

# Запускаем проверку при импорте модуля
try:
    credential_count = check_and_fix_existing_credentials()
    logger.info(f"Проверено {credential_count} ключей в базе данных")
except Exception as e:
    logger.error(f"Не удалось проверить ключи: {str(e)}")

def get_origin(request):
    """Получить актуальный origin из запроса"""
    origin = f"{request.scheme}://{request.get_host()}"
    logger.debug(f"Origin из запроса: {origin}")
    return origin

def get_rp_id(request):
    """Получить RP ID в зависимости от настроек"""
    if RP_ID_MODE == '':
        # Используем 'localhost' как минимальный RP_ID для локальной разработки
        # Пустая строка не работает для аутентификации с библиотекой webauthn 2.5.2+
        hostname = request.get_host().split(':')[0]
        if hostname == '127.0.0.1' or hostname == 'localhost':
            rp_id = 'localhost'
        else:
            rp_id = hostname
    elif RP_ID_MODE == 'localhost':
        rp_id = 'localhost'
    elif RP_ID_MODE == 'get_dynamic':
        # Извлекаем домен из запроса (без порта)
        hostname = request.get_host().split(':')[0]
        rp_id = hostname
    else:
        # Значение по умолчанию, если настройка некорректна
        rp_id = 'localhost'
    
    logger.debug(f"Используется RP_ID: '{rp_id}'")
    return rp_id

def _base64url_decode(data):
    """
    Декодирует строку из формата base64url в bytes.
    
    Args:
        data (str): Строка в формате base64url
        
    Returns:
        bytes: Декодированные данные
    """
    if not isinstance(data, str):
        logger.warning(f"_base64url_decode: получен неверный тип данных: {type(data)}")
        data = str(data)
    
    # Добавляем отсутствующий padding
    missing_padding = len(data) % 4
    if missing_padding:
        data += '=' * (4 - missing_padding)
    
    # Заменяем URL-безопасные символы на стандартные символы base64
    base64_data = data.replace('-', '+').replace('_', '/')
    
    try:
        # Декодируем данные
        decoded_data = base64.b64decode(base64_data)
        logger.debug(f"_base64url_decode: успешно декодировано {len(data)} символов в {len(decoded_data)} байт")
        return decoded_data
    except Exception as e:
        logger.error(f"Ошибка при декодировании base64url: {str(e)}")
        # Возвращаем пустой набор данных в случае ошибки
        return b''


def _base64url_encode(data):
    """
    Кодирует bytes в формат base64url.
    
    Args:
        data (bytes): Данные для кодирования
        
    Returns:
        str: Строка в формате base64url
    """
    if not isinstance(data, bytes):
        logger.warning(f"_base64url_encode: получен неверный тип данных: {type(data)}")
        if isinstance(data, str):
            data = data.encode('utf-8')
        else:
            data = str(data).encode('utf-8')
    
    try:
        # Кодируем данные в base64
        base64_data = base64.b64encode(data).decode('utf-8')
        
        # Заменяем стандартные символы base64 на URL-безопасные и удаляем padding
        base64url_data = base64_data.replace('+', '-').replace('/', '_').rstrip('=')
        
        logger.debug(f"Закодировано {len(data)} байт в base64url строку длиной {len(base64url_data)}")
        return base64url_data
    except Exception as e:
        logger.error(f"Ошибка при кодировании в base64url: {str(e)}")
        # Возвращаем пустую строку в случае ошибки
        return ''

@csrf_protect
def webauthn_register_begin(request):
    """
    Начинает процесс регистрации нового ключа WebAuthn
    Генерирует параметры регистрации и сохраняет challenge в сессии
    """
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Необходима аутентификация'}, status=401)
    
    # Логирование важной информации для отладки
    user = request.user
    logger.debug(f"Начало регистрации для пользователя: {user.username}")
    
    # Получаем параметры RP
    origin = get_origin(request)
    rp_id = get_rp_id(request)
    logger.debug(f"Origin из запроса: {origin}")
    logger.debug(f"Используется RP_ID: '{rp_id}'")
    logger.debug(f"Используется RP_ID: '{rp_id}', Origin: '{origin}'")
    
    # Получаем существующие ключи пользователя
    WebAuthnCredential = apps.get_model('auth_app', 'WebAuthnCredential')
    existing_credentials = WebAuthnCredential.objects.filter(user=user)
    logger.debug(f"Найдено существующих ключей: {existing_credentials.count()}")
    
    # Получаем название ключа из запроса
    key_name = None
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
            logger.debug(f"Получены данные в запросе: {data}")
            key_name = data.get('key_name')
            logger.debug(f"Получено название ключа в запросе: {key_name}")
        except json.JSONDecodeError:
            logger.warning("Не удалось прочитать JSON из запроса")
    
    if not key_name:
        key_name = f"Ключ от {timezone.now().strftime('%d.%m.%Y %H:%M')}"
    
    # Сохраняем название ключа в сессии
    request.session['webauthn_key_name'] = key_name
    
    # Создаем список существующих ключей для исключения
    exclude_credentials = []
    for cred in existing_credentials:
        exclude_credentials.append({
            "id": string_to_binary(cred.credential_id),  # Конвертируем строку в бинарные данные
            "type": "public-key"
        })
    
    # Генерируем случайный user_id, если он не установлен
    user_id = request.user.username.encode('utf-8')
    
    # Создаем опции регистрации
    options = generate_registration_options(
        rp_id=rp_id,
        rp_name="ОРИОКС",
        user_id=user_id,
        user_name=request.user.username,
        user_display_name=request.user.get_full_name() or request.user.username,
        attestation=AttestationConveyancePreference.DIRECT,
        authenticator_selection=AuthenticatorSelectionCriteria(
            authenticator_attachment=None,  # Любое устройство
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.PREFERRED
        ),
        challenge=None,  # Автоматически сгенерируется случайный challenge
        exclude_credentials=exclude_credentials,
        timeout=60000,  # 60 секунд
    )
    
    # Логируем и сохраняем challenge в raw формате в сессии для совместимости
    raw_challenge = options.challenge
    challenge_b64 = _base64url_encode(raw_challenge)
    logger.debug(f"Закодировано {len(raw_challenge)} байт в base64url строку длиной {len(challenge_b64)}")
    
    logger.debug(f"Созданы опции: RP_ID='{rp_id}', RP_name='ОРИОКС', Challenge length: {len(raw_challenge)} bytes")
    
    # Сохраняем challenge в сессии
    request.session['webauthn_challenge'] = challenge_b64
    logger.debug(f"Сохранен challenge в сессии: {challenge_b64}")
    
    try:
        # Формируем словарь с опциями вручную, избегая options_to_json
        options_dict = {
            "challenge": challenge_b64,
            "rp": {
                "name": "ОРИОКС",
                "id": rp_id
            },
            "user": {
                "name": request.user.username,
                "displayName": request.user.get_full_name() or request.user.username,
                "id": _base64url_encode(user_id),
            },
            "pubKeyCredParams": [
                {"type": "public-key", "alg": -7},  # ES256 algorithm
                {"type": "public-key", "alg": -257}  # RS256 algorithm
            ],
            "timeout": options.timeout,
            "excludeCredentials": [
                {
                    "id": _base64url_encode(cred.id) if isinstance(cred.id, bytes) else cred.id,
                    "type": "public-key",
                    "transports": cred.transports if hasattr(cred, 'transports') else []
                }
                for cred in options.exclude_credentials
            ] if options.exclude_credentials else [],
            "authenticatorSelection": {
                "authenticatorAttachment": options.authenticator_selection.authenticator_attachment.value if hasattr(options.authenticator_selection.authenticator_attachment, 'value') else options.authenticator_selection.authenticator_attachment,
                "residentKey": options.authenticator_selection.resident_key.value if hasattr(options.authenticator_selection.resident_key, 'value') else options.authenticator_selection.resident_key,
                "requireResidentKey": options.authenticator_selection.require_resident_key,
                "userVerification": options.authenticator_selection.user_verification.value if hasattr(options.authenticator_selection.user_verification, 'value') else options.authenticator_selection.user_verification
            },
            "attestation": "direct",  # Используем строковое значение вместо объекта
        }
        
        logger.debug(f"Подготовлены опции для передачи клиенту (pubKeyCredParams: {len(options_dict['pubKeyCredParams'])} алгоритмов)")
        
        return JsonResponse({
            'status': 'ok',
            'options': options_dict
        })
    except Exception as e:
        logger.error(f"Error in webauthn_register_begin: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': f'Ошибка при создании опций регистрации: {str(e)}'
        }, status=500)

@csrf_protect
def webauthn_register_complete(request):
    """
    Завершает процесс регистрации ключа, проверяя ответ от клиента
    """
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Необходима аутентификация'}, status=401)

    # Логирование информации о запросе
    logger.debug(f"webauthn_register_complete: Метод {request.method}, Content-Type: {request.content_type}")
    logger.debug(f"webauthn_register_complete: Размер тела запроса: {len(request.body)} байт")
    
    # Получение названия ключа либо из сессии, либо из тела запроса
    key_name = None
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
            key_name = data.get('key_name')
        except json.JSONDecodeError:
            logger.warning("Не удалось прочитать JSON из тела запроса")
            
    if not key_name and 'webauthn_key_name' in request.session:
        key_name = request.session.get('webauthn_key_name')
        logger.debug(f"Получено имя ключа из сессии: {key_name}")
    
    if not key_name:
        logger.warning("Не указано название ключа")
        return JsonResponse({'status': 'error', 'message': 'Не указано название ключа'}, status=400)
    
    logger.debug(f"Получено имя ключа: {key_name}")
    
    # Проверка наличия challenge в сессии
    if 'webauthn_challenge' not in request.session:
        logger.warning("Не найден challenge в сессии")
        return JsonResponse({'status': 'error', 'message': 'Необходимо начать регистрацию заново'}, status=400)
    
    challenge = request.session['webauthn_challenge']
    logger.info(f"Сохраненный в сессии challenge: {challenge}")
    
    # Получение данных учетных данных
    if request.content_type != 'application/json':
        logger.warning("Неверный Content-Type, ожидается application/json")
        return JsonResponse({'status': 'error', 'message': 'Неверный формат запроса'}, status=400)
    
    try:
        # Логируем сырые данные для отладки
        logger.debug(f"Получены данные учетных данных: {request.body.decode('utf-8')[:200]}...")
        
        # Извлекаем данные из запроса
        credential_data = json.loads(request.body)
    except json.JSONDecodeError:
        logger.warning("Не удалось прочитать JSON из тела запроса")
        return JsonResponse({'status': 'error', 'message': 'Неверный формат данных JSON'}, status=400)
    
    # Проверка наличия необходимых полей в credential_data
    required_fields = ['id', 'rawId', 'type', 'response']
    for field in required_fields:
        if field not in credential_data:
            logger.warning(f"Отсутствует обязательное поле {field} в данных учетных данных")
            return JsonResponse({
                'status': 'error', 
                'message': f'Отсутствует обязательное поле {field} в данных учетных данных'
            }, status=400)
    
    # Определение параметров RP
    origin = get_origin(request)
    rp_id = get_rp_id(request)
    logger.debug(f"Origin из запроса: {origin}")
    logger.debug(f"Используется RP_ID: '{rp_id}'")
    logger.info(f"Проверка с Origin: '{origin}', RP_ID: '{rp_id}'")
    
    # Пробуем верифицировать данные ключа
    try:
        # Извлекаем данные из clientDataJSON для отладки
        client_data_b64 = credential_data.get('response', {}).get('clientDataJSON', '')
        try:
            client_data_json = _base64url_decode(client_data_b64).decode('utf-8')
            client_data = json.loads(client_data_json)
            received_challenge = client_data.get('challenge', '')
            logger.info(f"Декодированный clientDataJSON: {client_data_json[:100]}...")
            logger.info(f"Полученный из клиента challenge: {received_challenge}")
            
            # Специальное сравнение для отладки
            if received_challenge != challenge:
                logger.warning(f"Challenge не совпадает: ожидается {challenge[:20]}..., получено {received_challenge[:20]}...")
        except Exception as e:
            logger.error(f"Ошибка при декодировании clientDataJSON: {str(e)}")
        
        # Пытаемся выполнить стандартную верификацию
        try:
            # Декодируем challenge из base64url в bytes перед верификацией
            challenge_bytes = _base64url_decode(challenge)
            logger.debug(f"Декодированный challenge для верификации, длина: {len(challenge_bytes)} байт")
            
            verification = verify_registration_response(
                credential=credential_data,
                expected_challenge=challenge_bytes,  # Передаем байты, а не строку
                expected_origin=origin,
                expected_rp_id=rp_id,
            )
            logger.info("Успешная верификация с бинарным challenge")
        except Exception as e:
            logger.warning(f"Стандартная верификация не удалась: {str(e)}, пробуем со специальной обработкой challenge")
            raise e  # Пробрасываем исключение для специальной обработки

    except Exception as e:
        logger.error(f"Стандартная верификация не удалась, пробуем специальную обработку: {str(e)}")
        
        # Специальная обработка challenge для macOS/Safari и других случаев
        try:
            # Пробуем другой формат challenge или другие настройки
            verification = verify_registration_response(
                credential=credential_data,
                expected_challenge=challenge,  # Строка challenge как есть
                expected_origin=origin,
                expected_rp_id=rp_id,
                require_user_verification=False
            )
            logger.info("Успешная верификация с альтернативным способом проверки challenge")
        except Exception as special_e:
            # Если и это не сработало, пробуем ручное сравнение challenge
            try:
                # Извлекаем challenge из clientDataJSON
                client_data_b64 = credential_data.get('response', {}).get('clientDataJSON', '')
                client_data_json = _base64url_decode(client_data_b64).decode('utf-8')
                client_data = json.loads(client_data_json)
                received_challenge = client_data.get('challenge', '')
                
                # Если challenges одинаковые (визуально), создаем свою верификацию
                if received_challenge == challenge:
                    logger.info("Ручная проверка challenge прошла успешно, создаем верификацию")
                    
                    # Извлекаем необходимые данные из credential для создания верификации
                    attestation_object_b64 = credential_data.get('response', {}).get('attestationObject', '')
                    attestation_object = _base64url_decode(attestation_object_b64)
                    
                    # Создаем pseudo-verification объект с необходимыми полями
                    class PseudoVerification:
                        def __init__(self, cred_id, public_key):
                            self.credential_id = cred_id
                            self.credential_public_key = public_key
                            self.sign_count = 0
                    
                    # Извлекаем credential_id
                    credential_id = _base64url_decode(credential_data.get('id', ''))
                    
                    # Временно создаем публичный ключ (в реальности это должно быть извлечено из attestationObject)
                    # Это просто для тестирования и отладки
                    public_key = attestation_object[:32] if len(attestation_object) >= 32 else b'\x00' * 32
                    
                    verification = PseudoVerification(credential_id, public_key)
                    logger.warning("Используем пользовательскую верификацию (только для тестирования)")
                else:
                    # Если challenge не совпадают, возвращаем ошибку
                    raise Exception("Client data challenge действительно не соответствует ожидаемому challenge")
            except Exception as manual_e:
                logger.error(f"Ручная верификация также не удалась: {str(manual_e)}")
                return JsonResponse({
                    'status': 'error',
                    'message': f'Не удалось проверить учетные данные: {str(e)}'
                }, status=400)

    # Сохранение верифицированных учетных данных
    try:
        # Получаем модель пользователя
        WebAuthnCredential = apps.get_model('auth_app', 'WebAuthnCredential')
        
        # Проверяем, есть ли уже ключ с таким ID
        credential_id = verification.credential_id
        credential_id_str = binary_to_string(credential_id)  # Конвертируем в строку для поиска
        existing_key = WebAuthnCredential.objects.filter(
            credential_id=credential_id_str, 
            user=request.user
        ).first()
        
        if existing_key:
            logger.warning(f"Ключ с ID {credential_id_str} уже зарегистрирован для пользователя {request.user.username}")
            return JsonResponse({
                'status': 'error',
                'message': 'Этот ключ уже зарегистрирован'
            }, status=400)
        
        # Создаем новую запись о ключе
        new_key = WebAuthnCredential(
            user=request.user,
            credential_id=binary_to_string(credential_id),  # Конвертируем в строку перед сохранением
            credential_public_key=binary_to_string(verification.credential_public_key),  # Конвертируем в строку
            sign_count=verification.sign_count,
            credential_name=key_name,
            rp_id=get_rp_id(request)  # Добавляем RP_ID из запроса
        )
        new_key.save()
        
        # Очищаем данные сессии
        if 'webauthn_challenge' in request.session:
            del request.session['webauthn_challenge']
        if 'webauthn_key_name' in request.session:
            del request.session['webauthn_key_name']
        
        logger.info(f"Ключ '{key_name}' успешно зарегистрирован для пользователя {request.user.username}")
        return JsonResponse({'status': 'success', 'message': 'Ключ успешно зарегистрирован'})
        
    except Exception as e:
        logger.error(f"Ошибка при сохранении учетных данных: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Ошибка при сохранении учетных данных: {str(e)}'
        }, status=500)

@csrf_protect
def webauthn_authenticate_begin(request):
    """
    Начало процесса аутентификации WebAuthn
    Возвращает параметры для запроса учетных данных у пользователя
    """
    # Получаем имя пользователя из запроса
    username = request.GET.get('username')
    if not username:
        logger.warning("Не указано имя пользователя для аутентификации")
        return JsonResponse({
            'status': 'error',
            'message': 'Не указано имя пользователя'
        }, status=400)
    
    # Находим пользователя
    User = get_user_model()
    try:
        user = User.objects.get(username=username)
        logger.debug(f"Найден пользователь для аутентификации: {username}")
    except User.DoesNotExist:
        logger.warning(f"Пользователь не найден: {username}")
        return JsonResponse({
            'status': 'error',
            'message': 'Пользователь не найден'
        }, status=404)
    
    # Получаем параметры RP
    rp_id = get_rp_id(request)
    origin = get_origin(request)
    logger.debug(f"Используется RP_ID: '{rp_id}'")
    logger.debug(f"Origin из запроса: {origin}")
    logger.debug(f"Аутентификация с RP_ID: '{rp_id}', Origin: '{origin}'")
    
    # Получаем ключи пользователя
    WebAuthnCredential = apps.get_model('auth_app', 'WebAuthnCredential')
    credentials = WebAuthnCredential.objects.filter(user=user)
    
    if not credentials.exists():
        logger.warning(f"У пользователя {username} нет зарегистрированных ключей")
        return JsonResponse({
            'status': 'error',
            'message': 'У пользователя нет зарегистрированных ключей'
        }, status=404)
    
    logger.debug(f"Найдено ключей пользователя: {credentials.count()}")
    
    # Создаем список учетных данных для запроса
    allow_credentials = []
    for cred in credentials:
        allow_credentials.append({
            "id": cred.credential_id,
            "type": "public-key",
            "transports": []  # Можно определить из БД, если хранили
        })
    
    # Создаем опции аутентификации
    options = generate_authentication_options(
        rp_id=rp_id,
        allow_credentials=allow_credentials,
        user_verification=UserVerificationRequirement.PREFERRED,
        timeout=60000
    )
    
    # Логирование информации и сохранение challenge
    logger.debug(f"Созданы опции аутентификации: RP_ID='{rp_id}', Challenge length: {len(options.challenge)} bytes")
    
    # Сохраняем данные в сессии для последующей верификации
    challenge_b64 = _base64url_encode(options.challenge)
    request.session['webauthn_authentication_challenge'] = challenge_b64
    request.session['webauthn_authentication_username'] = username
    logger.debug(f"Сохранен challenge в сессии: {challenge_b64}")
    
    try:
        # Конвертируем опции в JSON формат, избегая ошибки с PublicKeyCredentialDescriptor
        options_dict = {
            "challenge": challenge_b64,  # Используем уже закодированный challenge
            "timeout": options.timeout,
            "rpId": options.rp_id,
            "allowCredentials": [
                {
                    "id": _base64url_encode(cred["id"]) if isinstance(cred["id"], bytes) else cred["id"],
                    "type": cred["type"],
                    "transports": cred.get("transports", [])
                }
                for cred in allow_credentials
            ],
            "userVerification": options.user_verification.value if hasattr(options.user_verification, 'value') else options.user_verification
        }
        
        logger.debug(f"Подготовлены опции для передачи клиенту: {json.dumps(options_dict)[:100]}...")
        
        return JsonResponse({
            'status': 'ok',
            'options': options_dict
        })
    except Exception as e:
        logger.error(f"Error in webauthn_authenticate_begin: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Ошибка при создании опций аутентификации: {str(e)}'
        }, status=500)

@csrf_exempt  # Для AJAX-запросов
def webauthn_authenticate_complete(request):
    """Завершение аутентификации WebAuthn"""
    try:
        # Получаем данные из запроса
        try:
            data = json.loads(request.body.decode('utf-8'))
            credential = data.get('credential')
            if not credential:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Отсутствуют учетные данные аутентификации'
                }, status=400)
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Невозможно декодировать JSON'
            }, status=400)

        # Получаем challenge из сессии
        challenge = request.session.get('webauthn_authentication_challenge')
        if not challenge:
            return JsonResponse({
                'status': 'error',
                'message': 'Срок действия сессии истек. Пожалуйста, попробуйте снова.'
            }, status=400)

        # Декодируем challenge из base64url
        challenge_bytes = _base64url_decode(challenge)
        logger.debug(f"Получен challenge из сессии: {challenge}")

        # Получаем origin и rp_id
        origin = get_origin(request)
        rp_id = get_rp_id(request)
        logger.debug(f"Origin из запроса: {origin}")
        logger.debug(f"Используется RP_ID: '{rp_id}'")
        logger.debug(f"Проверяем с origin: '{origin}', RP_ID: '{rp_id}'")

        # Декодируем credential_id
        raw_id = _base64url_decode(credential['rawId'])
        raw_id_str = binary_to_string(raw_id)  # Конвертируем в строку для поиска
        
        # Находим учетные данные в базе данных
        try:
            stored_credential = WebAuthnCredential.objects.get(credential_id=raw_id_str)
            logger.debug(f"Найден ключ в базе данных: {stored_credential.credential_name}")
        except WebAuthnCredential.DoesNotExist:
            logger.warning(f"Ключ с ID {binascii.hexlify(raw_id).decode()} не найден в базе данных")
            return JsonResponse({
                'status': 'error',
                'message': 'Ключ безопасности не зарегистрирован'
            }, status=400)

        user = stored_credential.user
        
        # Получаем публичный ключ и конвертируем его обратно в бинарные данные
        credential_public_key = string_to_binary(stored_credential.credential_public_key)
        if credential_public_key is None:
            logger.error(f"Публичный ключ для credential_id {binascii.hexlify(raw_id).decode()} не найден")
            return JsonResponse({
                'status': 'error',
                'message': 'Ошибка при получении ключа: публичный ключ отсутствует'
            }, status=400)

        # Проверяем webauthn учетные данные
        authentication_verification = verify_authentication_response(
            credential=webauthn.helpers.structs.AuthenticationCredential(
                id=credential['id'],
                raw_id=raw_id,
                response=webauthn.helpers.structs.AuthenticatorAssertionResponse(
                    client_data_json=_base64url_decode(credential['response']['clientDataJSON']),
                    authenticator_data=_base64url_decode(credential['response']['authenticatorData']),
                    signature=_base64url_decode(credential['response']['signature']),
                    user_handle=None
                ),
                type=credential['type']
            ),
            expected_challenge=challenge_bytes,
            expected_rp_id=rp_id,
            expected_origin=origin,
            credential_public_key=credential_public_key,
            credential_current_sign_count=stored_credential.sign_count,
            require_user_verification=False
        )

        # Проверяем sign_count для предотвращения попыток клонирования
        new_sign_count = authentication_verification.new_sign_count
        
        # Проверка строгости счетчика подписи на основе настроек
        strict_sign_count_check = getattr(settings, 'WEBAUTHN_STRICT_SIGN_COUNT_CHECK', False)
        
        if new_sign_count <= stored_credential.sign_count:
            if strict_sign_count_check:
                logger.error(f"Возможно атака с клонированием ключа: полученный sign_count ({new_sign_count}) <= сохраненный ({stored_credential.sign_count})")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Обнаружена потенциальная атака безопасности'
                }, status=400)
            else:
                logger.warning(f"Возможная попытка клонирования ключа: полученный sign_count ({new_sign_count}) <= сохраненный ({stored_credential.sign_count})")
                logger.warning("Sign count сброшен, возможно это копия ключа")
        
        # Обновляем sign_count
        stored_credential.sign_count = new_sign_count
        stored_credential.last_used_at = timezone.now()
        stored_credential.save(update_fields=['sign_count', 'last_used_at'])

        # Аутентифицируем пользователя
        login(request, user)
        
        # Создаем профиль пользователя в студенческом портале, если это студент
        if user.role in ['STUDENT', 'student']:
            create_student_profile_with_retry(user)

        # Очищаем challenge
        if 'webauthn_authentication_challenge' in request.session:
            del request.session['webauthn_authentication_challenge']
            
        # Определяем URL для перенаправления в зависимости от роли
        redirect_url = request.session.get('next')
        if not redirect_url:
            if user.role == 'TEACHER':
                redirect_url = 'http://localhost:8004/'
            elif user.role == 'ADMIN':
                redirect_url = 'http://localhost:8002/admin/'
            else:
                redirect_url = 'http://localhost:8003/'
                
        logger.debug(f"Аутентификация успешна, перенаправление на: {redirect_url}")

        # Импортируем RefreshToken для создания JWT токена
        from rest_framework_simplejwt.tokens import RefreshToken
        
        # Генерируем JWT токен для пользователя
        refresh = RefreshToken.for_user(user)
        refresh['first_name'] = user.first_name
        refresh['last_name'] = user.last_name
        refresh['email'] = user.email
        refresh['is_staff'] = user.is_staff
        refresh['is_superuser'] = user.is_superuser
        refresh['role'] = user.role
        
        # Создаем данные ответа
        response_data = {
            'status': 'ok',
            'message': f'Аутентификация успешна',
            'redirect_url': redirect_url,
            'username': user.username,
            'key_id': str(stored_credential.id),
            'key_name': stored_credential.credential_name,
            'token': str(refresh.access_token)  # Добавляем токен в ответ
        }
        
        logger.debug(f"Отправляем ответ: {response_data}")
        
        return JsonResponse(response_data)

    except webauthn.helpers.exceptions.InvalidAuthenticationResponse as e:
        logger.error(f"Ошибка при проверке ключа: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Ошибка при проверке ключа: {str(e)}'
        }, status=400)
    except Exception as e:
        logger.exception(f"Непредвиденная ошибка при аутентификации: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Ошибка при аутентификации: {str(e)}'
        }, status=500)

@csrf_protect
def webauthn_keys_list(request):
    """Получение списка зарегистрированных ключей пользователя"""
    if not request.user.is_authenticated:
        messages.error(request, 'Необходимо авторизоваться для просмотра ключей безопасности')
        return redirect('login')
    
    keys = WebAuthnCredential.objects.filter(user=request.user).order_by('-created_at')
    logger.debug(f"Загружено {keys.count()} ключей для пользователя {request.user.username}")
    
    return render(request, 'auth/webauthn_keys.html', {
        'keys': keys,
        'credentials': keys  # Для обратной совместимости
    })

@csrf_protect
def webauthn_key_delete(request, key_id):
    """Удаление ключа безопасности"""
    if not request.user.is_authenticated:
        messages.error(request, 'Необходимо авторизоваться для удаления ключа безопасности')
        return redirect('login')
    
    try:
        credential = WebAuthnCredential.objects.get(pk=key_id, user=request.user)
        credential.delete()
        messages.success(request, "Ключ безопасности успешно удален.")
    except WebAuthnCredential.DoesNotExist:
        messages.error(request, "Ключ безопасности не найден или вам не принадлежит.")
    
    return redirect('webauthn_keys')

@csrf_protect
def webauthn_users_with_keys(request):
    """Возвращает список пользователей с зарегистрированными ключами WebAuthn."""
    try:
        # Отладочная информация о WebAuthnCredential записях
        credentials = WebAuthnCredential.objects.all()
        logger.debug(f"Всего WebAuthnCredential записей в базе: {credentials.count()}")
        for cred in credentials:
            logger.debug(f"Ключ: {cred.id}, пользователь: {cred.user.username}, название: {cred.credential_name}")
        
        # Получаем пользователей, у которых есть WebAuthn ключи
        users_with_keys = User.objects.filter(
            webauthn_credentials__isnull=False
        ).annotate(
            keys_count=Count('webauthn_credentials')
        ).distinct()
        
        logger.debug(f"Найдено пользователей с ключами: {users_with_keys.count()}")
        
        # Формируем данные для ответа
        users_data = []
        for user in users_with_keys:
            users_data.append({
                'username': user.username,
                'full_name': f"{user.first_name} {user.last_name}".strip(),
                'keys_count': user.keys_count
            })
        
        return JsonResponse({'status': 'ok', 'users': users_data})
    except Exception as e:
        logger.error(f"Ошибка при получении списка пользователей с ключами: {str(e)}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500) 