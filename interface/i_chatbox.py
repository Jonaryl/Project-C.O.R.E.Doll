import customtkinter
import json

from tools.keyVar import KeyVar

key_var = KeyVar()

class Message_frame(customtkinter.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.load_messages()

    def refresh(self):
        self.load_messages()

    def load_messages(self):
        for widget in self.winfo_children():
            widget.destroy()

        nb_rows = 0

        with open(key_var.get_message_json(), "r", encoding="utf-8") as f:
            allMessage = json.load(f)   

            for i in range(len(allMessage)):
                if(allMessage[i]["user"] == "IA"):
                    self.textboxName = customtkinter.CTkLabel(master=self, text=allMessage[i]["user"])
                    self.textboxName.grid(row=nb_rows, column=0, sticky="nsew", pady=5)
                    nb_rows += 1

                    self.textbox = customtkinter.CTkLabel(master=self, text=allMessage[i]["message"], width=700, anchor="w", wraplength=680)
                    self.textbox.grid(row=nb_rows, column=2, sticky="nsew", pady=5)
                    nb_rows += 1
                    
                else:
                    self.textboxReName = customtkinter.CTkLabel(master=self, text=allMessage[i]["user"], anchor="e")
                    self.textboxReName.grid(row=nb_rows, column=4, sticky="nsew", padx=10, pady=5)
                    nb_rows += 1

                    self.textboxRe = customtkinter.CTkLabel(master=self, text=allMessage[i]["message"], width=700, anchor="e", wraplength=680)
                    self.textboxRe.grid(row=nb_rows, column=2, sticky="nsew", padx=10, pady=5)
                    nb_rows += 1

