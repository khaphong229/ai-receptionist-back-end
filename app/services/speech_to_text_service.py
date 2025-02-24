from google.cloud import speech
import io
import os
from pydub import AudioSegment

class SpeechToTextService:
    def __init__(self):
        self.client = speech.SpeechClient()

    def transcribe_audio(self, audio_path: str) -> str:
        # Convert MP3 to WAV if necessary
        if audio_path.endswith('.mp3'):
            audio = AudioSegment.from_mp3(audio_path)
            audio = audio.set_channels(1)  # Convert to mono
            audio_path = audio_path.replace('.mp3', '.wav')
            audio.export(audio_path, format='wav')
        else:
            # Load the audio file and convert to mono if necessary
            audio = AudioSegment.from_file(audio_path)
            if audio.channels > 1:
                audio = audio.set_channels(1)
                audio.export(audio_path, format='wav')

        # Load the audio file
        audio = AudioSegment.from_file(audio_path)
        sample_rate = audio.frame_rate

        with io.open(audio_path, "rb") as audio_file:
            content = audio_file.read()

        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,
            language_code="en-US",
            enable_automatic_punctuation=True,
            model="default",
            use_enhanced=True,
        )

        response = self.client.recognize(config=config, audio=audio)

        # Concatenate all results
        transcript = ""
        for result in response.results:
            transcript += result.alternatives[0].transcript + " "

        return transcript.strip()