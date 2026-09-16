from pathlib import Path

class KeyVar:
    # Path(__file__).parent
    CONVERSATION_MODEL = "qwen3:8b"
    FAST_DECISION_MODEL = "qwen3:0.6b"

    AUDIO_DATABASE_PATH =  Path(__file__).parent.parent / "library" / "database" / "voice" / "voice_database.db"
    VISION_DATABASE_PATH =  Path(__file__).parent.parent / "library" / "database" / "vision" / "vision_database.db"

    MESSAGEJSON = Path(__file__).parent.parent / "library" / "memories" / "temporary" / "CurrentDiscussion.json"
    TEMPORARY_PATH = Path(__file__).parent.parent / "library" / "memories" / "temporary"

    PRIVATE_CONFIG = Path(__file__).parent.parent / "configs" / "configs.yaml"
    AUDIO_CONFIG = Path(__file__).parent.parent / "configs" / "audio.json"
    VIDEO_CONFIG = Path(__file__).parent.parent / "configs" / "video.json"

    IMMUTABLE_RULE_PATH = Path(__file__).parent.parent / "library" / "rules" / "immutable_rules.md"
    CONVERSATION_RULE_PATH = Path(__file__).parent.parent / "library" / "rules" / "conversation_engine.md"
    KNOWLEDGE_RULE_PATH = Path(__file__).parent.parent / "library" / "rules" / "knowledge.md"
    MEMORIES_RULE_PATH = Path(__file__).parent.parent / "library" / "rules" / "memories.md"
    RELATIONSHIP_RULE_PATH = Path(__file__).parent.parent / "library" / "rules" / "relationship.md"
    STATE_RULE_PATH = Path(__file__).parent.parent / "library" / "rules" / "state.md"
    PERSONALITY_TRAIT_PATH = Path(__file__).parent.parent / "library" / "rules" / "personality_trait.json"
    RESPONSE_FORMAT_PATH = Path(__file__).parent.parent / "library" / "rules" / "response_format.md"

    STATE_PATH = Path(__file__).parent.parent / "library" / "consciousness" / "state.json"
    RELATIONSHIP_PATH = Path(__file__).parent.parent / "library" / "consciousness" / "relationship.json"

    TEST_AUDIO = Path(__file__).parent.parent / "_test" / "walking.mp3"

    def get_conversation_model(self):
        return self.CONVERSATION_MODEL
    def get_fast_model(self):
        return self.FAST_DECISION_MODEL

    def get_voice_database(self):
        self.AUDIO_DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        return self.AUDIO_DATABASE_PATH

    def get_vision_database(self):
        self.VISION_DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        return self.VISION_DATABASE_PATH

    def get_message_json(self):
        self.MESSAGEJSON.parent.mkdir(parents=True, exist_ok=True)
        return self.MESSAGEJSON
    
    def get_temporary_path(self):
        self.TEMPORARY_PATH.mkdir(parents=True, exist_ok=True)
        return self.TEMPORARY_PATH

    def get_immutable_rules(self):
        return self.IMMUTABLE_RULE_PATH
    def get_conversation_rules(self):
        return self.CONVERSATION_RULE_PATH
    def get_knowledge_rules(self):
        return self.KNOWLEDGE_RULE_PATH
    def get_memories_rules(self):
        return self.MEMORIES_RULE_PATH
    def get_relationship_rules(self):
        return self.RELATIONSHIP_RULE_PATH
    def get_state_rules(self):
        return self.STATE_RULE_PATH
    def get_personality_trait(self):
        return self.PERSONALITY_TRAIT_PATH
    def get_response_format(self):
        return self.RESPONSE_FORMAT_PATH
    
    def get_state(self):
        self.STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        return self.STATE_PATH
    def get_relationship(self):
        self.RELATIONSHIP_PATH.parent.mkdir(parents=True, exist_ok=True)
        return self.RELATIONSHIP_PATH


    def get_audio_config(self):
        return self.AUDIO_CONFIG
    def get_video_config(self):
        return self.VIDEO_CONFIG
    def get_private_config(self):
        return self.PRIVATE_CONFIG

    
    def get_test_audio(self):
        return self.TEST_AUDIO