import sys
import threading
import pystray
import pyaudio
import time
from PIL import Image, ImageDraw
import os
from PySide6.QtWidgets import QApplication

from utils.config import ConfigManager
from utils.filters import TextProcessor
from ui.settings_window import SettingsWindow
from engine.audio import AudioStreamer
from engine.transcriber import DeepgramTranscriber
from engine.whisper_live_transcriber import WhisperLiveTranscriber
from engine.typist import MacTypist
from engine.vad import SileroVAD

from collections import deque

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
        self.connection_timeout = 7.0
        self.is_connected = False
        
        self.pre_roll = deque(maxlen=4)
        self.pending_audio = []

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

    def update_icon(self):
        if not self.recording_active:
            color = "#555555"
        elif self.is_connected:
            color = "#FF4444"
        else:
            color = "#FFD700"
            
        if self.icon:
            self.icon.icon = self.create_icon_image(color)

    def on_transcription(self, text, is_final):
        processed = self.processor.process_segment(text, is_final)
        if processed:
            print(f"[LIVE] {processed} (final={is_final})")
            if is_final:
                self.typist.type_text(processed + " ")

    def start_transcriber(self):
        if not self.transcriber:
            engine = self.config.get("transcription_engine", "deepgram")
            print(f"[INFO] VAD Triggered! Connecting to {engine}...")

            if engine == "deepgram":
                self.transcriber = DeepgramTranscriber(
                    self.config.get("api_key"),
                    self.config,
                    self.on_transcription
                )
            elif engine == "whisper_live":
                self.transcriber = WhisperLiveTranscriber(
                    self.config.get("whisper_host", "localhost"),
                    self.config.get("whisper_port", 9090),
                    self.config,
                    self.on_transcription
                )

            if self.transcriber:
                self.transcriber.start()
                if self.transcriber.connection_ready.wait(timeout=5):
                    print(f"[INFO] Connection to {engine} established.")
                    self.is_connected = True
                    self.update_icon()

                    for chunk in self.pre_roll:
                        self.transcriber.send_audio(chunk)

                    for chunk in self.pending_audio:
                        self.transcriber.send_audio(chunk)
                    self.pending_audio = []
                else:
                    print(f"[ERROR] Connection to {engine} timed out.")
                    self.stop_transcriber()

    def stop_transcriber(self):
        if self.transcriber:
            print("[INFO] Silence detected. Closing connection.")
            self.transcriber.stop()
            self.transcriber = None
            self.is_connected = False
            self.pending_audio = []
            self.update_icon()

    def audio_callback(self, in_data, frame_count, time_info, status):
        if not self.recording_active:
            return (None, pyaudio.paContinue)
            
        is_speech = self.vad and self.vad.is_speech(in_data)
        
        if is_speech:
            self.last_speech_time = time.time()
            if not self.is_connected and not self.transcriber:
                self.pending_audio.append(in_data)
                if len(self.pending_audio) == 1:
                    threading.Thread(target=self.start_transcriber, daemon=True).start()
            elif self.is_connected and self.transcriber:
                self.transcriber.send_audio(in_data)
        else:
            self.pre_roll.append(in_data)
            
            if self.is_connected and (time.time() - self.last_speech_time > self.connection_timeout):
                self.stop_transcriber()
                
        return (None, pyaudio.paContinue)

    def toggle_dictation(self):
        engine = self.config.get("transcription_engine", "deepgram")
        if engine == "deepgram" and not self.config.get("api_key"):
            print("[ERROR] No API Key set in settings!")
            self.on_settings()
            return

        self.recording_active = not self.recording_active
        self.update_icon()
        
        if self.recording_active:
            print("[INFO] App active. VAD monitoring started.")
            if not self.vad:
                self.vad = SileroVAD()
            self.audio.start(self.audio_callback)
        else:
            self.audio.stop()
            self.stop_transcriber()
            print("[INFO] Dictation stopped.")

    def on_exit(self):
        self.audio.stop()
        self.stop_transcriber()
        if self.icon: self.icon.stop()
        self.qt_app.quit()
        sys.exit(0)

    def set_language(self, lang):
        def inner():
            self.config.set("language", lang)
            print(f"[INFO] Language changed to: {lang}")
            if self.is_connected:
                self.stop_transcriber()
        return inner

    def run(self):
        lang_menu = pystray.Menu(
            pystray.MenuItem("🇪🇪 Estonian", self.set_language("ee"), 
                             checked=lambda item: self.config.get("language") == "ee", radio=True),
            pystray.MenuItem("🇷🇺 Russian", self.set_language("ru"), 
                             checked=lambda item: self.config.get("language") == "ru", radio=True),
            pystray.MenuItem("🇬🇧 English", self.set_language("en"), 
                             checked=lambda item: self.config.get("language") == "en", radio=True),
        )

        menu = pystray.Menu(
            pystray.MenuItem("Toggle Dictation", self.toggle_dictation, default=True),
            pystray.MenuItem("Language", lang_menu),
            pystray.MenuItem("Settings...", self.on_settings),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit ruttu.ee", self.on_exit)
        )
        
        self.icon = pystray.Icon("ruttu", self.create_icon_image("#555555"), "ruttu.ee", menu)
        
        icon_thread = threading.Thread(target=self.icon.run, daemon=True)
        icon_thread.start()
        
        sys.exit(self.qt_app.exec())

if __name__ == "__main__":
    app = RuttuApp()
    app.run()
