


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
        {user_input}
        """
        print("ConversationPrompt create_prompt Prompt :", prompt)

        return prompt