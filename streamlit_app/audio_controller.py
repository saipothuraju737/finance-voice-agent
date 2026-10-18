import tempfile

from gtts import gTTS


class AudioController:
    def __init__(self):
        self.audio_file = None

    def generate_audio(self, text):
        try:
            tts = gTTS(text)
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            tmp.close()
            tts.save(tmp.name)
            self.audio_file = tmp.name
            return tmp.name
        except Exception as e:
            print(f"[ERROR] Failed to generate TTS: {e}")
            return None


audio = AudioController()
