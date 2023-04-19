# ChaturbateRecorder

All credits to @beaston02, @ahsand97 and @Damianonymous

This is a script to automate the recording of public webcam shows from chaturbate.com.

## Requirements

Requires python3.5 or newer.

to install the required modules, run:
```
python3 -m pip install streamlink bs4 lxml gevent
```


Copy the config file `config.conf.dist` to `config.conf` and edit to point to the directory you want to record to, where your "wishlist" file is located, which genders, and the interval between checks (in seconds)

Add models to the "wishlist.txt" file (only one model per line). The model should match the model's name in their chatrooms URL (https://chaturbate.com/{modelname}/). To clarify this, it should only be the "modelname" portion, not the entire url.
