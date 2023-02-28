import os
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

def start_monitoring(handle_event,playbook_path):
    # create an event handler and observer

    event_handler = FileSystemEventHandler()
    event_handler.on_modified = handle_event
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(playbook_path), recursive=True)

    # start the observer
    observer.start()

    # loop forever
    try:
        logging.info(f"Monitoring '{playbook_path}' for changes...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()