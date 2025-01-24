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
CYCLE_PROMPTS = 8


def load_lesson(file_path):
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
                        row["usage"] if row["usage"] and row["usage"].strip() else ""
                    ),
                }
                for row in reader
            }
        return lesson_data
    except (KeyError, ValueError) as e:
        print(f"Error loading lesson data: {e}")
        return {}


def save_lesson(file_path, lesson_data):
    """Save lesson data back to the specified CSV file."""
    try:
        with open(file_path, mode="w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(
                file, fieldnames=["word", "translation", "progress", "usage"]
            )
            writer.writeheader()
            for word, data in lesson_data.items():
                writer.writerow(
                    {
                        "word": word,
                        "translation": data["translation"],
                        "progress": data["progress"],
                        "usage": data["usage"],
                    }
                )
        # print(f"Lesson data saved successfully to {file_path}.")
    except Exception as e:
        print(f"Error saving lesson data: {e}")


def play_text(text, language):
    """Play text audio in the given language."""
    try:
        tts = gTTS(text, lang=language)
        audio_data = io.BytesIO()
        tts.write_to_fp(audio_data)
        audio_data.seek(0)
        sound = pygame.mixer.Sound(audio_data)
        sound.play()
        while pygame.mixer.get_busy():
            pygame.time.Clock().tick(10)
    except Exception as e:
        print(f"Error playing text: {e}")


def confirm_choice(prompt="Are you sure? (yes/no): "):
    # Ask the user if they want to continue or exit
    print(prompt)
    answer = input(">> ").strip().lower()
    return answer in {"yes", "y"} or answer == ""


def show_words(lesson_data):
    """Display all words in the lesson."""
    print("ID | Word | Translation | Progress | Usage")
    idx = 1
    for word in lesson_data:
        print(
            f"{idx} | {word} | {lesson_data[word]['translation']} | {lesson_data[word]['progress']} | {lesson_data[word]['usage']}"
        )
        idx += 1


def reset_progress(lesson_data, default_progress=DEFAULT_PROGRESS):
    for word in lesson_data:
        lesson_data[word]["progress"] = default_progress
    print("Progress reset for all words.")


def lesson_info(lesson_name, lesson_data, language, target_progress):
    print(f"file: {lesson_name}")
    print(f"Language: {LANG_NAME_MAP[language]}")
    print(f"Target progress: {target_progress}")
    print(f"Number of words: {len(lesson_data)}")
    print(
        f"Words to practice: {len([word for word in lesson_data if lesson_data[word]['progress'] < target_progress])}"
    )
    print(
        f"Words completed: {len([word for word in lesson_data if lesson_data[word]['progress'] >= target_progress])}"
    )


def practice_lesson(lesson_data, mode_func, language=None, target_progress=4):
    """
    Practice the lesson using the specified prompting mode.

    Args:
        lesson_data (dict): The lesson data containing words, translations, and progress.
        mode_func (callable): The general_prompt function with a specific prompting mode.
        language (str): The target language.
        target_progress (int): The target progress to complete the lesson.
    """

    while True:
        # Initialize cycle status: Track if each word has been answered correctly in the current cycle
        cycle_status = {
            word: False
            for word in lesson_data
            if lesson_data[word]["progress"] < target_progress
        }

        if not cycle_status:
            print("No words to practice")
            break

        # Save the initial progress for comparison later
        initial_progress = {
            word: lesson_data[word]["progress"] for word in cycle_status
        }

        # Convert the cycle status to a list of words
        words_to_practice = list(cycle_status.keys())

        # Split the words into windows of up to CYCLE_PROMPTS
        windows = [
            words_to_practice[i : i + CYCLE_PROMPTS]
            for i in range(0, len(words_to_practice), CYCLE_PROMPTS)
        ]

        # Track if every word's progress has decreased
        cycle_progress_increased = {word: False for word in lesson_data}

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
                    prompt_status = mode_func(lesson_data, language, word)
                    if prompt_status == -1:
                        return  # -1 = exit code
                    elif prompt_status == 0:  # answered correctly
                        remaining_words.remove(word)

                    # Check if the progress has decreased by 1 compared to the initial value
                    if lesson_data[word]["progress"] > initial_progress[word]:
                        cycle_progress_increased[word] = (
                            True  # Mark as progress decreased
                        )

        # Check if all words in the cycle have had their progress decreased
        if all(cycle_progress_increased[word] for word in lesson_data):
            print("Lesson complete!")
            break

        if not confirm_choice("Do you want to start a new lesson? (yes/no): "):
            break


def prompt_translation_from_audio(lesson_data, language, word):
    play_text(word, language)
    print("Translation to English:")
    answer = input(">> ").strip()
    return answer, lesson_data[word]["translation"]


def prompt_target_word_from_translation(lesson_data, language, word):
    print(f"English word: {lesson_data[word]['translation']}")
    print(f"Spell in {LANG_NAME_MAP[language]}:")
    answer = input(f">> ").strip()
    return answer, word


def prompt_translation_from_target_word(lesson_data, language, word):
    print(f"{LANG_NAME_MAP[language]} word: {word}")
    print("Translation to English:")
    answer = input(">> ").strip()
    return answer, lesson_data[word]["translation"]


def general_prompt(lesson_data, language, mode, word=None):
    if not word:
        print("Error: Word not provided for this mode.")
        return 1

    answer, expected_answer = mode(lesson_data, language, word)

    while True:

        if answer == expected_answer:
            if mode == prompt_target_word_from_translation:
                play_text(word, language)
            print("Correct!")
            lesson_data[word]["progress"] += 1
            return 0
        elif answer in {"exit", "quit", "-e", "-q", "-exit", "-quit"}:
            print("Exiting this mode.")
            return -1
        elif answer in {"help", "-h", "?", "-?", "commands", "-help"}:
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
            answer = input(">> ").strip()
        elif answer in {"hint", "-hint"}:
            print(f"The first letter of the word is '{expected_answer[0]}'.")
            answer = input(">> ").strip()
        elif answer in {"usage", "-usage", "context", "-context", "-u"}:
            if not lesson_data[word]["usage"]:
                print("No usage/context provided for this word.")
            else:
                print(f"{lesson_data[word]['usage']}")
            answer = input(">> ").strip()
        elif answer in {"progress", "-progress", "-p"}:
            print(f"Current progress: {lesson_data[word]['progress']}")
            answer = input(">> ").strip()
        elif answer in {"skip", "-skip", "accept", "-accept", "-s"}:
            print("Skipping this word.")
            lesson_data[word]["progress"] += 1
            return 0
        elif answer in {"repeat", "-repeat", "play", "-play"}:
            print("Repeating the word...")
            play_text(word, language)
            answer = input(">> ").strip()
        else:
            print(f"Incorrect. The correct answer is '{expected_answer}'.")
            lesson_data[word]["progress"] -= 1
            return 1


def main():
    print("Welcome to the Professor KRO App!")

    target_progress = 4

    while True:

        print("\nAvailable lessons:")

        lessons = [
            (
                file,
                file.split("_")[-1].split(".")[0],
            )  # Extract language code from file name
            for file in os.listdir(LESSONS_DIR)
            if file.endswith(".csv")
        ]

        try:
            # Display available lessons
            for idx, (file, lang) in enumerate(lessons, start=1):
                print(f"({idx}) {file} (Language: {LANG_NAME_MAP[lang]})")

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
            lesson_data = load_lesson(os.path.join(LESSONS_DIR, lesson_file))

            while True:
                print("\nSelect an option:")
                print("(1) Practice")
                print("(2) Lesson Information")
                print("(3) Show words")
                print("(4) Reset Progress")
                print("(5) Reset to input Progress")
                print("(6) Set target Progress")
                print("(7) Quit lesson")
                option = input(">> ").strip()
                if option == "1":
                    while True:
                        if (
                            len(
                                [
                                    word
                                    for word in lesson_data
                                    if lesson_data[word]["progress"] < target_progress
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
                        print(f"(2) Practice spelling in {LANG_NAME_MAP[language]}")
                        print(
                            f"(3) Practice translation to English from {LANG_NAME_MAP[language]}"
                        )
                        print("(4) Exit")
                        mode = input(">> ").strip()
                        pygame.mixer.init()
                        if mode == "1":
                            practice_lesson(
                                lesson_data,
                                lambda lesson_data, language, word: general_prompt(
                                    lesson_data,
                                    language,
                                    prompt_translation_from_audio,
                                    word,
                                ),
                                language,
                                target_progress,
                            )
                        elif mode == "2":
                            practice_lesson(
                                lesson_data,
                                lambda lesson_data, language, word: general_prompt(
                                    lesson_data,
                                    language,
                                    prompt_target_word_from_translation,
                                    word,
                                ),
                                language,
                                target_progress,
                            )
                        elif mode == "3":
                            practice_lesson(
                                lesson_data,
                                lambda lesson_data, language, word: general_prompt(
                                    lesson_data,
                                    language,
                                    prompt_translation_from_target_word,
                                    word,
                                ),
                                language,
                                target_progress,
                            )
                        elif mode == "4":
                            save_lesson(
                                os.path.join(LESSONS_DIR, lesson_file), lesson_data
                            )
                            break
                        else:
                            print("Invalid choice. Please try again.")
                elif option == "2":
                    lesson_info(lesson_file, lesson_data, language, target_progress)
                elif option == "3":
                    show_words(lesson_data)
                elif option == "4":
                    if confirm_choice():
                        reset_progress(lesson_data)
                elif option == "5":
                    if confirm_choice():
                        print("Enter progress value to set:")
                        progress = input(">> ").strip()
                        try:
                            progress = int(progress)
                            reset_progress(lesson_data, progress)
                            print(f"Progress set to {progress} for all words.")
                        except ValueError:
                            print("Invalid input.")
                elif option == "6":
                    print("Enter goal progress value:")
                    target_progress = input(">> ").strip()
                    try:
                        target_progress = int(target_progress)
                        print(f"Goal progress set to {target_progress}.")
                    except ValueError:
                        print("Invalid input.")

                elif option == "7":
                    save_lesson(os.path.join(LESSONS_DIR, lesson_file), lesson_data)
                    break
                elif option == "maryse is a rat":
                    try:
                        with open("ascii_art.txt", "r", encoding="utf-8") as art_file:
                            ascii_art = art_file.read()
                            print(ascii_art)
                    except FileNotFoundError:
                        print("ascii_art.txt file not found.")
                    except Exception as e:
                        print(f"An error occurred while reading ascii_art.txt: {e}")
                else:
                    print("Invalid choice. Please try again.")

        except KeyboardInterrupt:
            save_lesson(os.path.join(LESSONS_DIR, lesson_file), lesson_data)
            print("Goodbye!")
            sys.exit()
        except Exception as e:
            print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
