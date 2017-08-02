import os

class FileHelper:

    @staticmethod
    # Create a directory if it doesn't exist
    def ensure_directory(dirname):
        if not os.path.exists(dirname):
            os.makedirs(dirname)
