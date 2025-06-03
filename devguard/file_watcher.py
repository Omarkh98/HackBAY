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
        if not event.is_directory:
            self.callback(event.src_path)

def on_file_change(file_path):
    print(f"📂 Detected file change: {file_path}")
    file_ext = os.path.splitext(file_path)[1]
    results = []

    # Run license checker
    license_result = check_licenses(file_path)
    results.append(("📜 Library License Check", license_result))

    # Run compliance check for supported files
    if file_ext in [".py", ".xml", ".java"]:
        compliance_result = check_compliance(file_path, output_format="json")
        results.append(("📏 Guideline Compliance Check", compliance_result))

    # Add result to shared queue for Streamlit to pick up
    file_event_queue.put({
        "file": file_path,
        "results": results
    })

def start_file_watcher():
    global observer_instance

    if observer_instance is not None and observer_instance.is_alive():
        print("🔁 Watcher already running.")
        return

    event_handler = FileChangeHandler(on_file_change)
    observer_instance = Observer()
    observer_instance.schedule(event_handler, path=ALLOWED_FILE_DIR, recursive=True)
    observer_instance.start()
    print(f"👀 Watching for changes in: {ALLOWED_FILE_DIR}")