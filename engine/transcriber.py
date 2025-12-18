import os
import threading
from deepgram import (
    DeepgramClient,
    LiveTranscriptionEvents,
    LiveOptions,
    DeepgramClientOptions
)

class DeepgramTranscriber:
    def __init__(self, api_key, config_manager, transcription_callback):
        self.api_key = api_key
        self.config_manager = config_manager
        self.callback = transcription_callback
        
        self.client = DeepgramClient(self.api_key)
        self.connection = None

    def start(self):
        self.connection = self.client.listen.live.v("1")

        def on_message(self, result, **kwargs):
            if result.channel.alternatives:
                transcript = result.channel.alternatives[0].transcript
                is_final = result.is_final
                if len(transcript) > 0:
                    self.callback(transcript, is_final)

        def on_error(self, error, **kwargs):
            print(f"[ERROR] Deepgram: {error}")

        self.connection.on(LiveTranscriptionEvents.Transcript, on_message)
        self.connection.on(LiveTranscriptionEvents.Error, on_error)

        options = LiveOptions(
            model=self.config_manager.get("model"),
            language=self.config_manager.get("language"),
            smart_format=True,
            interim_results=True
        )
        
        if self.connection.start(options) is False:
            raise Exception("Failed to start Deepgram connection")

    def send_audio(self, data):
        if self.connection:
            self.connection.send(data)

    def stop(self):
        if self.connection:
            self.connection.finish()
