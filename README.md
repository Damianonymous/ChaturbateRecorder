# ChaturbateRecorder

This is script to automate the recording of public webcam shows from chaturbate.com. 


I have tested this on debian(7+8), ubuntu 14, freenas10 (inside a jail), and Mac OS X (10.10.4), but it should run on other OSs
I do not have a windows machine to test on, but I had another user test it on windows and has reported the 6/21/17 update as working on windows 10 using python3.6.2  (may also work on python3.5+)
## Requirements

Requires python3.5 or newer. You can grab python3.5.2 from https://www.python.org/downloads/release/python-352/

to install required modules, run:
```
python3.5 -m pip install livestreamer bs4 lxml gevent
```


Edit the config file (config.conf) to point to the directory you want to record to, where your "wanted" file is located, which genders, and the interval between checks (in seconds)

Add models to the "wanted.txt" file (only one model per line). The model should match the models name in their chatrooms URL (https://chaturbate.com/{modelname}/). T clarify this, it should only be the "modelname" portion, not the entire url.
