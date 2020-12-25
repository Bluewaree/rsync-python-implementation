import socket
from _thread import *
import threading
import sys
import json
import os
import time
from pathlib import Path
import pickle

from server.helpers import (
    adler32_chunk,
    md5_chunk,
    checksums_file,
    delete_file,
    create_folder,
    delete_folder,
    write_blocks_to_file,
)
from server.constants import BLOCK_SIZE


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
    absolute_path = f"{absolute_folder_path}/{path}"
    if action == "file_created":
        handle_file_creation(c, absolute_path)
    if action == "file_updated":
        handle_file_update(c, absolute_path, absolute_folder_path, path)
    if action == "file_deleted":
        delete_file(c, absolute_path)
    if action == "folder_created":
        create_folder(c, absolute_path)
    if action == "folder_deleted":
        delete_folder(c, absolute_path)
    c.close()


if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else '.'
    HOST, PORT = "localhost", 9999
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(5)
    print("socket is listening")
    while True:
        c, addr = s.accept()
        print('Connected to :', addr[0], ':', addr[1])
        start_new_thread(client_handler, (c, path))
    s.close()
