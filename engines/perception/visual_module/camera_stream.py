import queue
import threading

import cv2
import requests

from tools.file_r import FileRead
from tools.keyVar import KeyVar

key_var = KeyVar()
file_read = FileRead()

class CameraSteam:
    def __init__(self, input_type):
        self.private_config = file_read.read_yaml(key_var.get_private_config())
        self.camera_url = self.private_config["camera"]["url"]

        self.frame_queue = queue.Queue(maxsize=1)
        self.running = False
        self.thread = None

        self.camera_input = ""
        if input_type == "camera_url":
            self.camera_input = self.camera_url

    def main(self):
        print("CameraSteam ----- main ---- self.camera_input === ", self.camera_input)
        self.running = True

        self.thread = threading.Thread(
            target=self.video_capture,
            name="CameraSteam",
            daemon=True
        )

        self.thread.start()

    def video_capture(self):
        print(f"video_capture ----- main -----  self.camera_input/video == {self.camera_input}/video")
        self.set_front_camera(True)
        cap = cv2.VideoCapture(f"{self.camera_input}/video")
        
        if not cap.isOpened():
            print("Impossible de se connecter à la caméra")
            self.stop()
            return

        while self.running:
            ret, frame = cap.read()

            if not ret:
                print("Impossible de lire une image")
                break
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self.frame_queue.put_nowait(frame)
            except queue.Full:
                pass
            #time.sleep(0.01)
        cap.release()

    def set_front_camera(self, enabled=True):
        value = "on" if enabled else "off"

        response = requests.get(
            f"{self.camera_url}/settings/ffc",
            params={"set": value}
        )
        return response.ok
    def get_frame(self):
        try:
            return self.frame_queue.get_nowait()
        except queue.Empty:
            return None
    def stop(self):
        self.running = False
