import time

import cv2

from engines.perception.visual_module.camera_stream import CameraSteam
from engines.perception.visual_module.focus_vision_module import FocusVisionModule
from engines.perception.visual_module.multi_vision_module import MultiVisionModule
from engines.perception.visual_module.visual_classes import (
    VisionObject,
    VisionPerson,
)
from engines.perception.visual_module.visual_frame_analysis import VisualFrameAnalisys
from engines.perception.visual_module.visual_recognition import VisualRecognition
from tools.file_r import FileRead
from tools.keyVar import KeyVar

key_var = KeyVar()
file_read = FileRead()
visual_frame_analysis = VisualFrameAnalisys()

class VisualModule:
    def __init__(self, bus):
        self.message_bus = bus

        self.persons: dict[int, VisionPerson] = {}
        self.objects: dict[int, VisionObject] = {}

        self.video_config = file_read.read_json_file(key_var.get_video_config())
        self.camera_input = self.video_config["camera_input"]

        self.camera_stream = CameraSteam(self.camera_input)
        self.visual_recognition = VisualRecognition()
        self.multi_vision_module = MultiVisionModule(self.persons,  self.objects, self.visual_recognition)
        self.focus_vision_module = FocusVisionModule(self.persons,  self.objects)

        self.running = False

    def main(self):
        self.camera_stream.main()
        self.running = True

        while self.running:
            frame = self.camera_stream.get_frame()
            if frame is None:
                time.sleep(0.01) 
                continue

            self.process_frame(frame)

            if cv2.waitKey(1) == 27:
                self.camera_stop()
                self.running = False
                
        self.close()
        cv2.destroyAllWindows()

    def process_frame(self, frame):
        self.multi_vision_module.process_frame(frame, self.process_multi_vision)


    def close(self):
        self.focus_vision_module.close()

    def process_multi_vision(self, message):
        persons = message.get('persons', {})
        last_image = message.get('last_image', {})
        frame = last_image

        if persons is None or not persons or len(persons) == 0:
            identity = None
        else:
            for track_id, person in persons.items():
                identity = person.identity

        focused_person = None
        for person in persons.values():
            if person.is_focused:
                focused_person = person
                break

        if focused_person is None:
            frame = last_image
            framerate = "slow"
        else:
            x1, y1, x2, y2 = focused_person.box_positions.tolist()
            
            pad = 40
            h, w = last_image.shape[:2]
            x1 = max(0, int(x1) - pad)
            y1 = max(0, int(y1) - pad)
            x2 = min(w, int(x2) + pad)
            y2 = min(h, int(y2) + pad)

            frame = last_image[y1:y2, x1:x2]
            framerate = "fast"

        self.focus_vision_module.process_frame(frame, framerate, identity, self.process_focus_vision)

    def process_focus_vision(self, message):
        if message["action"] == "Stop":
            self.multi_vision_module.stop_analisys()

    def camera_stop(self):
        self.camera_stream.stop()




