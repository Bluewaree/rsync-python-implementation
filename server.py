import socket
from _thread import *
import threading
import sys
from server.helpers import (
    adler32_chunk,
    md5_chunk,
    checksums_file,
)
from server.constants import BLOCK_SIZE
import json
import os
import time
from pathlib import Path
import pickle
import shutil


print_lock = threading.Lock()
def write_blocks_to_file(blocks, absolute_file_path, tmp_file):
    if os.path.exists(absolute_file_path):
        with open(absolute_file_path, "rb") as ft:
            with open(tmp_file, "wb") as f:
                for block in blocks:
                    if isinstance(block, int):
                        ft.seek(block * BLOCK_SIZE)
                        content = ft.read(BLOCK_SIZE)
                        f.write(content)
                    else:
                        f.write(block)

                f.close()
                os.remove(absolute_file_path)
                os.rename(tmp_file, absolute_file_path)
            ft.close()
    else:
        with open(absolute_file_path, "wb") as f:
            for block in blocks:
                f.write(block)


def handle_file_update(c, absolute_file_path, absolute_folder_path, file_path):
    checksums = checksums_file(absolute_file_path)
    data = json.dumps(checksums).encode("utf-8")
    c.send(data)
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


def handle_file_deletion(c, absolute_file_path):
    try:
        os.remove(absolute_file_path)
    except OSError as e:
        print ("Error: %s - %s." % (e.filename, e.strerror))


def handle_folder_creation(c, absolute_path):
    try:
        os.makedirs(absolute_path)
    except FileExistsError:
        print ("Folder exists.")


def handle_folder_deletion(c, absolute_path):
    try:
        shutil.rmtree(absolute_path)
    except OSError as e:
        print ("Error: %s - %s." % (e.filename, e.strerror))


def client_handler(c, folder_path):
    absolute_folder_path = Path(folder_path).absolute()
    data = c.recv(BLOCK_SIZE)
    data = json.loads(data.decode())
    path = data["path"]
    action = data["action"]
    absolute_path = f"{absolute_folder_path}/{path}"
    if action == "file_updated":
        handle_file_update(c, absolute_path, absolute_folder_path, path)
    if action == "file_deleted":
        delete_file(c, absolute_path)
    if action == "folder_created":
        create_folder(c, absolute_path)
    if action == "folder_deleted":
        deleted_folder(c, absolute_path)
    c.close()


if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else '.'
    HOST, PORT = "localhost", 9999
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(5)
    print("socket is listening")
    while True:
        c, addr = s.accept()
        print('Connected to :', addr[0], ':', addr[1])
        start_new_thread(client_handler, (c, path))
    s.close()
