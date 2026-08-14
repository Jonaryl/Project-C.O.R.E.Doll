from tools.file_r import FileRead
from tools.file_w import FileWrite
from tools.keyVar import KeyVar

file_read = FileRead()
file_write = FileWrite()
key_var = KeyVar()

class MemoryEngine:

    def add_to_discussion(self, message):
        path = key_var.get_message_json()

        #print("message", message)

        entry = {
        "id": message.id,
        "user": message.data.get("user"),
        "message": message.data.get("content"),
        "correlation_id": message.correlation_id,
        "time": message.timestamp
        }
        
        #print("entry : ", entry)
        file_write.write_json(path, entry)
