import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

class FileModifiedHandler(FileSystemEventHandler):
    def __init__(self, file_name, callback):
        self.file_name = file_name
        self.callback = callback
        self.path = os.path.dirname(file_name)

        # Set observer to watch for changes in the directory
        self.observer = Observer()
        self.observer.schedule(self, self.path, recursive=False)
        self.observer.start()
        self.observer.join()

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(self.file_name):
            self.callback()