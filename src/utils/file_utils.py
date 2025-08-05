def read_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='latin-1') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def write_file(file_path, content):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        print(f"Error writing to {file_path}: {e}")

def list_code_files(directory, extensions):
    from pathlib import Path
    code_files = []
    for file_path in Path(directory).rglob('*'):
        if file_path.suffix in extensions and file_path.is_file() and 'node_modules' not in str(file_path):
            code_files.append(file_path)
    return code_files