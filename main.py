import sys
import threading
import pystray
import pyaudio
from PIL import Image, ImageDraw
import os
from PySide6.QtWidgets import QApplication

from Mac.utils.config import ConfigManager
from Mac.utils.filters import TextProcessor
from Mac.ui.settings_window import SettingsWindow
from Mac.engine.audio import AudioStreamer
from Mac.engine.transcriber import DeepgramTranscriber
from Mac.engine.typist import MacTypist

class RuttuApp:
    def __init__(self):
        self.config = ConfigManager(os.path.join(os.path.dirname(__file__), "config.json"))
        self.processor = TextProcessor(self.config)
        self.typist = MacTypist()
        self.audio = AudioStreamer()
        
        self.qt_app = QApplication(sys.argv)
        self.qt_app.setQuitOnLastWindowClosed(False)
        
        self.recording_active = False
        self.icon = None
        self.settings_window = None
        self.transcriber = None
        
        self.last_text_len = 0

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
            
            # Simple differential typing for demonstration
            # In a real app, we'd handle interim results more carefully
            if is_final:
                self.typist.type_text(processed + " ")
                self.last_text_len = 0
            else:
                # For interim, we'll just print to console for now
                # Real differential typing on Mac is tricky with pynput 
                # but we can implement it later.
                pass

    def audio_callback(self, in_data, frame_count, time_info, status):
        if self.recording_active and self.transcriber:
            self.transcriber.send_audio(in_data)
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
            try:
                self.transcriber = DeepgramTranscriber(
                    self.config.get("api_key"), 
                    self.config, 
                    self.on_transcription
                )
                self.transcriber.start()
                self.audio.start(self.audio_callback)
                print("[INFO] Dictation started")
            except Exception as e:
                print(f"[ERROR] Failed to start transcriber: {e}")
                self.toggle_dictation()
        else:
            self.audio.stop()
            if self.transcriber:
                self.transcriber.stop()
            print("[INFO] Dictation stopped")

    def on_exit(self):
        self.audio.stop()
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
