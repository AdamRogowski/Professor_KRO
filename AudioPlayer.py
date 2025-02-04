from gtts import gTTS
import pygame
import io


class AudioPlayer:
    """Handles text-to-speech playback."""

    def __init__(self, language):
        self.language = language
        pygame.mixer.init()

    def play_text(self, text):
        """Play text as speech."""
        try:
            tts = gTTS(text, lang=self.language)
            audio_data = io.BytesIO()
            tts.write_to_fp(audio_data)
            audio_data.seek(0)
            sound = pygame.mixer.Sound(audio_data)
            sound.play()
            while pygame.mixer.get_busy():
                pygame.time.Clock().tick(10)
        except Exception as e:
            print(f"Error playing text: {e}")
