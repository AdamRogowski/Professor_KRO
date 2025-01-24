from gtts import gTTS
import os

from french_numbers import french_numbers
from polish_numbers import polish_numbers
from danish_numbers import danish_numbers

output_dir = "C:\\Users\\jaro\\Desktop\\git-projects\\numbers_prompt\\audio\\generated_audio\\danish"
os.makedirs(output_dir, exist_ok=True)

for num, text in danish_numbers.items():
    tts = gTTS(text, lang="da")
    tts.save(f"{output_dir}/{num}.mp3")
    print(f"Saved {num}.mp3")
