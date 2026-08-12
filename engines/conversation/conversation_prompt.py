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

        #print ("final prompt = ", finalprompt)
        return finalprompt


    def add_rules_to_prompt(self, prompt):
        updated_prompt = prompt

        conversation_rules = file_r.read_text(key_var.get_conversation_rules())
        immutable_rules = file_r.read_text(key_var.get_immutable_rules())
        state_rules = file_r.read_text(key_var.get_state_rules())
        state_rules_json = self.state_format_neural(file_r.read_json_file(key_var.get_state()))
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
        "--NEURAL_STATE_JSON--",
        state_rules_json)

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

    def state_format_neural(self, state):
        sections = []

        sections.append(self.state_format_identity(state["identity"]))
        sections.append(self.state_format_cognition(state["cognition"]))
        sections.append(self.state_format_capabilities(state["capabilities"]))
        sections.append(self.state_format_personal_values(state["personal_values"]))

        return "\n\n".join(sections)
        

    def state_format_identity(self, identity):
        text = ["## IDENTITY"]

        if identity.get("name"):
            text.append(f"Name: {identity['name']}")
        if identity.get("gender"):
            text.append(f"gender: {identity['gender']}")

        personality = identity.get("personality", {})

        if personality.get("traits"):
            personality_trait_count = 0
            text.append("\nPersonality traits:")

            for trait in personality["traits"]:
                if trait['name'] != "":
                    personality_trait_count += 1
                    text.append(
                        f"- {trait['name']} (strength: {trait['strength']:.2f}, confidence: {trait['confidence']:.2f})"
                    )
            if personality_trait_count == 0:
                text.append("\n- None established yet.")

        return "\n".join(text)

    def get_state_intensity_text(self, value):
        text = ""
        if value <= 0.2:
            text = "very low : "
        elif value <= 0.4:
            text = "low : "
        elif value <= 0.6:
            text = "moderate : "
        elif value <= 0.8:
            text = "high : "
        else:
            text = "very high : "
        return text

    def state_format_cognition(self, cognition):
        text = ["## COGNITIVE STATE"]

        current_attention = cognition.get("current_attention", {})
        if current_attention["subject"] and current_attention["reason"]:
            text.append("\nCurrent attention:")
            text.append(f"\nYour attention is currently about '{current_attention["subject"]}', the reason is : '{current_attention["reason"]}'. ")

            text.append(f"Importante = {self.get_state_intensity_text(current_attention["importance"])} : {current_attention["importance"]}")

        emotionnal_state = cognition.get("emotionnal_state", {})
        if emotionnal_state["primary"]:
            intensity = f"Intensity = {self.get_state_intensity_text(emotionnal_state["intensity"])} : {current_attention["intensity"]}"
            text.append("\nEmotionnal state:")
            text.append(f"\nYou mainly feel {emotionnal_state["primary"]}, {intensity} intensity.")

            causes = emotionnal_state.get("causes", [])

            if causes:
                text.append("\nThe causes you feel that way :")
                text.append(", ".join(str(c) for c in causes))

        if cognition.get("current_plan"):
            text.append(f"Your current plan is : {cognition['current_plan']}")

        print("state_format_cognition", text)
        return "\n".join(text)
    
    def state_format_capabilities(self, capabilities):
        text = ""

        if capabilities:
            text = ["## CAPABILITIES"]
            for capability in capabilities:
                available = "unavailable"
                online = ""
                if capability["available"]:
                    online = "/ offline"
                    available = "available"

                if capability["online"]:
                    online = "/ online"
                text.append(f"\n{capability["module"]} : {available} {online} - {capability["description"]}")

        print("state_format_capabilities", text)
        return "\n".join(text)

    def state_format_personal_values(self, personal_values):
        text = ["## YOUR PERSONAL VALUES"]

        for key, label in [("preferences", "Preferences"), ("interests", "Interests"), ("morals", "Morals")]:
            items = personal_values.get(key, [])
            text.append(f"\n{label} :")
            if items:
                text.append(", ".join(str(item) for item in items))
            else:
                text.append("- None established yet.")

        print("state_format_personal_values", text)
        return "\n".join(text)