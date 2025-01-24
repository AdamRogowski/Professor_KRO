import json
import os


class User:
    def __init__(self, user_directory):
        self.user_directory = user_directory
        self.cycle_prompts = None
        self.default_progress = None
        self.load_user_data()

    def load_user_data(self):
        user_data_file = os.path.join(self.user_directory, "user_data.json")
        if os.path.exists(user_data_file):
            with open(user_data_file, "r") as file:
                user_data = json.load(file)
                self.cycle_prompts = user_data.get("cycle_prompts", 0)
                self.default_progress = user_data.get("default_progress", 0)
        else:
            print(f"No user data file found in {self.user_directory}")


# Example usage:
# user = User('/path/to/user/directory')
# print(user.cycle_prompts)
# print(user.default_progress)
