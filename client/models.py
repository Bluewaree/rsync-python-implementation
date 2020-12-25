import re
from pathlib import Path
from datetime import datetime
from watchdog.events import PatternMatchingEventHandler
from _thread import *
import os

from client.constants import EVENT_LIMIT
from client.handlers import handle_folder_actions

class FileEventHandler(PatternMatchingEventHandler):
    def __init__(self, monitored_folder, *args, **kwargs):
        super(FileEventHandler, self).__init__(*args, **kwargs)
        self.monitored_folder = monitored_folder
        self.rate_limit = {}

    def set_rate_limit_for_path(self, path, curr=datetime.now()):
        self.rate_limit[path] = curr

    def is_file_action_allowed(self, path):
        curr = datetime.now()
        is_allowed = True
        if path in self.rate_limit and (curr - self.rate_limit[path]).seconds<=EVENT_LIMIT:
            is_allowed = False
        self.set_rate_limit_for_path(path, curr)
        return is_allowed

    def get_event_args(self, event):
        absolute_path = re.sub(r'^/private', '', event.src_path)
        path_within_folder = absolute_path.replace(self.monitored_folder, '')
        return absolute_path, path_within_folder, event.event_type, event.is_directory

    def on_any_event(self, event):
        absolute_path, path_within_folder, event_type, is_directory = self.get_event_args(event)
        if event_type=="created" and not is_directory:
            self.set_rate_limit_for_path(path_within_folder)
            start_new_thread(handle_folder_actions, ("file_created", path_within_folder, absolute_path))
        elif event_type=="modified" and not is_directory:
            if self.is_file_action_allowed(path_within_folder):
                if Path(absolute_path).exists():
                    start_new_thread(handle_folder_actions, ("file_updated", path_within_folder, absolute_path))
                else:
                    start_new_thread(handle_folder_actions, ("file_deleted", path_within_folder,))
        elif event_type=="deleted" and not is_directory:
            start_new_thread(handle_folder_actions, ("file_deleted", path_within_folder,))
        elif event_type=="created" and is_directory:
            if os.path.exists(absolute_path):
                if len(os.listdir(absolute_path)) == 0:
                    start_new_thread(handle_folder_actions, ("folder_created", path_within_folder,))
            else:
                start_new_thread(handle_folder_actions, ("folder_deleted", path_within_folder,))
        elif event_type=="deleted":
            start_new_thread(handle_folder_actions, ("folder_deleted", path_within_folder,))

