import os

class FileDownloadService:
    def __init__(self, storage_path):
        self.storage_path = storage_path

    def download_file(self, filename):
        file_path = os.path.join(self.storage_path, filename)
        with open(file_path, 'rb') as f:
            return f.read()
