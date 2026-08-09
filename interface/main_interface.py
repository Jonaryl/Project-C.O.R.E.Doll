import customtkinter
import asyncio
from interface.i_chatbox import Message_frame

customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("dark-blue")

class App(customtkinter.CTk):
    def __init__(self, agent=None):
        super().__init__()

        self.title("Main Interface")
        self.geometry("1000x800") 
        self.main_view = MainTab(master=self, agent=agent)
        self.main_view.grid(row=0, column=0, padx=20, pady=20)
        self.grid_columnconfigure(0, weight=1)


class MainTab(customtkinter.CTkTabview):
    def __init__(self, master, agent=None, **kwargs):
        super().__init__(master, **kwargs)
        self.agent = agent

        self.configure(width=900, height=800)   
        self.add("Main")

        self.process = None
        self.running = False

        # Message Frame
        
        self.add("Messages")
        self.my_frame = Message_frame(master=self.tab("Messages"), width=800, height=500)
        self.my_frame.grid(row=0, column=0, columnspan=2, padx=20, pady=20)

        self.User = customtkinter.CTkTextbox(master=self.tab("Messages"), height=20, width=300, wrap="word")
        self.User.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        self.NewMessage = customtkinter.CTkTextbox(master=self.tab("Messages"), height=100, width=700, wrap="word")
        self.NewMessage.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)

        self.NewMessageSend = customtkinter.CTkButton(master=self.tab("Messages"), text="Send", command=self.sendMessage_event)
        self.NewMessageSend.grid(row=2, column=1, sticky="nsew", padx=10, pady=5)


    def sendMessage_event(self):
        message = self.NewMessage.get("1.0", "end").strip()
        user = self.User.get("1.0", "end").strip()
        if not message:
            return

        self.agent.receive_user_input(user_input=message, user=user)

        self.NewMessage.delete("1.0", "end") 
        self.my_frame.refresh()

