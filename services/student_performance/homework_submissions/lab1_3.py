import sys

BLOCK_SIZE = 5
PADDING_CHAR = b'z'  # Байтовый символ 'z'


def read_key(filename):
    """Считывает ключ из файла и возвращает список перестановок."""
    try:
        with open(filename, "r") as f:
            key = list(map(int, f.read().split()))
            if sorted(key) != list(range(BLOCK_SIZE)):
                raise ValueError("Некорректный ключ! Должны быть числа 0-4 в произвольном порядке.")
            return key
    except Exception as e:
        print(f"Ошибка при чтении ключа: {e}")
        sys.exit(1)


def encrypt_file(input_file, output_file, key):
    """Шифрует файл методом вертикальной перестановки."""
    with open(input_file, "rb") as f:
        data = f.read()

    # Добавляем 'z' до кратности 5
    padding_needed = (BLOCK_SIZE - len(data) % BLOCK_SIZE) % BLOCK_SIZE
    data += PADDING_CHAR * padding_needed

    encrypted_data = bytearray()
    for i in range(0, len(data), BLOCK_SIZE):
        block = data[i:i + BLOCK_SIZE]
        encrypted_block = bytearray(block[k] for k in key)
        encrypted_data.extend(encrypted_block)

    with open(output_file, "wb") as f:
        f.write(encrypted_data)

    print(f"Файл {input_file} зашифрован в {output_file}")


def decrypt_file(input_file, output_file, key):
    """Расшифровывает файл методом вертикальной перестановки."""
    with open(input_file, "rb") as f:
        data = f.read()

    decrypted_data = bytearray()
    inverse_key = [key.index(i) for i in range(BLOCK_SIZE)]  # Обратная перестановка

    for i in range(0, len(data), BLOCK_SIZE):
        block = data[i:i + BLOCK_SIZE]
        decrypted_block = bytearray(block[k] for k in inverse_key)
        decrypted_data.extend(decrypted_block)

    # Убираем лишние 'z', если они были добавлены при шифровании
    while decrypted_data and decrypted_data[-1] == PADDING_CHAR[0]:
        decrypted_data.pop()

    with open(output_file, "wb") as f:
        f.write(decrypted_data)

    print(f"Файл {input_file} расшифрован в {output_file}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Использование: python script.py <encrypt|decrypt> <входной_файл> <выходной_файл>")
        sys.exit(1)

    mode = sys.argv[1].lower()
    input_file = sys.argv[2]
    output_file = sys.argv[3]

    key = read_key("key.txt")  # Читаем ключ из файла

    if mode == "encrypt":
        encrypt_file(input_file, output_file, key)
    elif mode == "decrypt":
        decrypt_file(input_file, output_file, key)
    else:
        print("Неизвестный режим! Используйте 'encrypt' или 'decrypt'.")
        sys.exit(1)
