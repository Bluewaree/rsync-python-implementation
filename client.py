import sys
import time
from watchdog.observers import Observer
from pathlib import Path
import threading
from _thread import *

from client.handlers import handle_folder_initial_sync
from client.models import FileEventHandler


def initiate_filehandler(path):
    absolute_path = f"{str(Path(path).absolute())}/"
    start_new_thread(handle_folder_initial_sync, (absolute_path,))
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
