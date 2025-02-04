import csv
from constants import DEFAULT_PROGRESS, LANG_NAME_MAP


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
