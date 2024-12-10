import os


def count_lines_in_folder(folder_path):
    total_lines = 0
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = sum(1 for _ in f)
                    total_lines += lines
                    print(f"{file}: {lines} lines")
            except Exception as e:
                print(f"Could not read {file}: {e}")
    print(f"Total lines: {total_lines}")


# Укажите путь к папке
folder_path = "/Users/kobelev/orioks_new/student_performance"
count_lines_in_folder(folder_path)
