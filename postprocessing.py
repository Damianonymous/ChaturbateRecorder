import queue

from processing_worker import ProcessingWorker

class PostProcessing():
    def __init__(self, cmd, thread_count):
        if not cmd:
            return

        # TODO: Handle ffmpeg encoding within the app (with processing progress bar)
        self.cmd = cmd
        self.thread_count = thread_count
        self.queue = queue.Queue()
        self.workers = []

        self.start()

    def start(self):
        for i in range(0, self.thread_count):
            thread = ProcessingWorker(self.queue, self.cmd)
            self.workers.append(thread)
            thread.start()

    def add(self, item):
        self.queue.put(item)
