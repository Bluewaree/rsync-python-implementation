import sys
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import os


class FileEventHandler(PatternMatchingEventHandler):
    def __init__(self, *args, **kwargs):
        super(FileEventHandler, self).__init__(*args, **kwargs)
        self.last_created = None

    def on_any_event(self, event):
        if event.event_type=="created" and not event.is_directory: # On file create, deletion, or update
            try: # On file creation or update
                open(event.src_path, 'r').close()
                pass
            except OSError: # On file deletion
                pass
        elif event.event_type=="created" and event.is_directory: # On folder creation
            if len(os.listdir(event.src_path)) == 0:
                pass
        elif event.event_type=="deleted": # On folder deletion
            pass


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else '.'
    patterns = "*"
    ignore_patterns = ["*~"]
    ignore_directories = False
    case_sensitive = True
    event_handler = FileEventHandler(ignore_patterns=["*~"])
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
