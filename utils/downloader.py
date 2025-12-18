import os
import requests

def download_silero_vad():
    model_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
    model_path = os.path.join(model_dir, "silero_vad.onnx")
    
    if os.path.exists(model_path):
        return model_path
    
    print("[INFO] Silero VAD model not found. Downloading...")
    os.makedirs(model_dir, exist_ok=True)
    
    url = "https://github.com/snakers4/silero-vad/raw/master/src/silero_vad/data/silero_vad.onnx"
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(model_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"[INFO] Model downloaded to {model_path}")
        return model_path
    else:
        raise Exception(f"Failed to download Silero VAD model. Status code: {response.status_code}")
