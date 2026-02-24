import requests
import time
import random
import tempfile
import os
import re

# HF Token
try:
    from config import HUGGINGFACE_API_TOKEN
except:
    HUGGINGFACE_API_TOKEN = "[REMOVED_HF_TOKEN]"


class AudioCaptchaSolver:
    """Solves audio captchas using faster Whisper ASR"""
    
    def __init__(self, driver=None):
        self.driver = driver
        self.headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}
        self._whisper_model = None
    
    def _get_whisper_model(self):
        """Lazy load whisper model"""
        if self._whisper_model is None:
            try:
                from faster_whisper import WhisperModel
                print("[Captcha] Loading Whisper model...")
                self._whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
            except ImportError:
                print("[Captcha] faster-whisper not available")
                return None
        return self._whisper_model
    
    def _transcribe_audio_url(self, url):
        """Download and transcribe audio"""
        try:
            # Download audio
            print("[Captcha] Downloading audio...")
            if url.startswith("data:audio"):
                import base64
                print("[Captcha] Decoding base64 audio data URI")
                header, encoded = url.split(",", 1)
                audio_data = base64.b64decode(encoded)
            else:
                resp = requests.get(url, timeout=30)
                if resp.status_code != 200:
                    print(f"[Captcha] Download failed: {resp.status_code}")
                    return None
                audio_data = resp.content
                
            print(f"[Captcha] Downloaded {len(audio_data)} bytes")
            
            # Save to temp file (keep .mp3 extension)
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                f.write(audio_data)
                temp_path = f.name
            
            text = None
            
            # Method 1: faster-whisper (best, handles mp3 directly)
            text = self._transcribe_faster_whisper(temp_path)
            
            # Method 2: Hugging Face API (backup)
            if not text:
                text = self._transcribe_hf_api(temp_path)
            
            # Cleanup
            try:
                os.unlink(temp_path)
            except:
                pass
            
            return text
            
        except Exception as e:
            print(f"[Captcha] Error: {e}")
            return None
    
    def _transcribe_faster_whisper(self, audio_path):
        """Use faster-whisper (fast local ASR)"""
        try:
            model = self._get_whisper_model()
            if not model:
                return None
            
            print("[Captcha] Transcribing with faster-whisper...")
            
            # Transcribe with language hints for captcha
            segments, info = model.transcribe(
                audio_path,
                language="en",
                beam_size=1,  # Faster
                vad_filter=True,  # Voice activity detection
            )
            
            text = "".join([segment.text for segment in segments]).strip()
            
            if text:
                print(f"[Captcha] faster-whisper result: '{text}'")
                return text
            
            return None
            
        except Exception as e:
            print(f"[Captcha] faster-whisper error: {e}")
            return None
    
    def _transcribe_hf_api(self, audio_path):
        """Use Hugging Face Inference API as backup"""
        try:
            print("[Captcha] Trying HF API backup...")
            
            with open(audio_path, 'rb') as f:
                audio_bytes = f.read()
            
            # Try Whisper models on HF
            models = [
                "openai/whisper-tiny",
                "openai/whisper-small",
                "openai/whisper-large-v3-turbo",
            ]
            
            for model in models:
                try:
                    url = f"https://api-inference.huggingface.co/models/{model}"
                    
                    resp = requests.post(
                        url,
                        headers=self.headers,
                        data=audio_bytes,
                        timeout=60
                    )
                    
                    print(f"[Captcha] HF {model}: status {resp.status_code}")
                    
                    if resp.status_code == 200:
                        result = resp.json()
                        if isinstance(result, dict) and 'text' in result:
                            text = result['text'].strip()
                            print(f"[Captcha] HF result: '{text}'")
                            return text
                    elif resp.status_code == 503:
                        # Model is loading
                        data = resp.json()
                        wait_time = data.get('estimated_time', 10)
                        print(f"[Captcha] Model loading, waiting {wait_time}s...")
                        time.sleep(min(wait_time, 20))
                        
                        # Retry
                        resp = requests.post(url, headers=self.headers, data=audio_bytes, timeout=60)
                        if resp.status_code == 200:
                            result = resp.json()
                            if 'text' in result:
                                return result['text'].strip()
                                
                except requests.exceptions.Timeout:
                    print(f"[Captcha] {model} timeout")
                    continue
                except Exception as e:
                    print(f"[Captcha] {model} error: {str(e)[:50]}")
                    continue
            
            return None
            
        except Exception as e:
            print(f"[Captcha] HF API error: {e}")
            return None


def install_asr():
    """Install ASR dependencies"""
    import subprocess
    import sys
    
    packages = ["faster-whisper"]
    
    for pkg in packages:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            print(f"[*] Installing {pkg}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])


if __name__ == "__main__":
    install_asr()
    print("[OK] ASR ready")
