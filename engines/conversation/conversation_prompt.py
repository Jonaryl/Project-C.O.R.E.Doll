from tools.file_r import FileRead
from tools.keyVar import KeyVar

key_var = KeyVar()
file_r = FileRead()

class ConversationPrompt:
    def manage_user_messages(self, messages):
        prompt = "# User input : \n"
        for message in messages:
            prompt += f"- user: {message["user"]}\n"
            prompt += f"- message: {message["content"]}\n"
        return prompt

    def create_prompt(self, all_events):
        user_input = self.manage_user_messages(all_events["messages"])

        prompt = f"""
--Conversation--

{user_input}
"""
        print("ConversationPrompt create_prompt Prompt :", prompt)

        finalprompt = self.add_rules_to_prompt(prompt)

        print ("final prompt = ", finalprompt)
        #return prompt


    def add_rules_to_prompt(self, prompt):
        updated_prompt = prompt

        conversation_rules = file_r.read_text(key_var.get_conversation_rules())
        immutable_rules = file_r.read_text(key_var.get_immutable_rules())
        state_rules = ""
        memories_rules = ""
        knowledge_rules = ""
        relationship_rules = ""

        updated_prompt = updated_prompt.replace(
        "--Conversation--",
        conversation_rules)

        updated_prompt = updated_prompt.replace(
        "--IMMUTABLE_RULES--",
        immutable_rules)

        updated_prompt = updated_prompt.replace(
        "--SELF_STATE--",
        state_rules)

        updated_prompt = updated_prompt.replace(
        "--MEMORIES--",
        memories_rules)

        updated_prompt = updated_prompt.replace(
        "--KNOWLEDGE--",
        knowledge_rules)

        updated_prompt = updated_prompt.replace(
        "--RELATIONSHIP--",
        relationship_rules)

        return updated_prompt