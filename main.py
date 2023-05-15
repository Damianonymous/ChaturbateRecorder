import time
import os
from tqdm import tqdm
from wakepy import set_keepawake

from wishlist import Wishlist
from monitor import Monitor
import config
import log

# Enable ANSI escape sequence processing in Windows
if os.name == 'nt':
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

screen_refresh = 1

settings = {}
threads = []

def cls():
    os.system('cls' if os.name == 'nt' else 'clear')

if __name__ == '__main__':
    cls()
    set_keepawake()

    settings = config.readConfig()
    try:
        wishlist = Wishlist(settings['wishlist'])
        wishlist.start()

        pbars = {
            'recorded': tqdm(desc='No recordings yet', bar_format='{desc}'),
            'processing': [],
            'recording': {}
        }

        app = Monitor(wishlist, pbars)
        app.start()

        i = 1
        if app.postprocess:
            for processing_thread in app.postprocess.workers:
                processing_pbar = tqdm(desc=f'Processing #{i:02d}', total=100, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}{postfix}')
                processing_pbar.display('Waiting')
                processing_thread.setPbar(processing_pbar)
                pbars['processing'].append(processing_pbar)
            i += 1

        # TODO: Key press to force-refresh models?

        while True:
            for i in range(settings['interval'], 0, -screen_refresh):
                time.sleep(screen_refresh)

                if len(app.done) > 0:
                    recorded_models = set(recording['model'] for recording in app.done)
                    status_message = f"{len(app.done)} recorded models: {', '.join(recorded_models)}"
                    if app.postprocess:
                        status_message += f" ({app.postprocess.queue.qsize()} queued for processing)"
                    pbars['recorded'].set_description(status_message    )

                # Update processing progress bars - done already
                # for processing_thread in app.postprocess.workers:

                if len(app.recording_threads) > 0:
                    for model_thread in app.recording_threads.values():
                        file_info = model_thread.info()
                        duration = file_info['duration']
                        file_size = file_info['file_size'] / 1024 / 1024
                        duration_in_minutes = duration.total_seconds() / 60
                        model_thread.pbar.n = min(duration_in_minutes, model_thread.max_duration)
                        model_thread.pbar.set_postfix({'size': f'>{file_size:>7.2f}Mb'})

    except KeyboardInterrupt:
        pass
    except Exception as e:
        log.exception(e)

    # cls()
    if len(app.done) > 0:
        print(f'Completed {len(app.done)} recordings:')
        for done in app.done:
            print(f'[{(done["duration"] / 60):3.0f} minutes] {done["resolution"]} {done["path"]} ({done["file_size_mb"]:.2f}Mb at {(done["total_bitrate"] / 1024):.0f}kbps)')
