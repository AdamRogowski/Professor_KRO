import random
from constants import CYCLE_PROMPTS, LANG_NAME_MAP
from AudioPlayer import AudioPlayer


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

    @property
    def target_progress(self):
        return self._target_progress

    @target_progress.setter
    def target_progress(self, value):
        if value < 1:
            raise ValueError("Target progress must be at least 1.")
        self._target_progress = value

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
                self.lesson.save_lesson()
                break

            if not self.confirm_choice("Do you want to start a new lesson? (yes/no): "):
                self.lesson.save_lesson()
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
            # elif answer in self.EDIT_COMMANDS:
            #    return self.edit_word(word)
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
            # Remove the old word entry and add the new word entry
            self.lesson.data[new_word] = self.lesson.data.pop(word)
            data = self.lesson.data[new_word]
            data["word"] = new_word
        if new_translation:
            data["translation"] = new_translation
        if new_usage:
            data["usage"] = new_usage

        print("Word updated.")
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
    - ['repeat', '-repeat', 'play', '-play']: Repeats the word by playing its audio."""
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
        # elif command in self.EDIT_COMMANDS:
        #    return self.edit_word(word)
        elif (
            command in self.SKIP_COMMANDS and not correct
        ):  # Skip possible only if the answer was incorrect
            print("Answer accepted")
            self.lesson.data[word]["progress"] += 1
            return 0
        if correct:
            self.lesson.data[word]["progress"] += 1
            return 0
        else:
            if self.lesson.data[word]["progress"] > 0:
                self.lesson.data[word]["progress"] -= 1
            return 1
