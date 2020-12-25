import json
import pickle
import time
import socket
import os
from _thread import *

from .constants import BLOCK_SIZE
from .helpers import initiate_socket, _get_block_list

def handle_file_creation(s, src_path):
    time.sleep(1)
    with open(src_path, "rb") as f:
        data = f.read()
        s.sendall(data)
        f.close()

def handle_file_update(s, src_path):
    data = s.recv(BLOCK_SIZE)
    checksums = data
    while data:
        try:
            s.settimeout(2.0)
            data = s.recv(BLOCK_SIZE)
        except socket.timeout:
            break
        s.settimeout(None)
        checksums += data
    checksums = json.loads(checksums.decode("utf-8"))
    blocks = pickle.dumps(_get_block_list(src_path, checksums))
    s.sendall(blocks)

def handle_folder_actions(action, event_path, src_path=None):
    data = json.dumps({"action": action, "path": event_path}).encode("utf-8")
    s = initiate_socket()
    s.send(data)
    if action == "file_updated":
        data = s.recv(BLOCK_SIZE)
        file_exists = json.loads(data.decode())["file_exists"] # Check if file exists on server to either perform a create or update
        if file_exists:
            handle_file_update(s, src_path)
        else:
            handle_file_creation(s, src_path)
    if action == "file_created":
        handle_file_creation(s, src_path)
    s.close()

def handle_folder_initial_sync(path):
    for pth, subdirs, files in os.walk(path):
        start_new_thread(handle_folder_actions, ("bulk_create_folders", subdirs,))
        for name in files:
            file_path = os.path.join(path, name)
            start_new_thread(handle_folder_actions, ("file_created", name, file_path))

