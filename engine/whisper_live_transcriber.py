import threading
import websockets
import asyncio
import json

class WhisperLiveTranscriber:
    def __init__(self, host, port, config_manager, transcription_callback):
        self.host = host
        self.port = port
        self.config_manager = config_manager
        self.callback = transcription_callback
        self.websocket = None
        self.listening_thread = None
        self.connection_ready = threading.Event()
        self.loop = None

    def start(self):
        self.listening_thread = threading.Thread(target=self.run_client, daemon=True)
        self.listening_thread.start()

    def run_client(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.connect_and_listen())

    async def connect_and_listen(self):
        uri = f"ws://{self.host}:{self.port}"
        try:
            async with websockets.connect(uri) as websocket:
                self.websocket = websocket
                self.connection_ready.set()

                config = {
                    "uid": "user",
                    "language": self.config_manager.get("language"),
                    "model_size": self.config_manager.get("whisper_model", "small"),
                    "use_vad": False,
                }
                await websocket.send(json.dumps(config))

                while True:
                    try:
                        message = await websocket.recv()
                        data = json.loads(message)
                        if "segments" in data and data["segments"]:
                            transcript = " ".join([seg["text"] for seg in data["segments"]])
                            self.callback(transcript, True)
                    except websockets.exceptions.ConnectionClosed:
                        break
        except Exception as e:
            print(f"[ERROR] WhisperLive connection failed: {e}")
        finally:
            self.websocket = None
            self.connection_ready.clear()

    def send_audio(self, data):
        if self.connection_ready.wait(timeout=0.1) and self.websocket and self.loop:
            future = asyncio.run_coroutine_threadsafe(self.websocket.send(data), self.loop)
            try:
                future.result(timeout=1)
            except Exception as e:
                print(f"[ERROR] WhisperLive send_audio failed: {e}")
        else:
            print("[DEBUG] WhisperLive connection not ready, skipping audio chunk")

    def stop(self):
        if self.websocket and self.loop:
            future = asyncio.run_coroutine_threadsafe(self.websocket.close(), self.loop)
            try:
                future.result(timeout=1)
            except Exception as e:
                print(f"[ERROR] WhisperLive stop failed: {e}")
        if self.listening_thread:
            self.listening_thread.join(timeout=2.0)
            self.listening_thread = None
