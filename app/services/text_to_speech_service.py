from gtts import gTTS
import os

class TextToSpeechService:
    def __init__(self):
        """Ensure static/audio directory exists."""
        self.audio_folder = os.path.join(os.getcwd(), "static/audio")  # Absolute path
        os.makedirs(self.audio_folder, exist_ok=True)  # Ensure folder exists
        self.audio_file = os.path.join(self.audio_folder, "response.mp3")  # MP3 path

    def text_to_speech(self, text: str) -> str:
        """Convert text to speech using Google TTS and save as MP3."""
        try:
            tts = gTTS(text=text, lang="en")
            tts.save(self.audio_file)  # Save as MP3
            return self.audio_file  # Return absolute file path
        except Exception as e:
            print(f"Error generating speech: {str(e)}")
            return None