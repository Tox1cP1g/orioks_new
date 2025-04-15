def count_byte_frequencies(filename):
    byte_counts = [0] * 256
    total_bytes = 0

    with open(filename, "rb") as file:
        while byte := file.read(1):  # Читаем по 1 байту
            byte_counts[byte[0]] += 1
            total_bytes += 1

    if total_bytes == 0:
        print("Файл пуст!")
        return

    print("Байт | Частота")
    print("-----------------")
    for i in range(256):
        if byte_counts[i] > 0:
            frequency = byte_counts[i] / total_bytes
            print(f"{i:3}  | {frequency:.6f}")


filename = "тест.doc"
count_byte_frequencies(filename)
