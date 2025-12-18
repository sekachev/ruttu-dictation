# ruttu.ee - Fast Dictation for macOS

**Codename:** ruttu.ee
**Target Platform:** macOS (Menu Bar App)
**Backend:** Deepgram (Real-time Streaming)

## Features
- [ ] **Menu Bar Integration:** Red/Gray status icon.
- [ ] **Real-time Transcription:** Low-latency text insertion via Deepgram Nova-3.
- [ ] **Smart Formatting:** Automatic punctuation and formatting.
- [ ] **Settings Dashboard:**
    - Language switcher (RU, EE, EN).
    - API Key Management.
    - Custom Exclusions (Hallucination filtering).
    - Voice Commands (New line, list, etc.).

## Project Structure
- `main.py`: App lifecycle and Tray Icon.
- `engine/`: Core logic.
    - `transcriber.py`: Deepgram WebSocket integration.
    - `audio.py`: Microphone capture (PyAudio).
    - `typist.py`: Text insertion logic (pynput).
- `ui/`: GUI components.
    - `settings_window.py`: PySide6 tabs for configuration.
- `utils/`: Helpers.
    - `config.py`: Persistent settings (JSON).
    - `filters.py`: Logic for exclusions and command processing.
