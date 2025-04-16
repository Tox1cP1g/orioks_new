import base64


def binary_to_string(binary_data):
    """
    Конвертирует бинарные данные в строку base64.
    Используется для сохранения binary полей в text/char полях базы данных.

    Args:
        binary_data: Бинарные данные для конвертации

    Returns:
        str: Закодированная строка base64
    """
    if binary_data is None:
        return None

    if isinstance(binary_data, str):
        return binary_data  # Уже строка, просто возвращаем

    # Кодируем бинарные данные в base64
    return base64.b64encode(binary_data).decode('utf-8')


def string_to_binary(base64_string):
    """
    Конвертирует строку base64 обратно в бинарные данные.
    Используется для восстановления бинарных данных из text/char полей базы данных.

    Args:
        base64_string: Строка в формате base64

    Returns:
        bytes: Декодированные бинарные данные
    """
    if base64_string is None:
        return None

    if isinstance(base64_string, bytes):
        return base64_string  # Уже бинарные данные, просто возвращаем

    # Декодируем строку base64 в бинарные данные
    return base64.b64decode(base64_string)