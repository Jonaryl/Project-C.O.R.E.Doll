import json
import yaml

class FileWrite:
    def write_json(self, file_path, obj_to_add):
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                data.append(obj_to_add)
                #print("data", data)
                #print("obj_to_add", obj_to_add)
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4, ensure_ascii=False)