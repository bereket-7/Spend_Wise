import os

class FileUploadService:
    def __init__(self, storage_path):
        self.storage_path = storage_path

    def upload_file(self, file_data, filename):
        file_path = os.path.join(self.storage_path, filename)
        with open(file_path, 'wb') as f:
            f.write(file_data)
