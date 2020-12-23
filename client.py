import sys
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import os


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else '.'
    patterns = "*"
    ignore_patterns = ["*~"]
    ignore_directories = False
    case_sensitive = True
    observer = Observer()
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
