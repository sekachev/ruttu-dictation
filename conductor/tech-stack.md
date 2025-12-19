# Tech Stack: ruttu-dictation

## Core Technologies
*   **Language:** Python 3.11+
*   **GUI Framework:** PySide6 (Qt for Python)
*   **Tray Icon & Menu:** pystray
*   **Audio Capture:** PyAudio
*   **Voice Activity Detection (VAD):** Silero VAD (ONNX)
*   **Transcription Service:** Deepgram (Real-time Streaming)
*   **Text Injection:** pynput (Typing emulation)

## Libraries & Tools
*   **numpy:** Audio buffer processing.
*   **websockets:** Communication with Deepgram.
*   **python-dotenv:** Environment variable management (API Keys).
*   **requests:** General HTTP requests.
*   **Pillow:** Icon and image processing for the tray.

## Architecture
*   **Modular Design:** Separate engines for audio capture, VAD, transcription, and typing.
*   **Asynchronous Processing:** Likely using `asyncio` or threading for low-latency transcription without blocking the UI.
*   **State Management:** Configuration handled via persistent JSON files.

## Target Platform
*   **Primary:** macOS (designed for native-like menu bar experience).
