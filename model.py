import datetime
import threading
import os
import time
import streamlink
import requests

import config
import log

class Model(threading.Thread):
    def __init__(self, model, app):
        threading.Thread.__init__(self)
        self._stopevent = threading.Event()
        self.running = True

        settings = config.readConfig()

        self.model = model
        self.hls_cache_file = f'logs/stream_{self.model}.txt'
        self.start_time = None
        self.app = app
        self.file = None
        self.directory = settings['save_directory']
        self.max_duration = settings['max_duration'] or 0
        self.online = None
        self.hls_source = None
        self.pbar = None

    def generateFilename(self):
        settings = config.readConfig()
        now = datetime.datetime.now()
        self.file = settings['directory_structure'].format(
            path=self.directory,
            model=self.model,
            seconds=now.strftime("%S"),
            minutes=now.strftime("%M"),
            hour=now.strftime("%H"),
            day=now.strftime("%d"),
            month=now.strftime("%m"),
            year=now.strftime("%Y")
        )

    def run(self):
        settings = config.readConfig()

        while self.running:
            if not self.isOnline():
                # It was recording - stop now
                if self.online:
                    self.stopRecording()

                time.sleep(settings['interval'])
                continue

            # Shouldn't happen? Another thread recording the same model?
            if self.app.isRecording(self.model):
                time.sleep(1)
                continue

            # Model is online - start recording
            self.startRecording()


    def info(self):
        ret = {
            'model': self.model,
            'online': self.online,
            'start_time': self.start_time,
        }

        ret['duration'] = datetime.datetime.now() - self.start_time
        ret['file_size'] = os.path.getsize(self.file)

        return ret

    def isOnline(self):
        if self.getCachedStream():
            return True

        try:
            model_url = f'https://chaturbate.com/api/chatvideocontext/{self.model}/'
            resp = requests.get(model_url)

            if resp.headers.get('content-type') != 'application/json':
                log.error(f'{self.model} couldn\'t be checked - potential CloudFlare filtering')
                return False

            hls_url = ''
            if 'hls_source' in resp.json():
                hls_url = resp.json()['hls_source']
            if len(hls_url):
                self.hls_source = hls_url
                self.cacheStream(hls_url)

                return True
            else:
                self.hls_source = True
                self.clearCache()
                return False
        except Exception as e:
            log.exception(f'EXCEPTION: {e}')
            return False

    def startRecording(self):
        self.online = True
        self.generateFilename()
        self._stopevent.clear()
        self.start_time = datetime.datetime.now()

        try:
            session = streamlink.Streamlink()
            streams = session.streams(f'hlsvariant://{self.hls_source}')
            stream = streams['best']
            with stream.open() as hls_stream:
                os.makedirs(os.path.join(self.directory, self.model), exist_ok=True)

                f = open(self.file, 'wb')
                self.app.startRecording(self)

                while not (self._stopevent.isSet() or os.fstat(f.fileno()).st_nlink == 0):
                    try:
                        # Break file into 1h chunks
                        if self.max_duration:
                            delta = datetime.datetime.now() - self.start_time
                            minutes = delta.total_seconds() / 60
                            if minutes > self.max_duration:
                                self.app.processRecording(self.model, self.file, self.info()['duration'])
                                self.start_time = datetime.datetime.now()
                                self.generateFilename()
                                f = open(self.file, 'wb')

                        data = hls_stream.read(1024)
                        f.write(data)
                    except:
                        hls_stream.close()
                        self.clearCache()
                        break

        except Exception as e:
            log.exception(f'EXCEPTION: {e}')
        finally:
            if self.online:
                self.stopRecording()

    def cacheStream(self, stream):
        with open(self.hls_cache_file, 'w') as f:
            f.write(stream)

    def getCachedStream(self):
        if os.path.isfile(self.hls_cache_file):
            with open(self.hls_cache_file, 'r') as f:
                hls_url = f.readline()
                if len(hls_url):
                    self.hls_source = hls_url
                    return True

        return False

    def clearCache(self):
        if os.path.isfile(self.hls_cache_file):
            os.remove(self.hls_cache_file)

    def stopRecording(self):
        self.online = False
        self.app.stopRecording(self)
        self.start_time = None
        self._stopevent.set()
        self.hls_source = None
        self.pbar = None

        # If file is too small, delete it
        if self.file:
            try:
                if os.path.isfile(self.file) and os.path.getsize(self.file) <= 1024:
                    os.remove(self.file)
            except Exception as e:
                log.exception(f'EXCEPTION: {e}')

            self.file = None
