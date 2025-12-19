import numpy as np
import torch
from silero_vad import load_silero_vad

class SileroVAD:
    def __init__(self, threshold=0.5, sample_rate=16000):
        self.threshold = threshold
        self.sample_rate = sample_rate
        
        # Load the Silero VAD model
        self.model = load_silero_vad()
        
        # Set torch to use single thread for better performance
        torch.set_num_threads(1)

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
        
        if len(audio_float32) == 0:
            return False

        # Silero VAD expects exactly 512 samples for 16kHz
        # If we have more samples, take the first 512
        expected_samples = 512
        if len(audio_float32) >= expected_samples:
            audio_float32 = audio_float32[:expected_samples]
        else:
            # If we have fewer samples, pad with zeros
            audio_float32 = np.pad(audio_float32, (0, expected_samples - len(audio_float32)), 'constant')
        
        # Convert to torch tensor and add batch dimension
        audio_tensor = torch.from_numpy(audio_float32).unsqueeze(0)
        
        # Get speech probability from Silero VAD
        with torch.no_grad():
            speech_prob = self.model(audio_tensor, self.sample_rate).item()
        
        return speech_prob >= self.threshold
