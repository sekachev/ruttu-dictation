import numpy as np
import onnxruntime as ort
import os
from Mac.utils.downloader import download_silero_vad

class SileroVAD:
    def __init__(self, threshold=0.5, sample_rate=16000):
        model_path = download_silero_vad()
        
        # Disable logging for ONNX
        options = ort.SessionOptions()
        options.log_severity_level = 3
        
        self.session = ort.InferenceSession(model_path, options, providers=['CPUExecutionProvider'])
        self.threshold = threshold
        self.sample_rate = sample_rate
        
        # State for the model (RNN states)
        self.h = np.zeros((2, 1, 64)).astype('float32')
        self.c = np.zeros((2, 1, 64)).astype('float32')
        self.sr = np.array([sample_rate], dtype=np.int64)

    def is_speech(self, audio_chunk):
        """
        audio_chunk: bytes or numpy array (16-bit PCM)
        Returns: True if speech detected, False otherwise
        """
        # Convert bytes to float32 normalized
        if isinstance(audio_chunk, bytes):
            audio_int16 = np.frombuffer(audio_chunk, dtype=np.int16)
        else:
            audio_int16 = audio_chunk
            
        audio_float32 = audio_int16.astype('float32') / 32768.
        
        # Prepare input
        # Silero expects chunk size of 512, 1024 or 1536 samples for 16kHz
        # If chunk is different, we might need to pad or handle it
        if len(audio_float32) == 0:
            return False

        input_data = {
            'input': audio_float32.reshape(1, -1),
            'h': self.h,
            'c': self.c,
            'sr': self.sr
        }
        
        out, h, c = self.session.run(None, input_data)
        self.h, self.c = h, c
        
        prob = out[0][0]
        return prob >= self.threshold
