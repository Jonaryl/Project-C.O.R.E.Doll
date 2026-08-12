from tools.file_r import FileRead
from tools.file_w import FileWrite
from tools.keyVar import KeyVar

file_read = FileRead()
file_write = FileWrite()
key_var = KeyVar()

class MemoryEnigine:

    def add_to_discussion(self, username, message):
        path = key_var.get_message_json()
        file_write.write_json(path, message)
