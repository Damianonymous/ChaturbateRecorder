import configparser
import os
import sys

mainDir = sys.path[0]

def readConfig():
    config = configparser.ConfigParser()
    config.read(mainDir + '/config.conf')
    settings = {
        'save_directory': config.get('paths', 'save_directory'),
        'directory_structure': config.get('paths', 'directory_structure').lower(),
        'wishlist': config.get('paths', 'wishlist'),
        'interval': int(config.get('settings', 'check_online_interval')),
        'max_duration': int(config.get('settings', 'max_duration_mins')),
        'postProcessingCommand': config.get('settings', 'postProcessingCommand'),
    }
    try:
        settings['postProcessingThreads'] = int(config.get('settings', 'postProcessingThreads'))
    except ValueError:
        if settings['postProcessingCommand'] and not settings['postProcessingThreads']:
            settings['postProcessingThreads'] = 1

    if not os.path.exists(f'{settings["save_directory"]}'):
        os.makedirs(f'{settings["save_directory"]}')

    return settings
