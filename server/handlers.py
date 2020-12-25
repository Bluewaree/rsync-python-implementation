import json
import os
from pathlib import Path
import pickle

from .helpers import (
    adler32_chunk,
    md5_chunk,
    checksums_file,
    delete_file,
    create_folder,
    delete_folder,
    write_blocks_to_file,
)
from .constants import BLOCK_SIZE


def handle_file_update(c, absolute_file_path, absolute_folder_path, file_path):
    checksums = checksums_file(absolute_file_path)
    data = json.dumps(checksums).encode("utf-8")
    c.sendall(data)
    blocks = []
    while True:
        data = c.recv(BLOCK_SIZE)
        if not data:
            break
        blocks.append(data)
    blocks= pickle.loads(b"".join(blocks))
    file_name = os.path.splitext(file_path)[0].split("/")[-1]
    extention = os.path.splitext(file_path)[1]
    tmp_file = f"{absolute_folder_path}/tmp_{file_name}{extention}"
    write_blocks_to_file(blocks, absolute_file_path, tmp_file)


def handle_file_creation(c, absolute_path):
    file_data = []
    with open(absolute_path, "wb") as f:
        while True:
            data = c.recv(BLOCK_SIZE)
            if not data:
                break
            f.write(data)
        f.close()

def client_handler(c, folder_path):
    absolute_folder_path = Path(folder_path).absolute()
    data = c.recv(BLOCK_SIZE)
    data = json.loads(data.decode())
    path = data["path"]
    action = data["action"]
    if action == "bulk_create_folders":
        for folder_path in path:
            create_folder(c, f"{absolute_folder_path}/{folder_path}")
        return
    absolute_path = f"{absolute_folder_path}/{path}"
    if action == "file_created":
        handle_file_creation(c, absolute_path)
    if action == "file_updated":
        file_exists = Path(absolute_path).exists()
        data = json.dumps({"file_exists": file_exists}).encode("utf-8")
        c.send(data)
        if file_exists:
            handle_file_update(c, absolute_path, absolute_folder_path, path)
        else:
            handle_file_creation(c, absolute_path)
    if action == "file_deleted":
        delete_file(c, absolute_path)
    if action == "folder_created":
        create_folder(c, absolute_path)
    if action == "folder_deleted":
        delete_folder(c, absolute_path)
    c.close()
