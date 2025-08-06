from pathlib import Path
from src.utils.file_utils import extract_code_files, read_file
from src.utils.language_utils import detect_language

class CodebaseVectorizer:
    def __init__(self, codebase_path, embedder=None, text_splitter=None, code_extensions=None, batch_size=16):
        self.codebase_path = Path(codebase_path)
        self.embedder = embedder
        self.text_splitter = text_splitter
        self.code_extensions = code_extensions
        self.batch_size = batch_size

    def process_file(self, file_path):
        content = read_file(file_path)
        chunks = self.text_splitter.split_text(content)
        return [{'content': chunk, 'metadata': self.create_metadata(file_path, i, chunk)} for i, chunk in enumerate(chunks)]

    def create_metadata(self, file_path, chunk_id, chunk):
        return {
            'file_path': str(file_path),
            'relative_path': str(file_path.relative_to(self.codebase_path)),
            'file_extension': file_path.suffix,
            'language': detect_language(file_path.suffix),
            'chunk_id': chunk_id,
            'chunk_size': len(chunk)
        }

    def vectorize_codebase(self):
        print(f"Starting vectorization of {self.codebase_path}")
        code_files = extract_code_files(self.codebase_path, self.code_extensions)

        print(f"Found {len(code_files)} code files")
        all_documents = [doc for file_path in code_files for doc in self.process_file(file_path)]
        print(f"Created {len(all_documents)} code chunks")

        texts = [doc['content'] for doc in all_documents]
        metadatas = [doc['metadata'] for doc in all_documents]

        return (texts, metadatas)

