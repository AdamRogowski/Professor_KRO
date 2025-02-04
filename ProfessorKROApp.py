import os
import sys
from constants import LANG_NAME_MAP, LESSONS_DIR
from Lesson import Lesson
from PracticeSession import PracticeSession


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
                                # session.target_progress = int(input(">> ").strip())
                                self.target_progress = int(input(">> ").strip())
                                lesson.save_lesson()
                                session = PracticeSession(
                                    lesson, language, self.target_progress
                                )
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
            # except Exception as e:
            #   print(f"An error occurred: {e}")
