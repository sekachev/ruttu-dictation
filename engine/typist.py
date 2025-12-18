import time
from pynput.keyboard import Controller, Key

class MacTypist:
    """
    Handles text insertion on macOS. 
    Uses a combination of direct typing and clipboard for speed/reliability.
    """
    def __init__(self):
        self.keyboard = Controller()

    def type_text(self, text):
        if not text:
            return
        
        # On Mac, sometimes direct typing is more reliable for short segments, 
        # but clipboard is faster for long ones.
        # For our live dictation, we'll try direct typing first.
        self.keyboard.type(text)

    def backspace(self, count):
        for _ in range(count):
            self.keyboard.press(Key.backspace)
            self.keyboard.release(Key.backspace)
            time.sleep(0.01)

    def press_combo(self, keys):
        """Presses combinations like Cmd+V"""
        # Note: In pynput, Key.cmd is the Command key on Mac
        for key in keys:
            self.keyboard.press(key)
        for key in reversed(keys):
            self.keyboard.release(key)
