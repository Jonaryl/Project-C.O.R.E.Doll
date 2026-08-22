from pathlib import Path

class KeyVar:
    # Path(__file__).parent
    CONVERSATION_MODEL = "qwen3:8b"
    FAST_DECISION_MODEL = "qwen3:0.6b"

    AUDIO_DATABASE_PATH =  Path(__file__).parent.parent / "library" / "database" / "voice" / "voice_database.db"

    MESSAGEJSON = Path(__file__).parent.parent / "library" / "memories" / "temporary" / "CurrentDiscussion.json"

    AUDIO_CONFIG = Path(__file__).parent.parent / "configs" / "audio.json"

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
        return self.AUDIO_DATABASE_PATH
    
    def get_message_json(self):
        return self.MESSAGEJSON

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
        return self.STATE_PATH
    def get_relationship(self):
        return self.RELATIONSHIP_PATH

    def get_audio_config(self):
        return self.AUDIO_CONFIG

    
    def get_test_audio(self):
        return self.TEST_AUDIO