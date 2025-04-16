import base64

def binary_to_string(binary_data):
    """Convert binary data to base64 string"""
    if isinstance(binary_data, str):
        return binary_data
    return base64.b64encode(binary_data).decode('utf-8')

def string_to_binary(string_data):
    """Convert base64 string to binary data"""
    if isinstance(string_data, bytes):
        return string_data
    return base64.b64decode(string_data) 