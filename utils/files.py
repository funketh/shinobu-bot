import os

import aiofiles
import aiosqlite
from typing import Set

from CONSTANTS import DB_PATH, FILE_ROOT


async def make_file_path(file_name, extension):
    return os.path.join(FILE_ROOT, f'{file_name}{extension}')


async def create_file(contents, extension: str) -> int:
    async with aiosqlite.connect(DB_PATH) as connection:
        async with connection.cursor() as cursor:
            await cursor.execute('INSERT INTO file VALUES (NULL, ?)', [extension])
            id_ = cursor.lastrowid
            file_path = await make_file_path(id_, extension)
            if os.path.exists(file_path):
                print(file_path)
            async with aiofiles.open(file_path, 'wb') as file:
                await file.write(contents)
            await connection.commit()
    return id_


async def tag_file(file_id: int, tags: Set[str] = None):
    tags = tags or set()
    async with aiosqlite.connect(DB_PATH) as connection:
        async with connection.cursor() as cursor:
            for tag in tags:
                await cursor.execute(
                    'INSERT OR IGNORE INTO tag VALUES (?);',
                    [tag]
                )
                await cursor.execute(
                    'INSERT OR IGNORE INTO tagged_files VALUES ((?), LAST_INSERT_ROWID())',
                    [file_id]
                )
        await connection.commit()
