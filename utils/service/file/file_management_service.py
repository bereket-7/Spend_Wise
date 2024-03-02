import os

class FileManagementService:
    def __init__(self, storage_path):
        self.storage_path = storage_path

    def list_files(self):
        return os.listdir(self.storage_path)

    def delete_file(self, filename):
        file_path = os.path.join(self.storage_path, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        else:
            return False
