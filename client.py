import sys
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import os
from pathlib import Path
from datetime import datetime
import socket
import json
import threading
from _thread import *
import pickle
import re

from client.helpers import adler32_chunk, md5_chunk, _get_block_list
from client.constants import BLOCK_SIZE, EVENT_LIMIT


def handle_folder_actions(action, event_path, src_path=None):
    data = json.dumps({"action": action, "path": event_path}).encode("utf-8")
    s = initiate_socket()
    s.send(data)
    if action == "file_updated":
        msg = s.recv(BLOCK_SIZE)
        checksums = msg
        while msg:
            try:
                s.settimeout(2.0)
                msg = s.recv(BLOCK_SIZE)
            except socket.timeout:
                break
            s.settimeout(None)
            checksums += msg
        checksums = json.loads(checksums.decode("utf-8"))
        blocks = pickle.dumps(_get_block_list(src_path, checksums))
        s.sendall(blocks)
    if action == "file_created":
        time.sleep(1)
        with open(src_path, "rb") as f:
            data = f.read()
            s.sendall(data)
            f.close()
    s.close()


class FileEventHandler(PatternMatchingEventHandler):
    def __init__(self, monitored_folder, *args, **kwargs):
        super(FileEventHandler, self).__init__(*args, **kwargs)
        self.monitored_folder = monitored_folder
        self.rate_limit = {}

    def on_any_event(self, event):
        striped_src_path = re.sub(r'^/private', '', event.src_path)
        event_path = striped_src_path.replace(self.monitored_folder, '')
        if event.event_type=="created" and not event.is_directory: # On file create
            curr = datetime.now()
            self.rate_limit[event_path] = curr
            start_new_thread(handle_folder_actions, ("file_created", event_path, striped_src_path))
        elif event.event_type=="modified" and not event.is_directory: # On file update
            curr = datetime.now()
            allow = True
            if event_path in self.rate_limit and (curr - self.rate_limit[event_path]).seconds<=EVENT_LIMIT:
                allow = False
            self.rate_limit[event_path] = curr
            if allow:
                try: # On file creation or update
                    open(striped_src_path, 'r').close()
                    start_new_thread(handle_folder_actions, ("file_updated", event_path, striped_src_path))
                except OSError: # Deletes file if not exists
                    start_new_thread(handle_folder_actions, ("file_deleted", event_path,))
        elif event.event_type=="deleted" and not event.is_directory: # On file deletion
            start_new_thread(handle_folder_actions, ("file_deleted", event_path,))
        elif event.event_type=="created" and event.is_directory: # On folder creation
            if os.path.exists(striped_src_path):
                if len(os.listdir(striped_src_path)) == 0:
                    start_new_thread(handle_folder_actions, ("folder_created", event_path,))
            else: # Deletes folder if not exists
                start_new_thread(handle_folder_actions, ("folder_deleted", event_path,))
        elif event.event_type=="deleted": # On folder deletion
            start_new_thread(handle_folder_actions, ("folder_deleted", event_path,))


def initial_sync(path):
    for pth, subdirs, files in os.walk(path):
        start_new_thread(handle_folder_actions, ("bulk_create_folders", subdirs,))
        for name in files:
            file_path = os.path.join(path, name)
            start_new_thread(handle_folder_actions, ("file_created", name, file_path))


def initiate_socket():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    HOST, PORT = "localhost", 9999
    s.connect((HOST, PORT))
    return s


def initiate_filehandler(path):
    absolute_path = f"{str(Path(path).absolute())}/"
    start_new_thread(initial_sync, (absolute_path,))
    patterns = "*"
    ignore_patterns = ["*~"]
    ignore_directories = False
    case_sensitive = True
    event_handler = FileEventHandler(absolute_path, ignore_patterns=["*~"])
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else '.'
    initiate_filehandler(path)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
