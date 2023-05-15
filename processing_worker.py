import subprocess
import time
import threading
import os
import json
from tqdm import tqdm
from mmisp import process

class ProcessingWorker(threading.Thread):
    def __init__(self, queue, cmd):
        super().__init__()
        self.daemon = True

        self.cmd = cmd
        self.queue = queue
        self.sleep = 1 # 60
        self.current_file = None
        self.pbar = None

    def setPbar(self, pbar: tqdm):
        self.pbar = pbar

    def update_progress(self, percent_complete):
        if isinstance(self.pbar, tqdm):
            self.pbar.n = percent_complete
            self.pbar.refresh()

    def run(self):
        while True:
            while self.queue.empty():
                time.sleep(self.sleep)

            parameters = self.queue.get()
            self.current_file = parameters['path']

            if self.cmd == 'mmisp':
                with open('process.json', 'r') as f:
                    process.run(parameters['path'],
                        json.load(f),
                        progress_callback=self.update_progress)
            else:
                replacements = {
                    'path': parameters['path'],
                    'filename': os.path.split(parameters['path'])[-1],
                    'directory': os.path.dirname(parameters['path']),
                    'file': os.path.splitext(os.path.split(parameters['path'])[-1])[0],
                    'model': parameters['model']
                }
                cmd = self.cmd.format(replacements)
                subprocess.call(cmd.split())

            self.pbar.clear()
            self.pbar.display('Waiting')
            self.current_file = None
