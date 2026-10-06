import os

MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}

def validate_file(file_path: str, original_filename: str) -> None:
    if not os.path.exists(file_path):
        raise ValueError("File does not exist on disk.")

    file_size = os.path.getsize(file_path)
    if file_size > MAX_FILE_SIZE_BYTES:
        raise ValueError(f"File size ({file_size / (1024*1024):.2f}MB) exceeds limit of {MAX_FILE_SIZE_MB}MB.")

    ext = os.path.splitext(original_filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file extension '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")
