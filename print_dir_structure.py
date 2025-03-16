import os

# 제외할 폴더 이름 목록
EXCLUDE_FOLDERS = ["__pycache__", ".git", ".idea", ".venv", "node_modules", "venv"]


def print_directory_tree(start_path, prefix=""):
    # 현재 경로에 있는 폴더만 가져오기 + 필터링
    folders = [
        name
        for name in os.listdir(start_path)
        if os.path.isdir(os.path.join(start_path, name)) and name not in EXCLUDE_FOLDERS
    ]

    # 보기 좋게 정렬
    folders.sort()

    for index, folder in enumerate(folders):
        is_last = index == (len(folders) - 1)
        pointer = "└── " if is_last else "├── "

        print(prefix + pointer + folder)

        # 하위 폴더 재귀 호출
        new_prefix = prefix + ("    " if is_last else "│   ")
        print_directory_tree(os.path.join(start_path, folder), new_prefix)


root_dir = "."
print_directory_tree(root_dir)
