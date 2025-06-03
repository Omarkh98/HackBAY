# file_event_queue.py

import queue

# Shared queue for communicating file change results from watcher to Streamlit
file_event_queue = queue.Queue()