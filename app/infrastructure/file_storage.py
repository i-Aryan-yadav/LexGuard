import os
import aiofiles
from uuid import uuid4
from fastapi import UploadFile

UPLOAD_DIR = "contracts/uploaded_files"

class FileStorage:
    def __init__(self):
        os.makedirs(UPLOAD_DIR, exist_ok=True)

    async def save_file(self, file: UploadFile) -> str:
        file_ext = file.filename.split(".")[-1]
        file_name = f"{uuid4()}.{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, file_name)
        
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
            
        return file_path
