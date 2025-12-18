import sys
import threading
import pystray
import pyaudio
import time
from PIL import Image, ImageDraw
import os
from PySide6.QtWidgets import QApplication

from Mac.utils.config import ConfigManager
from Mac.utils.filters import TextProcessor
from Mac.ui.settings_window import SettingsWindow
from Mac.engine.audio import AudioStreamer
from Mac.engine.transcriber import DeepgramTranscriber
from Mac.engine.typist import MacTypist
from Mac.engine.vad import SileroVAD

class RuttuApp:
    def __init__(self):
        self.config = ConfigManager(os.path.join(os.path.dirname(__file__), "config.json"))
        self.processor = TextProcessor(self.config)
        self.typist = MacTypist()
        self.audio = AudioStreamer()
        self.vad = None
        
        self.qt_app = QApplication(sys.argv)
        self.qt_app.setQuitOnLastWindowClosed(False)
        
        self.recording_active = False
        self.icon = None
        self.settings_window = None
        self.transcriber = None
        
        self.last_speech_time = 0
        self.connection_timeout = 10.0 # seconds of silence before closing connection
        self.is_connected = False

    def create_icon_image(self, color):
        width, height = 64, 64
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        padding = 10
        draw.ellipse([padding, padding, width-padding, height-padding], fill=color)
        return image

    def on_settings(self):
        if not self.settings_window:
            self.settings_window = SettingsWindow(self.config)
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def on_transcription(self, text, is_final):
        processed = self.processor.process_segment(text, is_final)
        if processed:
            print(f"[LIVE] {processed} (final={is_final})")
            if is_final:
                self.typist.type_text(processed + " ")

    def start_transcriber(self):
        if not self.transcriber:
            print("[INFO] Reconnecting to Deepgram...")
            self.transcriber = DeepgramTranscriber(
                self.config.get("api_key"), 
                self.config, 
                self.on_transcription
            )
            self.transcriber.start()
            self.is_connected = True

    def stop_transcriber(self):
        if self.transcriber:
            print("[INFO] Silence detected. Closing Deepgram connection to save credits.")
            self.transcriber.stop()
            self.transcriber = None
            self.is_connected = False

    def audio_callback(self, in_data, frame_count, time_info, status):
        if not self.recording_active:
            return (None, pyaudio.paContinue)
            
        # 1. Run VAD
        if self.vad and self.vad.is_speech(in_data):
            self.last_speech_time = time.time()
            if not self.is_connected:
                # Use a thread to avoid blocking audio stream
                threading.Thread(target=self.start_transcriber, daemon=True).start()
            
            if self.is_connected and self.transcriber:
                self.transcriber.send_audio(in_data)
        else:
            # 2. Handle silence timeout
            if self.is_connected and (time.time() - self.last_speech_time > self.connection_timeout):
                self.stop_transcriber()
                
        return (None, pyaudio.paContinue)

    def toggle_dictation(self):
        if not self.config.get("api_key"):
            print("[ERROR] No API Key set in settings!")
            self.on_settings()
            return

        self.recording_active = not self.recording_active
        color = "#FF4444" if self.recording_active else "#555555"
        self.icon.icon = self.create_icon_image(color)
        
        if self.recording_active:
            print("[INFO] App active. VAD monitoring started.")
            if not self.vad:
                self.vad = SileroVAD()
            self.audio.start(self.audio_callback)
        else:
            self.audio.stop()
            self.stop_transcriber()
            print("[INFO] Dictation fully stopped")

    def on_exit(self):
        self.audio.stop()
        self.stop_transcriber()
        if self.icon: self.icon.stop()
        self.qt_app.quit()
        sys.exit(0)

    def run(self):
        menu = pystray.Menu(
            pystray.MenuItem("Toggle Dictation", self.toggle_dictation, default=True),
            pystray.MenuItem("Settings", self.on_settings),
            pystray.Separator(),
            pystray.MenuItem("Exit ruttu.ee", self.on_exit)
        )
        
        self.icon = pystray.Icon("ruttu", self.create_icon_image("#555555"), "ruttu.ee", menu)
        
        icon_thread = threading.Thread(target=self.icon.run, daemon=True)
        icon_thread.start()
        
        sys.exit(self.qt_app.exec())

if __name__ == "__main__":
    app = RuttuApp()
    app.run()
