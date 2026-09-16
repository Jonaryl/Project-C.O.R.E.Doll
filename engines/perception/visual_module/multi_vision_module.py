import queue
import threading
import time

import cv2

#from ollama import Image
from PIL import Image
from ultralytics import YOLO

from engines.perception.visual_module.visual_classes import (
    VisionObject,
    VisionPerson,
)
from engines.perception.visual_module.visual_recognition import VisualRecognition
from tools.file_r import FileRead
from tools.keyVar import KeyVar
from tools.manage_errors import ManageError

key_var = KeyVar()
file_read = FileRead()
manage_errors = ManageError()

class MultiVisionModule:
    def __init__(self, persons: dict[int, VisionPerson], objects: dict[int, VisionObject], visual_reco:VisualRecognition):
        self.persons = persons
        self.objects = objects
        self.visual_recognition = visual_reco

        self.temporary_path = key_var.get_temporary_path()
        self.last_image_path = self.temporary_path / "vision" / "last_image.jpg"
        self.last_image_path.parent.mkdir(parents=True, exist_ok=True)

        self.vision_path = key_var.get_vision_database()
        self.person_folder = self.vision_path.parent
        self.person_folder.mkdir(parents=True, exist_ok=True)

        self.video_config = file_read.read_json_file(key_var.get_video_config())
        self.yolo_model_name = self.video_config["yolo"]["yolo_model"]

        self.last_yolo_time = 0
        self.yolo_current_interval = 0
        self.yolo_interval_low = self.video_config["yolo"]["yolo_interval_low"]
        self.yolo_interval_high = self.video_config["yolo"]["yolo_interval_high"]

        self.process_data_time = self.video_config["yolo"]["process_data_time"]
        self.last_process_data_time = None

        self.yolo_current_interval = self.yolo_interval_high

        self.yolo_model = YOLO(self.yolo_model_name)

        self.fps_counter_start = time.perf_counter()
        self.fps_counter_frames = 0
        self.yolo_fps = 0.0

        self.last_annotated_frame = None
        self.last_image = None

    def change_yolo_framerate(self, speed):
        if speed == "low":
            self.yolo_current_interval = self.yolo_interval_low
        elif speed == "high":
            self.yolo_current_interval = self.yolo_interval_high

    def process_data(self, data):
        if manage_errors._error(
                variables={
                "data": data,
                "data.boxes": getattr(data, "boxes", None),
                "data.names": getattr(data, "names", None),
                "data.orig_img": getattr(data, "orig_img", None),
                "data.orig_shape": getattr(data, "orig_shape", None),
            },
            conditions={
                "data.boxes": lambda v: v is not None and len(v) >= 0,
                "data.names": lambda v: isinstance(v, (dict, list)),
                "data.orig_img": lambda v: v is not None and hasattr(v, "shape"),
            }
        ): 
            return


        boxes = data.boxes
        names = data.names
        speed = data.speed
        orig_img = data.orig_img
        orig_shape = data.orig_shape

        new_persons: dict[int, VisionPerson] = {}
        new_objects: dict[int, VisionObject] = {}

        for box in boxes:
            required_attrs = ['id', 'cls', 'conf', 'xyxy', 'xywh']
            attrs = {attr: getattr(box, attr, None) for attr in required_attrs}
            manage_errors._error(
                variables=attrs,
            )            
            if any(v is None for v in attrs.values()):
                continue

            track_id = int(box.id[0]) 
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])

            class_name = names[class_id]

            x1, y1, x2, y2 = box.xyxy[0].tolist()
            sx1, sy1, sx2, sy2 = box.xywh[0].tolist()

            if(class_name == "person"): 
                new_persons[track_id] = VisionPerson(
                    track_id=track_id,                    
                    identity=class_name,
                    identity_confidence=confidence,
                
                    box_sizes=box.xywh[0],
                    box_positions=box.xyxy[0],
                    
                    last_seen=0,
                    is_focused= True                
                )
            else:
                new_objects[track_id] = VisionObject(
                    track_id=track_id,

                    class_id=class_id,
                    class_name=class_name,

                    confidence=confidence,

                    box_sizes=box.xywh[0],
                    box_positions=box.xyxy[0],

                    last_seen= 0
                )                   

        manage_errors._error(
            variables={
                "new_persons": new_persons,
                "new_objects": new_objects,
                "orig_img": orig_img,
            }
        )

        self.update_person(new_persons, orig_img)
        self.update_object(new_objects)

        if len(self.persons) > 0 or len(new_persons) > 0:
            self.recover_lost_tracks(self.persons, new_persons, orig_img, True)
        if len(self.objects) > 0 or len(new_objects) > 0:
            self.recover_lost_tracks(self.objects, new_objects, orig_img, False)

        if len(self.persons) > 0 :
            self.cleanup_old_tracks(self.persons)
        if len(self.objects) > 0:
            self.cleanup_old_tracks(self.objects)
        # !!!!!!!!!!!!!!!!!!!!!! PROBLEME A PARTIR DE LA VERS PROCHAIN LOG
        score_persons = self.calcul_events_score(self.persons, True)
        score_objects = self.calcul_events_score(self.objects, False)


        manage_errors._error(
            variables={
                "score_persons": score_persons,
                "score_objects": score_objects,
            },
            conditions={
                "score_persons": lambda v: isinstance(v, (int, float)),
                "score_objects": lambda v: isinstance(v, (int, float)),
            }
        )


        final_score = score_persons + score_objects

        #img_rgb = cv2.cvtColor(orig_img, cv2.COLOR_BGR2RGB)
        #Image.fromarray(img_rgb).save(self.last_image_path)
        self.last_image = orig_img.copy()

        if False:
            print()
            print(" =============== data         : ===============")
            print(data)
            print(" =============== boxes        : ===============")
            print(boxes)
            print()
            print(" =============== names        : ===============")
            print(names)
            print()
            print(" =============== speed        : ===============")
            print(speed)
            print()
            print(" =============== orig_shape   : ===============")
            print(orig_shape)
            print()
        message = {
            "type": "multi_vision_data",
            "final_score": final_score,
            "last_image": self.last_image,
            "persons": self.persons
        }
        return message

    def stop_analisys(self):
        for id, person in self.persons.items():
            person.is_focused= False

    def process_frame(self, frame, process_message):
        now = time.perf_counter()
        message = {
                    "type": "multi_vision_data",
                    "final_score": 0,
                    "last_image": frame,
                    "persons": self.persons
        }
        if now - self.last_yolo_time < self.yolo_current_interval:
            #if self.last_annotated_frame is not None:
                #cv2.imshow("Vision", self.last_annotated_frame)
            #else:
                #cv2.imshow("Vision", frame)
            process_message(message)
            return
              
        self.last_yolo_time = now

        start = time.perf_counter()
        #results = self.yolo_model( frame, verbose=False, device=0)
        results = self.yolo_model.track( frame, persist=True, verbose=False, device=0)
        inference_time = time.perf_counter() - start

        fps = self.calcul_fps()
        
        annotated = results[0].plot()
        self.last_annotated_frame = annotated

        info = (
            f"YOLO FPS: {fps} | "
            f"Inference: {inference_time * 1000:.1f} ms"
        )

        #cv2.imshow("Vision", frame)
        #cv2.putText(annotated, info, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        #cv2.imshow("Vision", annotated)

        if self.last_process_data_time is None:
            self.last_process_data_time = time.monotonic() + self.process_data_time
        if self.timer_time() < 0:
            message = self.process_data(results[0])
            self.last_process_data_time = time.monotonic() + self.process_data_time            
        process_message(message)

    def update_person(self, new_persons, new_image):
        for track_id, obj in new_persons.items():
            if track_id in self.persons:
                self.persons[track_id].update_from(obj)
                self.persons[track_id].last_seen = 0

                if self.persons[track_id].face_embedding is None:
                    #print("/////////////////// NEW PERSON Uptade_person ////////////////////// identity = ", self.persons[track_id].identity )
                    self.new_person(self.persons[track_id], new_image, track_id, self.persons[track_id].database_id, self.persons[track_id].identity)

                events = self.event_managment(self.persons[track_id], is_person=True)
                self.persons[track_id].events = events

        for track_id in list(self.persons.keys()):
            if track_id not in new_persons:
                self.persons[track_id].last_seen += 1

    def update_object(self, new_objects):
        for track_id, obj in new_objects.items():
            if track_id in self.objects:
                self.objects[track_id].update_from(obj)
                self.objects[track_id].last_seen = 0

                events = self.event_managment(self.objects[track_id], is_person=False)
                self.objects[track_id].events = events

        for track_id in list(self.objects.keys()):
            if track_id not in new_objects:
                self.objects[track_id].last_seen += 1

    def recover_lost_tracks(self, stored: dict, current: dict, new_image, is_person: bool = False):
        lost_tracks = {
            tid: obj for tid, obj in stored.items()
            if obj.last_seen > 0 and obj.last_seen <= 3
        }
        new_tracks = {
            tid: obj for tid, obj in current.items()
            if tid not in stored
        }

        for new_id, new_obj in new_tracks.items():
            best_match_id = None
            best_score = 0.0

            for lost_id, lost_obj in lost_tracks.items():
                iou = self.compute_iou(new_obj.box_positions, lost_obj.box_positions)
                if iou < 0.3:
                    continue

                score = iou

                if (is_person and new_obj.face_embedding is not None and lost_obj.face_embedding is not None):            
                    face_compare = self.visual_recognition.embedding_compare(new_obj.face_embedding, lost_obj.face_embedding)
                    score = 0.4 * iou + 0.6 * face_compare

                if score > best_score:
                    best_score = score
                    best_match_id = lost_id

            if best_match_id is not None and best_score > 0.25:
                lost_obj = stored[best_match_id]

                del stored[best_match_id]
                stored[new_id] = new_obj
                new_obj.last_seen = 0

                del lost_tracks[best_match_id]
            else:
                stored[new_id] = new_obj
                if is_person:
                    person = self.new_person(new_obj, new_image, new_id)
                    if person is not None:
                        stored[new_id].identity = person["identity"]
                        stored[new_id].database_id = person["database_id"]
                else:
                    self.new_object(new_obj)

    def cleanup_old_tracks(self, stored: dict, max_last_seen: int = 3):
        for track_id in list(stored.keys()):
            if stored[track_id].last_seen > max_last_seen:
                del stored[track_id]

    def calcul_events_score(self, stored: dict, is_person: bool = False):
        total_score = 0.0
        num_events = 0
        for obj in stored.values():
            if obj.events is not None:
                current_score = 0.0
                num_events += 1
                for event in obj.events:
                    current_score += event.get("score", 0.0)
                    current_score = max(current_score, 0)
                    if not is_person:
                        current_score = current_score * 0.5
                total_score += current_score
        
        return total_score / num_events if num_events > 0 else 0.0
        
    def compare_persons_identities(self, previous_image):
        value = self.visual_recognition.database_recognition(previous_image)
        return value

    def compare_stored_persons_identities(self, previous_image, current_image):
        value = self.visual_recognition.compare(previous_image, current_image)
        return value
        
    def new_person(self, new_person, new_image, new_id, database_id = None, identity = None):
        x1, y1, x2, y2 = map(int, new_person.box_positions.tolist())
        person_crop = new_image[y1:y2, x1:x2]

        persons_list = self.visual_recognition.recognize(person_crop)
        if len(persons_list) == 0:
            return
        new_person_data = persons_list[0]
        name = "unknown"

        fx1, fy1, fx2, fy2 = new_person_data["bbox"]

        face_width = fx2 - fx1
        face_height = fy2 - fy1
        if face_width < 80 or face_height < 80:
            return

        if identity is None:
            Value = self.compare_persons_identities(person_crop)
            if Value["identity_id"] is not None:
                identity = Value["identity"]
                new_person.identity = Value["identity"]
                new_person.database_id = Value["identity_id"]

        if identity is None:
            number = 1
            while True:
                folder = self.person_folder / "persons" / f"{name}_{number:03d}"

                if not folder.exists():
                    folder.mkdir(parents=True)
                    break
                number += 1

            person = f"unknown_{number:03d}"
        else:
            person = identity

        print("6 : new_person")

        person_dir = self.person_folder / "persons" / person
        person_dir.mkdir(parents=True, exist_ok=True) 

        img_number = 1
        while True:
            filename = f"{person}_{img_number:02d}.jpg"
            visual_path = person_dir / filename
            if not visual_path.exists():
                break
            img_number += 1

        filelink = (f"persons/{person}/{filename}")
        img_rgb = cv2.cvtColor(person_crop, cv2.COLOR_BGR2RGB)

        manage_errors._error(
            variables={
                "img_rgb.shape": img_rgb.shape,
                "img_rgb.dtype": img_rgb.dtype,
                "visual_path": visual_path,
                "type(visual_path)": type(visual_path),
            }
        )

        Image.fromarray(img_rgb).save(visual_path)

        if database_id is None:
            person_db_id = self.visual_recognition.add_person(person)
        else: 
            person_db_id = database_id
        print("7 : new_person")
        self.visual_recognition.add_face_embedding(person_db_id, filelink, new_person_data["embedding"])
        #self.visual_recognition.show_database()

        print("8 : new_person")
        return {
            "identity": person,
            "database_id":person_db_id
        }

    def new_object(self, new_object):
        print("new_object")

    def event_managment(self, object, is_person: bool = False):
        events = object.events
        if events is None:
            events = []
        new_events = []

        movement_event = self.event_movement(
                        object.previous_box_sizes,
                        object.box_sizes,
                        is_person=is_person
                    )
        if movement_event is not None:
            new_events.append(movement_event)

        size_change_event = self.event_size_change(
                        object.previous_box_sizes,
                        object.box_sizes,
                        is_person=is_person
                    )
        
        if size_change_event is not None:
            new_events.append(size_change_event)

        if new_events is None or len(new_events) == 0:
            nothing_event = {
                "type": "nothing",
                "score":-0.5
            }
            events.append(nothing_event)
        for event in new_events:
            events.append(event)

        if len(events) > 10:
            events = events[-10:]

        return events

    def event_movement(self, previous_box, current_box, is_person: bool = False):
        events = {
            "type":"",
            "directions":"",
            "distance":0.0,
            "score":0.0
        }
        dx = float(current_box[0] - previous_box[0])
        dy = float(current_box[1] - previous_box[1])

        score = 0.0
        distance = (dx ** 2 + dy ** 2) ** 0.5

        old_width = float(previous_box[2])
        if old_width <= 0:
            return None
        movement_ratio = distance / old_width

        has_moved = False
        type_event = "person" if is_person else "object"
        if movement_ratio > 0.5:
            has_moved = True
            type_event += "_small_movement"
            score += 0.3
        elif movement_ratio > 1.0:
            has_moved = True
            type_event += "_large_movement"
            score += 0.8
        else:
            type_event = "nothing"

        direction = ""
        if has_moved:
            if dx > 0 and dy > 0:
                direction = "moved_down_right"
            elif dx < 0 and dy > 0:
                direction = "moved_down_left"
            elif dx > 0 and dy < 0:
                direction = "moved_up_right"
            elif dx < 0 and dy < 0:
                direction = "moved_up_left"
            else:
                if dx > 0:
                    direction = "moved_right"
                elif dx < 0:
                    direction = "moved_left"
                elif dy > 0:
                    direction = "moved_down"
                elif dy < 0:
                    direction = "moved_up"

            events["distance"] = distance
            events["direction"] = direction
            events["type"] = type_event
            events["score"] = score

            return events
        
    def event_size_change(self, previous_box, current_box, is_person: bool = False):
        events = {
            "type":"",
            "size_change":"",
            "size_value":0.0,
            "score":0.0
        }
        old_width = float(previous_box[2])
        new_width = float(current_box[2])

        old_height = float(previous_box[3])
        new_height = float(current_box[3])

        if old_width <= 0:
            return None
        if old_height <= 0:
            return None

        width_change = (new_width - old_width) / old_width
        height_change = (new_height - old_height) / old_height

        size_change = (width_change + height_change) / 2.0
        has_changed = False

        type_event = "person" if is_person else "object"
        size_type = "size"
        score = 0.0

        if size_change > 0.1:
            has_changed = True
            size_type += "_small_increase"
            type_event += "_increase"
            score += 0.3
        elif size_change < -0.1:
            has_changed = True
            type_event += "_decrease"
            size_type += "_small_decrease"
            score += 0.3
        elif size_change > 0.25:
            has_changed = True
            size_type += "_large_increase"
            type_event += "_increase"
            score += 0.8
        elif size_change < -0.25:
            has_changed = True
            size_type += "_large_decrease"
            type_event += "_decrease"
            score += 0.8
        else:
            type_event = "nothing"

        if has_changed:
            events["size_change"] = size_type
            events["size_value"] = size_change
            events["type"] = type_event
            events["score"] = score

            return events

    def calcul_fps(self):
        self.fps_counter_frames += 1
        elapsed = time.perf_counter() - self.fps_counter_start

        if elapsed >= 1.0:
            self.yolo_fps = (
                self.fps_counter_frames / elapsed
            )

            self.fps_counter_frames = 0
            self.fps_counter_start = time.perf_counter()

        return f"{self.yolo_fps:.1f}"

    def timer_time(self):
        return self.last_process_data_time - time.monotonic()

    def compute_iou(self, box1, box2) -> float:
        if hasattr(box1, 'cpu'):
            box1 = box1.cpu().numpy()
        if hasattr(box2, 'cpu'):
            box2 = box2.cpu().numpy()

        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])

        inter_width = max(0, x2 - x1)
        inter_height = max(0, y2 - y1)
        inter_area = inter_width * inter_height

        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])

        union_area = area1 + area2 - inter_area
        if union_area == 0:
            return 0.0

        return float(inter_area / union_area) if union_area > 0 else 0.0
