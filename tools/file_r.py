import json
import yaml

class FileRead():
    def read_json_file(self, file_path):
        print("file_path", file_path)
        with open(file_path, 'r', encoding="utf-8") as f:
            return json.load(f)

    def read_text(self, file_path):
        with open(file_path, 'r') as f:
            return f.read()

    def read_yaml(self, file_path):
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)