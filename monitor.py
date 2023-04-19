import threading
import time
import os
import ffmpeg
from tqdm import tqdm

from model import Model
from postprocessing import PostProcessing
import config


settings = config.readConfig()

class Monitor(threading.Thread):
    def __init__(self, wishlist, pbars):
        threading.Thread.__init__(self, daemon=True)
        self.lock = threading.Lock()

        self.wishlist = wishlist
        self.pbars = pbars
        self.monitoring_threads = {}
        self.recording_threads = {}
        self.done = []

        self.postprocess = None
        if settings['postProcessingCommand']:
            self.postprocess = PostProcessing(settings['postProcessingCommand'], settings['postProcessingThreads'] or 2)

    def isHandled(self, model):
        return self.isMonitored(model) or self.isRecording(model)

    def isMonitored(self, model):
        return model in (model for model in self.monitoring_threads.keys())

    def isRecording(self, model):
        return model in (model for model in self.recording_threads.keys())

    def startRecording(self, modelThread):
        self.lock.acquire()
        self.recording_threads[modelThread.model] = modelThread
        del self.monitoring_threads[modelThread.model]
        self.lock.release()

        self.attachPbar(modelThread)

    def attachPbar(self, modelThread):
        modelPbar = tqdm(
            desc=f'Recording {modelThread.model:32s}',
            total=modelThread.max_duration,
            bar_format='{desc} |{bar}| {elapsed}{postfix}',
            leave=False
        )
        self.pbars['recording'][modelThread.model] = modelPbar
        modelThread.pbar = modelPbar

    def stopRecording(self, modelThread):
        self.lock.acquire()
        self.monitoring_threads[modelThread.model] = modelThread
        if modelThread.model in self.recording_threads:
            del self.recording_threads[modelThread.model]

        self.lock.release()

        if modelThread.model in self.pbars['recording']:
            self.pbars['recording'][modelThread.model].clear()
            self.pbars['recording'][modelThread.model].close()
            del self.pbars['recording'][modelThread.model]

        if os.path.isfile(modelThread.file) and os.path.getsize(modelThread.file) > 1024:
            self.processRecording(modelThread.model, modelThread.file)

    def processRecording(self, model, file):
        if self.postprocess:
            self.postprocess.add({'model': model, 'path': file})

        probe = ffmpeg.probe(file)
        file_size_mb = os.path.getsize(file) / 1024 / 1024
        video = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        audio = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
        recording = {
            'model': model,
            'path': file,
            'file_size': os.path.getsize(file),
            'file_size_mb': file_size_mb,
            'duration': float(probe['format']['duration']),
            'width': int(video['width']),
            'height': int(video['height']),
            'resolution': f"{video['width']}x{video['height']}",
            'video_bitrate': int(video['bit_rate']) if 'bit_rate' in video else (file_size_mb / (float(probe['format']['duration']) * .45)),
            'video_codec': f"{video['codec_name']} - {video['codec_long_name']}",
            'frame_rate': video['r_frame_rate'],
            'audio_codec': f"{audio['codec_name']} - {audio['codec_long_name']}",
            'audio_bitrate': int(audio['bit_rate']),
            'format': f"{probe['format']['format_name']} - {probe['format']['format_long_name']}",
            'total_bitrate': int(probe['format']['bit_rate']),
        }

        self.done.append(recording)

    def stopMonitoring(self, model):
        self.lock.acquire()
        self.monitoring_threads[model].running = False
        self.monitoring_threads[model].join()
        del self.monitoring_threads[model]
        self.lock.release()

    def startMonitoring(self, model):
        thread = Model(model, self)
        thread.daemon = True
        thread.start()

        self.lock.acquire()
        self.monitoring_threads[model] = thread
        self.lock.release()

    def cleanThreads(self):
        self.lock.acquire()
        models = list(self.recording_threads.keys())
        self.lock.release()

        for model in models:
            if model not in self.wishlist.wishlist:
                self.recording_threads[model].stopRecording()
                self.stopMonitoring(model)

        # models = self.recording_threads.keys()
        # for model in models:
        #     if not self.recording_threads[model].is_alive():
        #         self.recording_threads[model].stopRecording()

        # models = self.monitoring_threads.keys()
        # for model in models:
        #     if not self.monitoring_threads[model].is_alive():
        #         self.stopMonitoring(model)


    def loop(self):
        # Kill off stopped threads (will be recreated in the next step if needed)
        self.cleanThreads()

        # Start a thread for each model in our wishlist
        for model in self.wishlist.wishlist:
            if not self.isHandled(model):
                self.startMonitoring(model)

    def run(self):
        while True:
            self.loop()
            time.sleep(1)
