import aiofiles
import secrets
from pathlib import Path
from fastapi import UploadFile

# Определяем базовую директорию для загрузок
UPLOADS_DIR = Path("uploads")
AVATARS_DIR = UPLOADS_DIR / "avatars"

# Убедимся, что директории существуют при старте
AVATARS_DIR.mkdir(parents=True, exist_ok=True)


async def save_avatar(file: UploadFile, subscriber_id: int) -> str:
    """
    Сохраняет файл аватара на диск.
    Возвращает уникальное имя файла.
    """
    # Получаем расширение файла, например ".jpg"
    file_extension = Path(file.filename).suffix

    # Генерируем безопасное и уникальное имя файла
    # Например: subscriber_15_a8b2cde3.jpg
    token_name = secrets.token_hex(8)
    file_name = f"subscriber_{subscriber_id}_{token_name}{file_extension}"

    # Полный путь для сохранения файла
    file_path = AVATARS_DIR / file_name

    # Асинхронно записываем содержимое файла на диск
    async with aiofiles.open(file_path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)

    # Возвращаем только имя файла для сохранения в БД
    return file_name