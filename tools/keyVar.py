from pathlib import Path

class KeyVar:


    # Path(__file__).parent
    DESCRIPTION_PATH = Path(__file__).parent.parent / "library" / "personality" / "Description.yaml"
    EMOTION_PATH = Path(__file__).parent.parent / "library" / "personality" / "Emotions.json"
    CONTEXT_PATH = Path(__file__).parent.parent / "library" / "personality" / "Context.yaml"
    MESSAGEJSON = Path(__file__).parent.parent / "library" / "memories" / "CurrentDiscussion.json"


    def get_description_path(self):
        print(f"description_path: {self.DESCRIPTION_PATH}")
        return self.DESCRIPTION_PATH

    def get_emotion_path(self):
        print(f"emotion_path: {self.EMOTION_PATH}")
        return self.EMOTION_PATH
    
    def get_context_path(self):
        print(f"context_path: {self.CONTEXT_PATH}")
        return self.CONTEXT_PATH
    
    def get_master_name(self):
        print(f"master_name: {self.MASTER_NAME}")
        return self.MASTER_NAME
    
    def get_message_json(self):
        return self.MESSAGEJSON