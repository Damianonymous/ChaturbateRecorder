import websocket
import rel

import config

settings = config.readConfig()

def on_message(ws, message):
    print(message)

try:
    ws = websocket.WebSocketApp(
        f"wss://realtime.pa.highwebmedia.com/?access_token={settings['access_token']}&format=json&heartbeats=true&v=2&agent=ably-js%2F1.2.37%20browser&remainPresentFor=0",
        on_message=on_message,
    )

    # Set dispatcher to automatic reconnection, 5 second reconnect delay if connection closed unexpectedly
    ws.run_forever(dispatcher=rel, reconnect=5)
    # Keyboard Interrupt
    rel.signal(2, rel.abort)
    rel.dispatch()
except Exception as e:
    print(e)
