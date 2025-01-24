import csv
import pygame
import random
import os
import io
from gtts import gTTS
import sys

LANG_NAME_MAP = {
    "en": "English",
    "pl": "Polish",
    "fr": "French",
    "da": "Danish",
}

DEFAULT_PROGRESS = 2
CYCLE_PROMPTS = 8
LESSONS_DIR = "lessons"


class LessonManager:
    def __init__(self, lesson_file, language):
        self.lesson_file = lesson_file
        self.language = language
        self.lesson_data = self.load_lesson()

    def load_lesson(self):
        """Load lesson data from the specified CSV file."""
        try:
            with open(self.lesson_file, mode="r", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                return {
                    row["word"]: {
                        "translation": row["translation"],
                        "progress": (
                            int(row["progress"])
                            if row["progress"].strip()
                            else DEFAULT_PROGRESS
                        ),
                        "usage": row["usage"] if row["usage"].strip() else "",
                    }
                    for row in reader
                }
        except Exception as e:
            print(f"Error loading lesson data: {e}")
            return {}

    def save_lesson(self):
        """Save lesson data back to the specified CSV file."""
        try:
            with open(self.lesson_file, mode="w", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(
                    file, fieldnames=["word", "translation", "progress", "usage"]
                )
                writer.writeheader()
                for word, data in self.lesson_data.items():
                    writer.writerow(
                        {
                            "word": word,
                            "translation": data["translation"],
                            "progress": data["progress"],
                            "usage": data["usage"],
                        }
                    )
        except Exception as e:
            print(f"Error saving lesson data: {e}")

    def reset_progress(self, default_progress=DEFAULT_PROGRESS):
        for word in self.lesson_data:
            self.lesson_data[word]["progress"] = default_progress
        print("Progress reset for all words.")

    def show_words(self):
        print("ID | Word | Translation | Progress | Usage")
        for idx, (word, data) in enumerate(self.lesson_data.items(), start=1):
            print(
                f"{idx} | {word} | {data['translation']} | {data['progress']} | {data['usage']}"
            )

    def lesson_info(self, target_progress):
        print(f"File: {self.lesson_file}")
        print(f"Language: {LANG_NAME_MAP[self.language]}")
        print(f"Target progress: {target_progress}")
        print(f"Number of words: {len(self.lesson_data)}")
        print(
            f"Words to practice: {len([word for word in self.lesson_data if self.lesson_data[word]['progress'] < target_progress])}"
        )
        print(
            f"Words completed: {len([word for word in self.lesson_data if self.lesson_data[word]['progress'] >= target_progress])}"
        )


class PracticeSession:
    def __init__(self, lesson_manager, target_progress=4):
        self.lesson_manager = lesson_manager
        self.target_progress = target_progress

    def play_text(self, text):
        """Play text audio in the given language."""
        try:
            tts = gTTS(text, lang=self.lesson_manager.language)
            audio_data = io.BytesIO()
            tts.write_to_fp(audio_data)
            audio_data.seek(0)
            sound = pygame.mixer.Sound(audio_data)
            sound.play()
            while pygame.mixer.get_busy():
                pygame.time.Clock().tick(10)
        except Exception as e:
            print(f"Error playing text: {e}")

    def handle_command(self, command, word, expected_answer):
        data = self.lesson_manager.lesson_data[word]

        if command in {"exit", "quit", "-e", "-q", "-exit", "-quit"}:
            print("Exiting this mode.")
            return -1
        elif command in {"help", "-h", "?", "-?", "commands", "-help"}:
            print(
                """Commands:
    - ['exit', 'quit', '-e', '-q', '-exit', '-quit']: Exits the current mode.
    - ['help', '-h', '?', '-?', 'commands', '-help']: Displays available commands.
    - ['hint', '-hint']: Provides a hint by showing the first letter of the word.
    - ['usage', '-usage', 'context', '-context', '-u']: Displays the usage/context of the word.
    - ['progress', '-progress', '-p']: Shows the current progress of the word.
    - ['skip', '-skip', 'accept', '-accept', '-s']: Skips the current word as if answered correctly.
    - ['repeat', '-repeat', 'play', '-play']: Repeats the word by playing its audio."""
            )
        elif command in {"hint", "-hint"}:
            print(f"The first letter of the word is '{expected_answer[0]}'.")
        elif command in {"usage", "-usage", "context", "-context", "-u"}:
            print(data["usage"] or "No usage/context provided for this word.")
        elif command in {"progress", "-progress", "-p"}:
            print(f"Current progress: {data['progress']}")
        elif command in {"skip", "-skip", "accept", "-accept", "-s"}:
            print("Skipping this word.")
            data["progress"] += 1
            return 0
        elif command in {"repeat", "-repeat", "play", "-play"}:
            print("Repeating the word...")
            self.play_text(word)
        else:
            print("Unknown command.")

        return None

    def prompt(self, word, prompt_type):
        data = self.lesson_manager.lesson_data[word]
        if prompt_type == "audio_to_translation":
            self.play_text(word)
            print("Translation to English:")
        elif prompt_type == "translation_to_word":
            print(f"English word: {data['translation']}")
            print(f"Spell in {LANG_NAME_MAP[self.lesson_manager.language]}:")
        elif prompt_type == "word_to_translation":
            print(f"{LANG_NAME_MAP[self.lesson_manager.language]} word: {word}")
            print("Translation to English:")

        expected_answer = (
            data["translation"] if prompt_type != "translation_to_word" else word
        )

        while True:
            answer = input(">> ").strip()
            if answer == expected_answer:
                print("Correct!")
                data["progress"] += 1
                return True
            command_result = self.handle_command(answer, word, expected_answer)
            if command_result is not None:
                return command_result
            print(f"Incorrect. The correct answer is '{expected_answer}'.")
            data["progress"] -= 1

    def start(self, mode):
        """Start a practice session."""
        while True:
            words_to_practice = [
                word
                for word, data in self.lesson_manager.lesson_data.items()
                if data["progress"] < self.target_progress
            ]

            if not words_to_practice:
                print("No words to practice.")
                break

            random.shuffle(words_to_practice)
            for word in words_to_practice:
                if not self.prompt(word, mode):
                    break

            if not input("Continue? (y/n): ").strip().lower() in {"y", "yes"}:
                break


class App:
    def __init__(self):
        self.lessons = self.load_lessons()
        self.target_progress = 4

    def load_lessons(self):
        return [
            (file, file.split("_")[-1].split(".")[0])
            for file in os.listdir(LESSONS_DIR)
            if file.endswith(".csv")
        ]

    def select_lesson(self):
        print("Available lessons:")
        for idx, (file, lang) in enumerate(self.lessons, start=1):
            print(f"({idx}) {file} (Language: {LANG_NAME_MAP[lang]})")

        choice = int(input(">> ").strip()) - 1
        lesson_file, language = self.lessons[choice]
        return LessonManager(os.path.join(LESSONS_DIR, lesson_file), language)

    def main_menu(self):
        pygame.mixer.init()
        lesson_manager = self.select_lesson()

        while True:
            print("\nSelect an option:")
            print("(1) Practice")
            print("(2) Lesson Information")
            print("(3) Show words")
            print("(4) Reset Progress")
            print("(5) Set Target Progress")
            print("(6) Exit")
            choice = input(">> ").strip()

            if choice == "1":
                print("\nSelect a mode:")
                print("(1) Practice translation from audio")
                print("(2) Practice spelling")
                print("(3) Practice translation to English")
                mode_choice = input(">> ").strip()

                mode_map = {
                    "1": "audio_to_translation",
                    "2": "translation_to_word",
                    "3": "word_to_translation",
                }
                mode = mode_map.get(mode_choice)
                if mode:
                    session = PracticeSession(lesson_manager, self.target_progress)
                    session.start(mode)
            elif choice == "2":
                lesson_manager.lesson_info(self.target_progress)
            elif choice == "3":
                lesson_manager.show_words()
            elif choice == "4":
                lesson_manager.reset_progress()
            elif choice == "5":
                self.target_progress = int(input("Enter target progress: ").strip())
            elif choice == "6":
                lesson_manager.save_lesson()
                break
            else:
                print("Invalid choice.")


if __name__ == "__main__":
    app = App()
    app.main_menu()
