import os
import uuid
from fastapi import UploadFile, HTTPException
from PIL import Image
import io
from app.config import settings


def save_upload_file(upload_file: UploadFile) -> str:
    file_ext = os.path.splitext(upload_file.filename)[1].lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Недопустимый формат файла. Разрешенные: {settings.ALLOWED_EXTENSIONS}")

    filename = f"{uuid.uuid4()}{file_ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)

    contents = upload_file.file.read()
    if len(contents) > settings.MAX_FILE_SIZE:
        raise HTTPException(400, f"Файл слишком большой. Максимум: {settings.MAX_FILE_SIZE // 1024 // 1024}MB")

    if file_ext in ['.jpg', '.jpeg', '.png']:
        image = Image.open(io.BytesIO(contents))
        image.thumbnail((1200, 1200))
        image.save(filepath, optimize=True, quality=85)
    else:
        with open(filepath, "wb") as f:
            f.write(contents)

    return filename