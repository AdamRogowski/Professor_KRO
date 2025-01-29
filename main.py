import csv
import pygame
import random
import os
import io
from gtts import gTTS
import sys

# Lessons directory
LESSONS_DIR = "lessons"

LANG_NAME_MAP = {
    "en": "English",
    "pl": "Polish",
    "fr": "French",
    "da": "Danish",
}

DEFAULT_PROGRESS = 2
CYCLE_PROMPTS = 5


class Lesson:
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = self.load_lesson(file_path)

    def load_lesson(self, file_path):
        """Load lesson data from the specified CSV file."""
        try:
            with open(file_path, mode="r", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                lesson_data = {
                    row["word"]: {
                        "translation": row["translation"],
                        "progress": (
                            int(row["progress"])
                            if row["progress"] and row["progress"].strip()
                            else DEFAULT_PROGRESS
                        ),
                        "usage": (
                            row["usage"]
                            if row["usage"] and row["usage"].strip()
                            else ""
                        ),
                    }
                    for row in reader
                }
            return lesson_data
        except (KeyError, ValueError) as e:
            print(f"Error loading lesson data: {e}")
            return {}

    def save_lesson(self):
        """Save lesson data back to the specified CSV file."""
        try:
            with open(self.file_path, mode="w", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(
                    file, fieldnames=["word", "translation", "progress", "usage"]
                )
                writer.writeheader()
                for word, data in self.data.items():
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
        for word in self.data:
            self.data[word]["progress"] = default_progress
        print("Progress reset for all words.")

    def show_words(self):
        """Display all words in the lesson."""
        print("ID | Word | Translation | Progress | Usage")
        idx = 1
        for word in self.data:
            print(
                f"{idx} | {word} | {self.data[word]['translation']} | {self.data[word]['progress']} | {self.data[word]['usage']}"
            )
            idx += 1

    def lesson_info(self, language, target_progress):
        print(f"file: {self.file_path}")
        print(f"Language: {LANG_NAME_MAP[language]}")
        print(f"Target progress: {target_progress}")
        print(f"Number of words: {len(self.data)}")
        print(
            f"Words to practice: {len([word for word in self.data if self.data[word]['progress'] < target_progress])}"
        )
        print(
            f"Words completed: {len([word for word in self.data if self.data[word]['progress'] >= target_progress])}"
        )


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


class PracticeSession:

    EXIT_COMMANDS = {"exit", "quit", "-e", "-q", "-exit", "-quit"}
    HELP_COMMANDS = {"help", "-h", "?", "-?", "commands", "-help"}
    HINT_COMMANDS = {"hint", "-hint"}
    USAGE_COMMANDS = {"usage", "-usage", "context", "-context", "-u"}
    SHOW_COMMANDS = {"show", "-show"}
    EDIT_COMMANDS = {"edit", "-edit"}
    SKIP_COMMANDS = {"skip", "-skip", "accept", "-accept", "-s"}
    REPEAT_COMMANDS = {"repeat", "-repeat", "play", "-play"}
    PROGRESS_COMMANDS = {"progress", "-progress", "-p"}

    def __init__(self, lesson, language, target_progress=4):
        self.lesson = lesson
        self.language = language
        self.target_progress = target_progress
        self.audio = AudioPlayer(language)

    def confirm_choice(self, prompt="Are you sure? (yes/no): "):
        # Ask the user if they want to continue or exit
        print(prompt)
        answer = input(">> ").strip().lower()
        return answer in {"yes", "y"} or answer == ""

    def present_lesson(self):
        """Present every word and its translation from the lesson list."""
        for word, data in self.lesson.data.items():
            print(f"{word} -> {data['translation']}")
            self.audio.play_text(word)
            if input("[PRESS ENTER] >>") in self.EXIT_COMMANDS:
                break

    def practice_lesson(self, mode_func):
        """
        Practice the lesson using the specified prompting mode.

        Args:
            mode_func (callable): The general_prompt function with a specific prompting mode.
        """
        while True:
            # Initialize cycle status: Track if each word has been answered correctly in the current cycle
            cycle_status = {
                word: False
                for word in self.lesson.data
                if self.lesson.data[word]["progress"] < self.target_progress
            }

            if not cycle_status:
                print("No words to practice")
                break

            # Save the initial progress for comparison later
            initial_progress = {
                word: self.lesson.data[word]["progress"] for word in cycle_status
            }

            # Convert the cycle status to a list of words
            words_to_practice = list(cycle_status.keys())

            # Split the words into windows of up to CYCLE_PROMPTS
            windows = [
                words_to_practice[i : i + CYCLE_PROMPTS]
                for i in range(0, len(words_to_practice), CYCLE_PROMPTS)
            ]

            # Track if every word's progress has decreased
            cycle_progress_increased = {word: False for word in self.lesson.data}

            for window in windows:
                # Shuffle the words within the current window
                random.shuffle(window)

                # Track words that need to be re-asked (those answered incorrectly in the window)
                remaining_words = window.copy()

                # Keep prompting the words until all are answered correctly at least once in the current window
                while remaining_words:
                    for word in remaining_words[
                        :
                    ]:  # Iterate over a copy of the remaining words
                        prompt_status = mode_func(self.lesson.data, self.language, word)
                        if prompt_status == -1:
                            return  # -1 = exit code
                        elif prompt_status == 0:  # answered correctly
                            remaining_words.remove(word)

                        # Check if the progress has decreased by 1 compared to the initial value
                        if self.lesson.data[word]["progress"] > initial_progress[word]:
                            cycle_progress_increased[word] = (
                                True  # Mark as progress decreased
                            )

            # Check if all words in the cycle have had their progress decreased
            if all(cycle_progress_increased[word] for word in self.lesson.data):
                print("Lesson complete!")
                break

            if not self.confirm_choice("Do you want to start a new lesson? (yes/no): "):
                break

    def prompt_translation_from_audio(self, word):
        self.audio.play_text(word)
        print("Translation to English:")
        answer = input(">> ").strip()
        return answer, self.lesson.data[word]["translation"]

    def prompt_target_word_from_translation(self, word):
        print(f"English word: {self.lesson.data[word]['translation']}")
        print(f"Spell in {LANG_NAME_MAP[self.language]}:")
        answer = input(f">> ").strip()
        return answer, word

    def prompt_translation_from_target_word(self, word):
        print(f"{LANG_NAME_MAP[self.language]} word: {word}")
        print("Translation to English:")
        answer = input(">> ").strip()
        return answer, self.lesson.data[word]["translation"]

    def general_prompt(self, mode, word=None):
        if not word:
            print("Error: Word not provided for this mode.")
            return 1

        answer, expected_answer = mode(word)

        while True:
            if answer == expected_answer:
                if mode == self.prompt_target_word_from_translation:
                    self.audio.play_text(word)
                print("Correct!")

                return self.handle_answer(word, True)

            elif answer in self.EXIT_COMMANDS:
                print("Exiting this mode.")
                return -1
            elif answer in self.HELP_COMMANDS:
                self.print_help()
                answer = input(">> ").strip()
            elif answer in self.HINT_COMMANDS:
                print(f"The first letter of the word is '{expected_answer[0]}'.")
                answer = input(">> ").strip()
            elif answer in self.USAGE_COMMANDS:
                self.show_usage(word)
                answer = input(">> ").strip()
            elif answer in self.PROGRESS_COMMANDS:
                print(f"Current progress: {self.lesson.data[word]['progress']}")
                answer = input(">> ").strip()
            elif answer in self.SKIP_COMMANDS:
                print("Skipping this word.")
                self.lesson.data[word]["progress"] += 1
                return 0
            elif answer in self.REPEAT_COMMANDS:
                print("Repeating the word...")
                self.audio.play_text(word)
                answer = input(">> ").strip()
            elif answer in self.SHOW_COMMANDS:
                print(f"Word: {word}")
                answer = input(">> ").strip()
            elif answer in self.EDIT_COMMANDS:
                return self.edit_word(word)
            else:
                print(f"Incorrect. The correct answer is '{expected_answer}'.")
                if mode == self.prompt_target_word_from_translation:
                    self.audio.play_text(expected_answer)

                return self.handle_answer(word, False)

    def edit_word(self, word):
        """Handles word editing."""
        data = self.lesson.data[word]
        new_word = input(f"Current word: {word}\nNew word >> ").strip()
        new_translation = input(
            f"Current translation: {data['translation']}\nNew translation >> "
        ).strip()
        new_usage = input(
            f"Current usage: {data.get('usage', '')}\nNew usage >> "
        ).strip()

        if new_word:
            data["word"] = new_word
        if new_translation:
            data["translation"] = new_translation
        if new_usage:
            data["usage"] = new_usage
        return 1

    def print_help(self):
        print(
            """Commands:
    - ['exit', 'quit', '-e', '-q', '-exit', '-quit']: Exits the current mode.
    - ['help', '-h', '?', '-?', 'commands', '-help']: Displays available commands.
    - ['hint', '-hint']: Provides a hint by showing the first letter of the word.
    - ['usage', '-usage', 'context', '-context', '-u']: Displays the usage/context of the word.
    - ['progress', '-progress', '-p']: Shows the current progress of the word.
    - ['skip', '-skip', 'accept', '-accept', '-s']: Skips the current word as if answered correctly.
    - ['show', '-show']: Prints the question.
    - ['repeat', '-repeat', 'play', '-play']: Repeats the word by playing its audio.
    - ['edit', '-edit']: Edits the question, translation and usage."""
        )

    def show_usage(self, word):
        """Displays usage/context."""
        usage = self.lesson.data[word].get("usage")
        print(usage if usage else "No usage provided.")
        if usage:
            self.audio.play_text(usage)

    def handle_answer(self, word, correct):
        """Handles additional actions after inputting an answer."""
        command = input("[PRESS ENTER] >>").strip()
        if command in self.EXIT_COMMANDS:
            print("Exiting this mode.")
            return -1
        if command in self.USAGE_COMMANDS:
            self.show_usage(word)
        elif command in self.SHOW_COMMANDS:
            print(f"Word: {word}")
        elif command in self.EDIT_COMMANDS:
            return self.edit_word(word)
        elif (
            command in self.SKIP_COMMANDS and not correct
        ):  # Skip possible only if the answer was incorrect
            print("Answer accepted")
            self.lesson.data[word]["progress"] += 1
        if correct:
            self.lesson.data[word]["progress"] += 1
            return 0
        else:
            if self.lesson.data[word]["progress"] > 0:
                self.lesson.data[word]["progress"] -= 1
            return 1


class ProfessorKROApp:
    def __init__(self):
        self.target_progress = 4

    def extract_lang(self, file_path):
        return file_path.split("_")[-1].split(".")[0]

    def extract_file_name(self, file_path):
        return file_path.split("\\")[-1].split(".")[0]

    def run(self):
        print("Welcome to the Professor KRO App!")

        while True:
            print("\nAvailable lessons:")

            lessons = []
            for root, _, files in os.walk(LESSONS_DIR):
                for file in files:
                    if file.endswith(".csv"):
                        # lang = file.split("_")[-1].split(".")[0]
                        lessons.append(
                            (os.path.join(root, file), self.extract_lang(file))
                        )

            try:
                # Display available lessons
                for idx, (file, lang) in enumerate(lessons, start=1):
                    print(
                        f"({idx}) {self.extract_file_name(file)} (Language: {LANG_NAME_MAP[lang]})"
                    )

                # Handle invalid input for lesson choice
                while True:
                    choice = input(">> ").strip()

                    if choice.isdigit():
                        choice = int(choice)
                        if (
                            1 <= choice <= len(lessons)
                        ):  # Check if the choice is within valid range
                            break
                        else:
                            print(
                                f"Invalid choice! Please enter a number between 1 and {len(lessons)}."
                            )
                    else:
                        print("Invalid input! Please enter a valid number.")

                # Retrieve the selected lesson and language
                selected_lesson = lessons[choice - 1]
                lesson_file, language = selected_lesson

                # Load the lesson data
                lesson = Lesson(lesson_file)
                session = PracticeSession(lesson, language, self.target_progress)

                try:

                    while True:
                        print("\nSelect an option:")
                        print("(1) Learn")
                        print("(2) Practice")
                        print("(3) Lesson Information")
                        print("(4) Show words")
                        print("(5) Reset Progress")
                        print("(6) Reset to input Progress")
                        print("(7) Set target Progress")
                        print("(8) Quit lesson")
                        option = input(">> ").strip()
                        if option == "1":
                            session.present_lesson()
                        elif option == "2":
                            while True:
                                if (
                                    len(
                                        [
                                            word
                                            for word in lesson.data
                                            if lesson.data[word]["progress"]
                                            < self.target_progress
                                        ]
                                    )
                                    == 0
                                ):
                                    print(
                                        "No words to practice. Increase target progress or reset progress."
                                    )
                                    break
                                print("\nSelect a mode:")
                                print(
                                    f"(1) Practice translation from {LANG_NAME_MAP[language]} audio"
                                )
                                print(
                                    f"(2) Practice spelling in {LANG_NAME_MAP[language]}"
                                )
                                print(
                                    f"(3) Practice translation to English from {LANG_NAME_MAP[language]}"
                                )
                                print("(4) Exit")
                                mode = input(">> ").strip()
                                # pygame.mixer.init()
                                if mode == "1":
                                    session.practice_lesson(
                                        lambda lesson_data, language, word: session.general_prompt(
                                            session.prompt_translation_from_audio,
                                            word,
                                        )
                                    )
                                elif mode == "2":
                                    session.practice_lesson(
                                        lambda lesson_data, language, word: session.general_prompt(
                                            session.prompt_target_word_from_translation,
                                            word,
                                        )
                                    )
                                elif mode == "3":
                                    session.practice_lesson(
                                        lambda lesson_data, language, word: session.general_prompt(
                                            session.prompt_translation_from_target_word,
                                            word,
                                        )
                                    )
                                elif mode == "4":
                                    lesson.save_lesson()
                                    break
                                else:
                                    print("Invalid choice. Please try again.")
                        elif option == "3":
                            lesson.lesson_info(language, self.target_progress)
                        elif option == "4":
                            lesson.show_words()
                        elif option == "5":
                            if session.confirm_choice():
                                lesson.reset_progress()
                        elif option == "6":
                            if session.confirm_choice():
                                print("Enter progress value to set:")
                                progress = input(">> ").strip()
                                try:
                                    progress = int(progress)
                                    lesson.reset_progress(progress)
                                    print(f"Progress set to {progress} for all words.")
                                except ValueError:
                                    print("Invalid input.")
                        elif option == "7":
                            print("Enter goal progress value:")
                            try:
                                self.target_progress = int(input(">> ").strip())
                                print(f"Goal progress set to {self.target_progress}.")
                            except ValueError:
                                print("Invalid input, must be integer.")
                        elif option == "8":
                            lesson.save_lesson()
                            break
                        else:
                            print("Invalid choice. Please try again.")

                except KeyboardInterrupt:
                    lesson.save_lesson()
                    print("Goodbye!")
                    sys.exit()

            except KeyboardInterrupt:
                # lesson.save_lesson()
                print("Goodbye!")
                sys.exit()
            except Exception as e:
                print(f"An error occurred: {e}")


if __name__ == "__main__":
    app = ProfessorKROApp()
    app.run()
