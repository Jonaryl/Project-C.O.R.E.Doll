import time

import cv2
import mediapipe as mp
from mediapipe import Image as MpImage
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.vision import drawing_styles, drawing_utils

from engines.perception.visual_module.visual_classes import (
    VisionObject,
    VisionPerson,
)
from engines.perception.visual_module.visual_frame_analysis import VisualFrameAnalisys
from tools.file_r import FileRead
from tools.keyVar import KeyVar
from tools.manage_errors import ManageError

key_var = KeyVar()
file_read = FileRead()
manage_errors = ManageError()
visual_frame_analysis = VisualFrameAnalisys()



class FocusVisionModule:
    def __init__(self, persons: dict[int, VisionPerson], objects: dict[int, VisionObject]):
        self.persons = persons
        self.objects = objects

        self.vision_path = key_var.get_vision_database()
        self.person_folder = self.vision_path.parent
        self.person_folder.mkdir(parents=True, exist_ok=True)

        self.video_config = file_read.read_json_file(key_var.get_video_config())
        self.last_mediapipe_time = 0
        self.mediapipe_current_interval = 0
        self.mediapipe_interval_low = self.video_config["mediapipe"]["mediapipe_interval_low"]
        self.mediapipe_interval_high = self.video_config["mediapipe"]["mediapipe_interval_high"]

        self.process_image_time = self.video_config["mediapipe"]["process_image_time"]
        self.process_video_time = self.video_config["mediapipe"]["process_video_time"]
        self.last_process_data_time = None
        self.is_video_process = False
        self.is_video_count = 0

        self.last_image_process = None
        self.last_video_process = []

        self.init_base_models()
        self.init_face_models()
        self.init_object_models()

        self.process_face_time = self.video_config["mediapipe"]["process_face_time"]
        self.face_mesh_active = False
        self.face_mesh_frames_left = 0
        self.face_mesh_results = [] 

        self.timestamp_ms = 0
        self.last_annotated_frame = None
        self.object_timestamp_ms = 0

        self.start_analisys_process()

    def init_base_models(self):
        model_path = self.video_config["mediapipe"]["mediapipe_model"]


        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_poses=2,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.pose = vision.PoseLandmarker.create_from_options(options)

    def init_face_models(self):
        face_model = self.video_config["mediapipe"]["face_model"]
        face_base_options = python.BaseOptions(model_asset_path=face_model)
        face_options = vision.FaceLandmarkerOptions(
            base_options=face_base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_faces=1,
            min_face_detection_confidence=0.6,
            min_face_presence_confidence=0.6,
            min_tracking_confidence=0.6,
            output_face_blendshapes=True,
            output_facial_transformation_matrixes=True
        )
        self.face_landmarker = vision.FaceLandmarker.create_from_options(face_options)
    def start_face_model(self):
        self.face_mesh_active = True
        self.face_mesh_frames_left = self.process_face_time
        self.face_mesh_results = []

    def run_face_mesh(self, frame, debug_visual = False):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = MpImage(image_format=mp.ImageFormat.SRGB, data=rgb)
        
        self.timestamp_ms += 33
        result = self.face_landmarker.detect_for_video(mp_image, self.timestamp_ms)

        annotated_frame = frame.copy()

        if result.face_landmarks:
            analysis = visual_frame_analysis.analyze_face_mesh(result)
            self.face_mesh_results.append(analysis)
            print("analysis = ", analysis)

            if debug_visual:
                for face_landmarks in result.face_landmarks:
                    drawing_utils.draw_landmarks(
                        image=annotated_frame,
                        landmark_list=face_landmarks,
                        connections=vision.FaceLandmarksConnections.FACE_LANDMARKS_TESSELATION,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=drawing_styles.get_default_face_mesh_tesselation_style()
                    )
                    drawing_utils.draw_landmarks(
                        image=annotated_frame,
                        landmark_list=face_landmarks,
                        connections=vision.FaceLandmarksConnections.FACE_LANDMARKS_CONTOURS,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=drawing_styles.get_default_face_mesh_contours_style()
                    )
                    drawing_utils.draw_landmarks(
                        image=annotated_frame,
                        landmark_list=face_landmarks,
                        connections=vision.FaceLandmarksConnections.FACE_LANDMARKS_LEFT_IRIS,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=drawing_styles.get_default_face_mesh_iris_connections_style()
                    )
                    drawing_utils.draw_landmarks(
                    image=annotated_frame,
                    landmark_list=face_landmarks,
                    connections=vision.FaceLandmarksConnections.FACE_LANDMARKS_RIGHT_IRIS,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=drawing_styles.get_default_face_mesh_iris_connections_style()
                    )

        return analysis, annotated_frame

    def init_object_models(self):
        object_model = self.video_config["mediapipe"]["object_model"]
        object_base_options = python.BaseOptions(
            model_asset_path="models/efficientdet_lite0.tflite"  # adapte le chemin
        )

        object_options = vision.ObjectDetectorOptions(
            base_options=object_base_options,
            running_mode=vision.RunningMode.VIDEO,   # important pour la vidéo
            max_results=8,
            score_threshold=0.35,                    # ajuste selon tes besoins
            # category_allowlist=["person", "cell phone", "cup", "book"]  # optionnel
        )

        self.object_detector = vision.ObjectDetector.create_from_options(object_options)
    def run_object_model(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = MpImage(image_format=mp.ImageFormat.SRGB, data=rgb)

        self.object_timestamp_ms += 33
        result = self.object_detector.detect_for_video(mp_image, self.object_timestamp_ms)

        detections = []
        annotated_frame = frame.copy()

        for detection in result.detections:
            bbox = detection.bounding_box
            category = detection.categories[0]

            x1 = bbox.origin_x
            y1 = bbox.origin_y
            x2 = x1 + bbox.width
            y2 = y1 + bbox.height

            det = {
                "label": category.category_name,
                "score": round(category.score, 3),
                "bbox": [x1, y1, x2, y2],
                "bbox_norm": [
                    x1 / frame.shape[1],
                    y1 / frame.shape[0],
                    x2 / frame.shape[1],
                    y2 / frame.shape[0]
                ]
            }
            detections.append(det)

            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"{det['label']} {det['score']:.2f}"
            cv2.putText(annotated_frame, label, (x1, y1 - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
        return detections, annotated_frame
    
    def timer_time(self):
        return self.last_process_data_time - time.monotonic()

    def start_analisys_process(self):
        print("start_analisys_process")
        self.is_video_process = True
        self.last_process_data_time = 2
        self.is_video_count = 0
        self.last_video_process.clear()

    def process_frame(self, frame, framerate, identity, process_message):
        manage_errors._error(
                    variables={
                        "frame": frame,
                        "framerate": framerate,
                        "self.pose": self.pose,
                    }
                )
        if framerate == "fast":
            self.mediapipe_current_interval = self.mediapipe_interval_high
        else:
            self.mediapipe_current_interval = self.mediapipe_interval_low

            now = time.perf_counter()            
            if now - self.last_mediapipe_time < self.mediapipe_current_interval:
                if self.last_annotated_frame is not None:
                    cv2.imshow("MediaPipe", self.last_annotated_frame)                
                return                
            self.last_mediapipe_time = now
            self.last_annotated_frame = frame

            cv2.imshow("MediaPipe", frame)
            return

        now = time.perf_counter()            
        if now - self.last_mediapipe_time < self.mediapipe_current_interval:
            if self.last_annotated_frame is not None:
                cv2.imshow("MediaPipe", self.last_annotated_frame)                
            return                
        self.last_mediapipe_time = now
        
        rgb = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        self.timestamp_ms += 33
        results = self.pose.detect_for_video(mp_image, self.timestamp_ms)
        annotated_frame = visual_frame_analysis.annotate(frame.copy(), results)

        objects, annotated = self.run_object_model(frame)
        annotated_frame = annotated

        face_analysis = None
        if self.face_mesh_active and self.face_mesh_frames_left > 0:
            face_analysis, annotated_frame = self.run_face_mesh(frame, True)
            self.face_mesh_frames_left -= 1

        cv2.imshow("MediaPipe", annotated_frame)
        self.last_annotated_frame = annotated_frame
        #print(results)
        #process_message(results)
        data = {
            "identity": identity,
            "results":results,
            "face_analysis":face_analysis,
            "objects":objects
        }

        self.process_data(data, process_message)

        if self.face_mesh_frames_left == 0 and self.face_mesh_active:
            self.face_mesh_active = False
            process_message({
                "message":None,
                "action": "Stop"
            })

    def process_data(self, data, process_message):
        identity = data["identity"]
        results = data["results"]
        face_analysis = data["face_analysis"]
        objects = data["objects"]

        if self.last_process_data_time is None:
            if self.is_video_process:
                self.last_process_data_time = time.monotonic() + self.process_video_time
            else:
                self.last_process_data_time = time.monotonic() + self.process_image_time
        if self.timer_time() < 0:
            print("PROCESS DATA MEDIAPIPE")
            persons = visual_frame_analysis.create_persons_from_results(results)
            if self.is_video_process and self.is_video_count < 6:
                print("PROCESS VIDEO")
                self.last_process_data_time = time.monotonic() + self.process_video_time
                self.is_video_count += 1
                image_process = visual_frame_analysis.person_analysis(persons[0])
                image_process["face_analysis"] = face_analysis
                image_process["objects_visible"] = objects
                self.last_video_process.append(image_process)

                if image_process["urgent_reaction_type"]:
                    print("PROCESS VIDEO URGENT PROCESS")
                    self.is_video_process = False
                    self.last_process_data_time = time.monotonic() + self.process_image_time
                    return

                if self.is_video_count == 5:
                    print("PROCESS VIDEO COMPLETE")
                    self.is_video_process = False
                    available_methods = {
                        "face_mesh": self.start_face_model
                    }

                    video_process = visual_frame_analysis.video_analisys(self.last_video_process, available_methods)
                    video_process["person"] = identity

                    print("video_process == ", video_process)
                    process_data = video_process["data"]
                    methods = video_process["methods"]

                    for method in methods:
                        method()

                    self.is_video_count = 0
                    self.last_video_process.clear()
                    self.last_process_data_time = time.monotonic() + self.process_image_time

                    if len(methods) == 0:
                        process_message({
                                "message":None,
                                "action": "Stop"
                            })

            else:
                print("PROCESS IMAGE")
                self.is_video_process = False
                self.last_process_data_time = time.monotonic() + self.process_image_time
                self.last_image_process = visual_frame_analysis.person_analysis(persons[0])
                process_message({
                        "message":None,
                        "action": "Stop"
                    })
            print("FINAL END")

    

    def close(self):
        self.pose.close()

