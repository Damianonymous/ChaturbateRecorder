import time, datetime, os, sys, requests, configparser, re, subprocess
if os.name == 'nt':
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
from queue import Queue
from livestreamer import Livestreamer
from threading import Thread

Config = configparser.ConfigParser()
Config.read(sys.path[0] + "/config.conf")
save_directory = Config.get('paths', 'save_directory')
wishlist = Config.get('paths', 'wishlist')
interval = int(Config.get('settings', 'checkInterval'))
genders = re.sub(' ', '', Config.get('settings', 'genders')).split(",")
directory_structure = Config.get('paths', 'directory_structure').lower()
postProcessingCommand = Config.get('settings', 'postProcessingCommand')
try:
    postProcessingThreads = int(Config.get('settings', 'postProcessingThreads'))
except ValueError:
    pass
completed_directory = Config.get('paths', 'completed_directory').lower()

def now():
    return '[' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ']'

recording = []
wanted = []

def startRecording(model):
    global postProcessingCommand
    global processingQueue
    try:
        result = requests.get('https://chaturbate.com/api/chatvideocontext/{}/'.format(model)).json()
        session = Livestreamer()
        session.set_option('http-headers', "referer=https://www.chaturbate.com/{}".format(model))
        streams = session.streams("hlsvariant://{}".format(result['hls_source'].rsplit('?')[0]))
        stream = streams["best"]
        fd = stream.open()
        now = datetime.datetime.now()
        filePath = directory_structure.format(path=save_directory, model=model, gender=result['broadcaster_gender'],
                                              seconds=now.strftime("%S"),
                                              minutes=now.strftime("%M"), hour=now.strftime("%H"),
                                              day=now.strftime("%d"),
                                              month=now.strftime("%m"), year=now.strftime("%Y"))
        directory = filePath.rsplit('/', 1)[0]+'/'
        if not os.path.exists(directory):
            os.makedirs(directory)
        if model in recording: return
        with open(filePath, 'wb') as f:
            recording.append(model)
            while model in wanted:
                try:
                    data = fd.read(1024)
                    f.write(data)
                except:
                    f.close()
                    break
        if postProcessingCommand:
            processingQueue.put({'model':model, 'path':filePath, 'gender':gender})
        elif completed_directory:
            finishedDir = completed_directory.format(path=save_directory, model=model,
                        gender=gender, seconds=now.strftime("%S"),
                        minutes=now.strftime("%M"),hour=now.strftime("%H"), day=now.strftime("%d"),
                        month=now.strftime("%m"), year=now.strftime("%Y"))

            if not os.path.exists(finishedDir):
                os.makedirs(finishedDir)
            os.rename(filePath, finishedDir+'/'+filePath.rsplit['/',1][0])
    except: pass
    finally:
        if model in recording:recording.remove(model)
def postProcess():
    global processingQueue
    global postProcessingCommand
    while True:
        while processingQueue.empty():
            time.sleep(1)
        parameters = processingQueue.get()
        model = parameters['model']
        path = parameters['path']
        filename = path.rsplit('/', 1)[1]
        gender = parameters['gender']
        directory = path.rsplit('/', 1)[0]+'/'
        subprocess.run(postProcessingCommand.split() + [path, filename, directory, model, gender])

def getOnlineModels():
    online = []
    global wanted
    for gender in genders:
        try:
            data = {'categories': gender, 'num': 127}
            result = requests.post("https://roomlister.stream.highwebmedia.com/session/start/", data=data).json()
            length = len(result['rooms'])
            online.extend([m['username'].lower() for m in result['rooms']])
            data['key'] = result['key']
            while length == 127:
                result = requests.post("https://roomlister.stream.highwebmedia.com/session/next/", data=data).json()
                length = len(result['rooms'])
                data['key'] = result['key']
                online.extend([m['username'].lower() for m in result['rooms']])
        except:
            break
    f = open(wishlist, 'r')
    wanted =  list(set(f.readlines()))
    wanted = [m.strip('\n').split('chaturbate.com/')[-1].lower().strip().replace('/', '') for m in wanted]
    #wantedModels = list(set(wanted).intersection(online).difference(recording))
    '''new method for building list - testing issue #19 yet again'''
    wantedModels = [m for m in (list(set(wanted))) if m in online and m not in recording]
    for theModel in wantedModels:
            thread = Thread(target=startRecording, args=(theModel,))
            thread.start()
    f.close()


if __name__ == '__main__':
    AllowedGenders = ['female', 'male', 'trans', 'couple']
    for gender in genders:
        if gender.lower() not in AllowedGenders:
            print(gender, "is not an acceptable gender, options are: female, male, trans, and couple - please correct your config file")
            exit()
    genders = [a.lower()[0] for a in genders]
    print()
    if postProcessingCommand != "":
        processingQueue = Queue()
        postprocessingWorkers = []
        for i in range(0, postProcessingThreads):
            t = Thread(target=postProcess)
            postprocessingWorkers.append(t)
            t.start()
    sys.stdout.write("\033[F")
    while True:
        sys.stdout.write("\033[K")
        print( now(),"{} model(s) are being recorded. Getting list of online models now".format(len(recording)))
        sys.stdout.write("\033[K")
        print("the following models are being recorded: {}".format(recording), end="\r")
        getOnlineModels()
        sys.stdout.write("\033[F")
        for i in range(interval, 0, -1):
            sys.stdout.write("\033[K")
            print(now(), "{} model(s) are being recorded. Next check in {} seconds".format(len(recording), i))
            sys.stdout.write("\033[K")
            print("the following models are being recorded: {}".format(recording), end="\r")
            time.sleep(1)
            sys.stdout.write("\033[F")
