import os
import threading
import time
from deepgram import (
    DeepgramClient,
)
from deepgram.core.events import EventType
from deepgram.extensions.types.sockets import ListenV1SocketClientResponse

class DeepgramTranscriber:
    def __init__(self, api_key, config_manager, transcription_callback):
        self.api_key = api_key
        self.config_manager = config_manager
        self.callback = transcription_callback
        self.connection = None
        self.listening_thread = None
        self.connection_ready = threading.Event()
        
        # Map language codes to Deepgram format
        self.language_map = {
            "en": "en",
            "ru": "russian", 
            "ee": "estonian"
        }

    def start(self):
        # Create Deepgram client with API key
        self.client = DeepgramClient(api_key=self.api_key)

        def on_message(message: ListenV1SocketClientResponse) -> None:
            # Log all received messages for debugging
            msg_type = getattr(message, "type", "Unknown")
            print(f"[DEBUG] Received Deepgram message type: {msg_type}")
            
            if hasattr(message, 'channel') and hasattr(message.channel, 'alternatives'):
                transcript = message.channel.alternatives[0].transcript
                is_final = message.is_final if hasattr(message, 'is_final') else False
                print(f"[DEBUG] Transcript: '{transcript}' (final: {is_final})")
                if len(transcript) > 0:
                    self.callback(transcript, is_final)
            else:
                print(f"[DEBUG] Message has no channel/alternatives: {message}")

        def on_error(error) -> None:
            print(f"[ERROR] Deepgram: {error}")

        def on_open(_) -> None:
            print("[INFO] Deepgram connection opened")
            self.connection_ready.set()

        def on_close(_) -> None:
            print("[INFO] Deepgram connection closed")
            self.connection_ready.clear()

        # Start listening in a separate thread
        def listening_thread():
            try:
                # Get the proper language code for Deepgram
                lang_code = self.config_manager.get("language")
                deepgram_language = self.language_map.get(lang_code, "en")  # Default to English
                
                print(f"[DEBUG] Using language: {lang_code} -> {deepgram_language}")
                
                # Create a websocket connection to Deepgram
                with self.client.listen.v1.connect(
                    model=self.config_manager.get("model"),
                    language=deepgram_language,
                    smart_format=True,
                    interim_results=True
                ) as connection:
                    
                    self.connection = connection
                    
                    # Set up event handlers
                    connection.on(EventType.OPEN, on_open)
                    connection.on(EventType.MESSAGE, on_message)
                    connection.on(EventType.ERROR, on_error)
                    connection.on(EventType.CLOSE, on_close)
                    
                    # Start listening for messages
                    connection.start_listening()
                    
            except Exception as e:
                print(f"[ERROR] Deepgram listening thread error: {e}")

        self.listening_thread = threading.Thread(target=listening_thread, daemon=True)
        self.listening_thread.start()

    def send_audio(self, data):
        # Wait for connection to be ready before sending audio
        if self.connection_ready.wait(timeout=0.1):  # Wait up to 100ms
            if self.connection:
                print(f"[DEBUG] Sending audio chunk: {len(data)} bytes")
                self.connection.send_media(data)
        else:
            print("[DEBUG] Connection not ready, skipping audio chunk")

    def stop(self):
        self.connection_ready.clear()  # Clear the event first
        if self.connection:
            self.connection.finish()
            self.connection = None
        if self.listening_thread:
            self.listening_thread.join(timeout=2.0)
            self.listening_thread = None
