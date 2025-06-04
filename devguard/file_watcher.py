# file_watcher.py

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
from dotenv import load_dotenv
from tools.library_license_checker.main import check_licenses
from tools.internal_guideline_compliance_checker.main import check_compliance
from file_event_queue import file_event_queue

load_dotenv()

ALLOWED_FILE_DIR = os.getenv("ALLOWED_FILE_DIR", ".")

observer_instance = None  # Global to prevent re-adding

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback

    def on_modified(self, event):
        print("🚨 ON MODIFIED", event)
        if not event.is_directory:
            self.callback(event.src_path)

def start_file_watcher(on_file_change):
    global observer_instance

    if observer_instance is not None and observer_instance.is_alive():
        print("🔁 Watcher already running.")
        return

    event_handler = FileChangeHandler(on_file_change)
    observer_instance = Observer()
    observer_instance.schedule(event_handler, path=ALLOWED_FILE_DIR, recursive=True)
    observer_instance.start()
    print(f"👀 Watching for changes in: {ALLOWED_FILE_DIR}")