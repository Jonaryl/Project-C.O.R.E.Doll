from collections import defaultdict
from collections.abc import Callable

import cv2
import numpy

from engines.perception.visual_module.visual_classes import (
    PartPosition,
    Person,
    PersonArm,
    PersonEyes,
    PersonFace,
    PersonHand,
    PersonLeg,
    PersonMouth,
    PerspectiveInfo,
    ValueInfos,
)


class VisualFrameAnalisys:
    def __init__(self):
        self.pose_connections = [
            # visage
            (0, 1),
            (1, 2),
            (2, 3),
            (3, 7),
            (0, 4),
            (4, 5),
            (5, 6),
            (6, 8),
            (9, 10),

            # épaules / bras gauche
            (11, 12),
            (11, 13),
            (13, 15),
            (15, 17),
            (15, 19),
            (15, 21),
            (17, 19),

            # bras droit
            (12, 14),
            (14, 16),
            (16, 18),
            (16, 20),
            (18, 20),

            # torse / hanches
            (11, 23),
            (12, 24),
            (23, 24),

            # jambe gauche
            (23, 25),
            (25, 27),
            (27, 29),
            (29, 31),
            (27, 31),

            # jambe droite
            (24, 26),
            (26, 28),
            (28, 30),
            (30, 32),
            (28, 32),
        ]

        self.expression_rules = {
            "happy": {
                "mouthSmileLeft": (0.55, 1.0),
                "mouthSmileRight": (0.55, 1.0),
                "cheekSquintLeft": (0.20, 1.0),
                "cheekSquintRight": (0.20, 1.0),
                "eyeSquintLeft": (0.15, 1.0),
                "eyeSquintRight": (0.15, 1.0),
                "browDownLeft": (0.0, 0.35),
                "browDownRight": (0.0, 0.35),
                "mouthFrownLeft": (0.0, 0.2),
                "mouthFrownRight": (0.0, 0.2),
            },

            "sad": {
                "mouthFrownLeft": (0.35, 1.0),
                "mouthFrownRight": (0.35, 1.0),
                "browInnerUp": (0.30, 1.0),
                "mouthSmileLeft": (0.0, 0.25),
                "mouthSmileRight": (0.0, 0.25),
            },

            "angry": {
                "browDownLeft": (0.45, 1.0),
                "browDownRight": (0.45, 1.0),
                "eyeSquintLeft": (0.25, 1.0),
                "eyeSquintRight": (0.25, 1.0),
                "mouthPressLeft": (0.15, 1.0),
                "mouthPressRight": (0.15, 1.0),
                "mouthSmileLeft": (0.0, 0.25),
                "mouthSmileRight": (0.0, 0.25),
            },

            "surprise": {
                "browInnerUp": (0.40, 1.0),
                "browOuterUpLeft": (0.30, 1.0),
                "browOuterUpRight": (0.30, 1.0),
                "eyeWideLeft": (0.30, 1.0),
                "eyeWideRight": (0.30, 1.0),
                "jawOpen": (0.25, 1.0),
            },

            "disgust": {
                "noseSneerLeft": (0.35, 1.0),
                "noseSneerRight": (0.35, 1.0),
                "mouthUpperUpLeft": (0.25, 1.0),
                "mouthUpperUpRight": (0.25, 1.0),
            },


            "serious": {
                "browDownLeft": (0.25, 0.70),
                "browDownRight": (0.25, 0.70),
                "mouthSmileLeft": (0.0, 0.25),
                "mouthSmileRight": (0.0, 0.25),
                "mouthFrownLeft": (0.0, 0.30),
                "mouthFrownRight": (0.0, 0.30),
                "jawOpen": (0.0, 0.25),
                "eyeWideLeft": (0.0, 0.30),
                "eyeWideRight": (0.0, 0.30),
                "eyeSquintLeft": (0.10, 0.60),
                "eyeSquintRight": (0.10, 0.60),
            },

            "thinking": { 
                "browInnerUp": (0.20, 0.70),
                "browDownLeft": (0.15, 0.55),
                "browDownRight": (0.15, 0.55),
                "eyeSquintLeft": (0.15, 0.60),
                "eyeSquintRight": (0.15, 0.60),
                "mouthSmileLeft": (0.0, 0.30),
                "mouthSmileRight": (0.0, 0.30),
                "mouthFrownLeft": (0.0, 0.35),
                "jawOpen": (0.0, 0.30),
            },

            "confused": {
                "browInnerUp": (0.30, 1.0),
                "browDownLeft": (0.15, 0.55),
                "browDownRight": (0.15, 0.55),
                "eyeSquintLeft": (0.10, 0.55),
                "eyeSquintRight": (0.10, 0.55),
                "mouthFrownLeft": (0.10, 0.50),
                "mouthFrownRight": (0.10, 0.50),
                "mouthSmileLeft": (0.0, 0.30),
                "mouthSmileRight": (0.0, 0.30),
                "jawOpen": (0.0, 0.35),
            },

            "neutral": {
                "mouthSmileLeft": (0.0, 0.28),
                "mouthSmileRight": (0.0, 0.28),
                "mouthFrownLeft": (0.0, 0.28),
                "mouthFrownRight": (0.0, 0.28),
                "browDownLeft": (0.0, 0.32),
                "browDownRight": (0.0, 0.32),
                "browInnerUp": (0.0, 0.32),
                "jawOpen": (0.0, 0.28),
                "eyeWideLeft": (0.0, 0.30),
                "eyeWideRight": (0.0, 0.30),
            }
        }

        self.math = CalculTools()

    def create_persons_from_results(self, results) -> list[Person]:
        persons = []
        if not results.pose_landmarks:
            return persons

        for i, landmarks in enumerate(results.pose_landmarks):
            world_landmarks = None
            if results.pose_world_landmarks and i < len(results.pose_world_landmarks):
                world_landmarks = results.pose_world_landmarks[i]

            def make_part(index: int, name: str) -> PartPosition:
                lm = landmarks[index]
                part = PartPosition(
                    name=name,
                    index=index,
                    x=lm.x,
                    y=lm.y,
                    z=lm.z,
                    visibility=lm.visibility
                )
                if world_landmarks:
                    wlm = world_landmarks[index]
                    part.world_x = wlm.x
                    part.world_y = wlm.y
                    part.world_z = wlm.z
                return part

            face = PersonFace(
                nose=make_part(0, "nose"),
                eye_l=PersonEyes(
                    inner=make_part(1, "left_eye_inner"),
                    middle=make_part(2, "left_eye"),
                    outer=make_part(3, "left_eye_outer")
                ),
                eye_r=PersonEyes(
                    inner=make_part(4, "right_eye_inner"),
                    middle=make_part(5, "right_eye"),
                    outer=make_part(6, "right_eye_outer")
                ),
                ear_l=make_part(7, "left_ear"),
                ear_r=make_part(8, "right_ear"),
                mouth=PersonMouth(
                    left=make_part(9, "mouth_left"),
                    right=make_part(10, "mouth_right")
                )
            )

            arm_l = PersonArm(
                shoulder=make_part(11, "left_shoulder"),
                elbow=make_part(13, "left_elbow"),
                wrist=make_part(15, "left_wrist")
            )
            arm_r = PersonArm(
                shoulder=make_part(12, "right_shoulder"),
                elbow=make_part(14, "right_elbow"),
                wrist=make_part(16, "right_wrist")
            )

            hand_l = PersonHand(
                pinky=make_part(17, "left_pinky"),
                index=make_part(19, "left_index"),
                thumb=make_part(21, "left_thumb")
            )
            hand_r = PersonHand(
                pinky=make_part(18, "right_pinky"),
                index=make_part(20, "right_index"),
                thumb=make_part(22, "right_thumb")
            )

            leg_l = PersonLeg(
                hip=make_part(23, "left_hip"),
                knee=make_part(25, "left_knee"),
                ankle=make_part(27, "left_ankle"),
                heel=make_part(29, "left_heel"),
                foot=make_part(31, "left_foot_index")
            )
            leg_r = PersonLeg(
                hip=make_part(24, "right_hip"),
                knee=make_part(26, "right_knee"),
                ankle=make_part(28, "right_ankle"),
                heel=make_part(30, "right_heel"),
                foot=make_part(32, "right_foot_index")
            )

            person = Person(
                face=face,
                arm_l=arm_l,
                arm_r=arm_r,
                hand_l=hand_l,
                hand_r=hand_r,
                leg_l=leg_l,
                leg_r=leg_r
            )
            persons.append(person)

        return persons

    def person_analysis(self, person: Person):
        perspective_info = self.analyze_perspective(person)
        body_position = self.body_position(person)
        #print("perspective_info == ", perspective_info)

        is_urgent_reaction_needed = False
        urgent_reaction_type = ""

        raw_analysis = {
            "perspective_info":perspective_info,
            "face_analysis":None,
            "body_position":body_position,
            
            "objects_visible": None,
            "is_urgent_reaction_needed":is_urgent_reaction_needed,
            "urgent_reaction_type":urgent_reaction_type
        }

        if is_urgent_reaction_needed:
            return raw_analysis

        return raw_analysis

    def analyze_perspective(self, person: Person) -> PerspectiveInfo:
        info = PerspectiveInfo(
            facing=ValueInfos(),
            camera_angle=ValueInfos(),
        )

        nose = person.face.nose
        left_ear = person.face.ear_l
        right_ear = person.face.ear_r

        inner_eye_l = person.face.eye_l.inner
        middle_eye_l = person.face.eye_l.middle
        outer_eye_l = person.face.eye_l.outer

        inner_eye_r = person.face.eye_r.inner
        middle_eye_r = person.face.eye_r.middle
        outer_eye_r = person.face.eye_r.outer

        face_points = [nose, left_ear, right_ear, 
                       inner_eye_l, middle_eye_l, outer_eye_l, 
                       inner_eye_r, middle_eye_r, outer_eye_r]
        
        face_visible = all(p is not None and p.visibility > 0.5 for p in face_points)

        if not face_visible:
            info.overall_confidence = 0.2
            return info


        # Face direction front left back right
        face_left_average = self.math.average_position([left_ear, inner_eye_l, outer_eye_l, middle_eye_l])
        face_right_average = self.math.average_position([right_ear, inner_eye_r, outer_eye_r, middle_eye_r])

        face_width = self.math.distance_2d(face_left_average, face_right_average)
        nose_to_l = self.math.distance_2d(face_left_average, nose)
        nose_to_r = self.math.distance_2d(face_right_average, nose)

        diff_ratio = abs(nose_to_l - nose_to_r) / (face_width + 1e-6)
        total_span = face_right_average.x - face_left_average.x
        if abs(total_span) < 1e-6:
            nose_ratio = 0.5
        else:
            nose_ratio = (nose.x - face_left_average.x) / total_span

        proximity = numpy.clip((face_width - 0.01) / 0.14, 0.0, 1.0)
        if face_left_average.x < nose.x < face_right_average.x or face_right_average.x < nose.x < face_left_average.x:
            if diff_ratio < 0.18:
                info.facing.text = "front"
                base_confidence = 0.85
            else:
                if nose_to_l < nose_to_r:
                    info.facing.text = "right"
                else:
                    info.facing.text = "left"
                base_confidence = 0.75

            distance_penalty = 0.35 * (1 - proximity)
            final_confidence = base_confidence - distance_penalty
            final_confidence = float(numpy.clip(final_confidence, 0.25, 0.95))
            info.facing.confidence = final_confidence            
        elif nose.x < min(face_left_average.x, face_right_average.x):
            info.facing.text = "left"
            info.facing.confidence = 0.8
        elif nose.x > max(face_left_average.x, face_right_average.x):
            info.facing.text = "right"
            info.facing.confidence = 0.8
        else:
            info.facing.text = "unknown"
            info.facing.confidence = 0.3

        # Face Pov bottom, top
        eyes_line = self.math.average_position([inner_eye_l, outer_eye_l, middle_eye_l, inner_eye_r, outer_eye_r, middle_eye_r])
        ears_line = self.math.average_position([left_ear, right_ear])

        distance_nose_eyes = self.math.distance_2d(eyes_line, nose)
        distance_nose_ears = self.math.distance_2d(ears_line, nose)
        distance_eyes_ears = self.math.distance_2d(ears_line, eyes_line)

        ratio_eye_ears = distance_nose_ears / (distance_eyes_ears + 1e-6)

        if ratio_eye_ears > 1.65:
            info.camera_angle.text = "high"
            info.camera_angle.confidence = 0.8
        elif ratio_eye_ears < 0.50:
            info.camera_angle.text = "low"
            info.camera_angle.confidence = 0.8
        else:
            info.camera_angle.text = "eye_level"
            info.camera_angle.confidence = 0.75

        confidences = [
            info.facing.confidence,
            info.camera_angle.confidence,
        ]
        info.overall_confidence = float(numpy.mean([c for c in confidences if c > 0]))
        return info
    
    def body_position(self, person: Person) -> list:
        nose = person.face.nose
        left_ear = person.face.ear_l
        right_ear = person.face.ear_r

        inner_eye_l = person.face.eye_l.inner
        middle_eye_l = person.face.eye_l.middle
        outer_eye_l = person.face.eye_l.outer

        inner_eye_r = person.face.eye_r.inner
        middle_eye_r = person.face.eye_r.middle
        outer_eye_r = person.face.eye_r.outer

        face_average_position = self.math.average_position([nose, left_ear, inner_eye_l, outer_eye_l, middle_eye_l, 
                                                   right_ear, inner_eye_r, outer_eye_r, middle_eye_r])
        shoulder_l_position = person.arm_l.shoulder
        shoulder_r_position = person.arm_r.shoulder

        hand_left_average = self.math.average_position([person.hand_l.index, person.hand_l.thumb, person.hand_l.pinky])
        hand_right_average = self.math.average_position([person.hand_r.index, person.hand_r.thumb, person.hand_r.pinky])

        body_part_object = [
            {"name": "face", "object": face_average_position},
            {"name": "shoulder_l", "object": shoulder_l_position},
            {"name": "shoulder_r", "object": shoulder_r_position},
            {"name": "hand_l", "object": hand_left_average},
            {"name": "hand_r", "object": hand_right_average},
        ]

        body_part_visible = []
        for part in body_part_object:
            p = part["object"]
            if p is not None and getattr(p, "visibility", 0) > 0.5:
                body_part_visible.append(part)
        return body_part_visible      

    def video_analisys(self, raw_analysis: list, available_methods: dict[str, Callable]):
        sequence = []
        #print("raw_analisys = ", raw_analysis)
        #print("available_methods = ", available_methods)

        objects = []
        for person in raw_analysis:
            facing = person["perspective_info"].facing
            objects.append(person["objects_visible"])
            if facing and facing.confidence > 0.55:
                sequence.append(facing.text)
            else:
                sequence.append("unknown")

        #print("Séquence brute :", sequence)
        face_scenario = self.interpret_facing_sequence(sequence)
        #print("Scénario détecté :", face_scenario)
        objects_interactions = self.detect_interactions(raw_analysis)
        #print("objects_interactions :", objects_interactions)

        methods_to_call = []
        if face_scenario["scenario"] == "looking_forward":
            methods_to_call.append(available_methods["face_mesh"])

        data = {
            "person":None,
            "face_scenario":face_scenario,
            "objects_interactions":objects_interactions
        }

        return{
            "data":data,
            "methods":methods_to_call
        }

    def analyze_face_mesh(self, result) -> dict:
        landmarks = result.face_landmarks[0]
        blendshapes = result.face_blendshapes[0] if result.face_blendshapes else None

        bs = {b.category_name: b.score for b in blendshapes}
        expressions = self.analyze_expressions(bs)
        top_expressions = expressions[:3]

        basic_analisys = self.analyze_elements(bs, top_expressions)

        other_data = self.other_data_search(bs, top_expressions)

        analysis = {
            "gaze_direction": basic_analisys["gaze_direction"],
            "eyes_open": basic_analisys["eyes_open"],
            "mouth_open": basic_analisys["mouth_open"],
            "expression": top_expressions,
            "other": other_data,
            "attention_score": basic_analisys["attention_score"]
        }
        return analysis
    
    def detect_interactions(self, raw_analysis: list) -> list[dict]:
        body_positions = defaultdict(list)
        object_positions = defaultdict(list)
        shoulder_widths = []

        for frame in raw_analysis:
            body_parts = frame.get("body_position") or []
            current_body = {}

            for part in body_parts:
                pos = part.get("object")
                if pos is not None and getattr(pos, "visibility", 0) > 0.5:
                    current_body[part["name"]] = (float(pos.x), float(pos.y))
                    body_positions[part["name"]].append((float(pos.x), float(pos.y)))

            if "shoulder_l" in current_body and "shoulder_r" in current_body:
                sl = current_body["shoulder_l"]
                sr = current_body["shoulder_r"]
                width = numpy.sqrt((sl[0] - sr[0])**2 + (sl[1] - sr[1])**2)
                shoulder_widths.append(width)

            objects = frame.get("objects_visible") or []
            for obj in objects:
                label = obj["label"]
                if label == "person":
                    continue
                if "bbox_norm" in obj:
                    x1, y1, x2, y2 = obj["bbox_norm"]
                    cx = (x1 + x2) / 2
                    cy = (y1 + y2) / 2
                    object_positions[label].append((cx, cy))

        avg_shoulder_width = numpy.mean(shoulder_widths) if shoulder_widths else 0.25
        threshold = numpy.clip(0.28 * (avg_shoulder_width / 0.25), 0.13, 0.48)

        print(f"avg_shoulder_width = {avg_shoulder_width:.3f} | threshold = {threshold:.3f}")

        body_avg = {name: (numpy.mean([p[0] for p in pts]), numpy.mean([p[1] for p in pts]))
                    for name, pts in body_positions.items() if len(pts) >= 2}

        object_avg = {label: (numpy.mean([p[0] for p in pts]), numpy.mean([p[1] for p in pts]))
                    for label, pts in object_positions.items() if len(pts) >= 2}

        BODY_PRIORITY = {
            "hand_l": 1.0,
            "hand_r": 1.0,
            "face": 0.75,
            "shoulder_l": 0.45,
            "shoulder_r": 0.45,
        }

        conclusions = []

        for obj_label, obj_pos in object_avg.items():
            for body_name, body_pos in body_avg.items():
                dist = numpy.sqrt((obj_pos[0] - body_pos[0])**2 + (obj_pos[1] - body_pos[1])**2)

                if dist > threshold:
                    continue

                distance_score = 1.0 - (dist / threshold)

                priority = BODY_PRIORITY.get(body_name, 0.5)
                final_confidence = distance_score * priority

                conclusion = self._get_conclusion_type(body_name, obj_label)

                conclusions.append({
                    "object": obj_label,
                    "body_part": body_name,
                    "distance_avg": round(float(dist), 3),
                    "conclusion": conclusion,
                    "confidence": round(float(final_confidence), 2)
                })

        best_by_object = {}
        for item in conclusions:
            obj = item["object"]
            if obj not in best_by_object or item["confidence"] > best_by_object[obj]["confidence"]:
                best_by_object[obj] = item

        final = list(best_by_object.values())
        final.sort(key=lambda x: x["confidence"], reverse=True)

        return final


    def _get_conclusion_type(self, body_part: str, obj_label: str) -> str:
        obj = obj_label.lower()

        if body_part in ["hand_l", "hand_r"]:
            if "phone" in obj:
                return "holding_phone"
            if obj in ["cup", "bottle", "wine glass"]:
                return "holding_drink"
            return "holding_object"

        if body_part == "face":
            if "phone" in obj:
                return "phone_near_face"
            if obj in ["cup", "bottle", "wine glass"]:
                return "drinking"
            return "object_near_face"

        return "near"

    def analyze_expressions(self, bs: dict[str, float]) -> list[dict]:
        results = []
        for expression, rules in self.expression_rules.items():
            score = self.score_expression(bs, rules)
            results.append({
                "expression": expression,
                "score": round(score, 3),
                "confidence": round(score, 3)
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        results = [r for r in results if r["score"] >= 0.35]
        return results
    def score_expression(self, bs: dict[str, float], rules: dict[str, tuple[float, float]]) -> float:
        if not rules:
            return 0.0

        matched = 0
        total = len(rules)

        for name, (min_val, max_val) in rules.items():
            value = bs.get(name, 0.0)
            if min_val <= value <= max_val:
                matched += 1
            #else:
                # distance = min(abs(value - min_val), abs(value - max_val))
                # if distance < 0.15:
                #     matched += 0.5

        return matched / total

    def analyze_elements(self,  bs: dict[str, float,], top_expressions):
        blink_avg = (bs.get("eyeBlinkLeft", 0) + bs.get("eyeBlinkRight", 0)) / 2
        eyes_open_score = 1.0 - blink_avg
        
        if blink_avg > 0.55:
            eyes_open = "closed"
        elif blink_avg > 0.35:
            eyes_open = "half-closed"
        else:
            eyes_open = "open"

        # ========== 3. Mouth ==========
        jaw_open = bs.get("jawOpen", 0.0)

        if jaw_open > 0.45:
            mouth_open = "wide_open"
        elif jaw_open > 0.22:
            mouth_open = "open"
        elif jaw_open > 0.08:
            mouth_open = "slightly_open"
        else:
            mouth_open = "closed"

        # ========== 4. Direction ==========
        look_in = (bs.get("eyeLookInLeft", 0) + bs.get("eyeLookInRight", 0)) / 2
        look_out = (bs.get("eyeLookOutLeft", 0) + bs.get("eyeLookOutRight", 0)) / 2
        look_up = (bs.get("eyeLookUpLeft", 0) + bs.get("eyeLookUpRight", 0)) / 2
        look_down = (bs.get("eyeLookDownLeft", 0) + bs.get("eyeLookDownRight", 0)) / 2

        if look_out > 0.35 and look_out > look_in:
            horizontal = "right" if bs.get("eyeLookOutLeft", 0) > bs.get("eyeLookOutRight", 0) else "left"
            # Note: selon le point de vue caméra, left/right peut être inversé → à tester
        elif look_in > 0.35:
            horizontal = "center"
        else:
            horizontal = "center"

        horizontal_score = bs.get("eyeLookOutLeft", 0) - bs.get("eyeLookOutRight", 0)
        
        if horizontal_score > 0.25:
            horizontal = "left"
        elif horizontal_score < -0.25:
            horizontal = "right"
        else:
            horizontal = "center"

        # Vertical
        if look_up > 0.30:
            vertical = "up"
        elif look_down > 0.30:
            vertical = "down"
        else:
            vertical = "center"

        if horizontal == "center" and vertical == "center":
            gaze_direction = "front"
        else:
            gaze_direction = f"{vertical}_{horizontal}".replace("center_", "").replace("_center", "")
            if gaze_direction == "":
                gaze_direction = "front"

        # ========== Attention Score ==========
        attention = 0.0

        # Regarde en face
        if gaze_direction == "front":
            attention += 0.40
        elif "center" in gaze_direction:
            attention += 0.25

        attention += eyes_open_score * 0.30
        if top_expressions and top_expressions[0]["expression"] in ["happy", "neutral", "serious", "thinking"]:
            attention += 0.20

        attention = min(round(attention, 2), 1.0)
        return {
            "gaze_direction": gaze_direction,
            "eyes_open": eyes_open,
            "mouth_open": mouth_open,
            "attention_score": attention,
        }

    def other_data_search(self,  bs: dict[str, float,], top_expressions):
        others = []
        blink_avg = (bs.get("eyeBlinkLeft", 0) + bs.get("eyeBlinkRight", 0)) / 2
        eyes_open_score = 1.0 - blink_avg

        # Fatigue
        if blink_avg > 0.35 and eyes_open_score < 0.55:
            others.append("seems_tired")

        # Tension
        tension = (bs.get("browDownLeft", 0) + bs.get("browDownRight", 0) + 
                bs.get("mouthPressLeft", 0) + bs.get("mouthPressRight", 0)) / 4
        if tension > 0.40:
            others.append("seems_tensed")

        # Forte asymétrie (sourire)
        smile_asym = abs(bs.get("mouthSmileLeft", 0) - bs.get("mouthSmileRight", 0))
        if smile_asym > 0.35:
            others.append("asymmetric_smile")

        return others
    
    def conclude_face_mesh(self, results: list[dict]) -> dict:
        if not results:
            return {"status": "no_data"}

        gazes = [r["gaze_direction"] for r in results]
        expressions = [r["expression"] for r in results]

        most_common_gaze = max(set(gazes), key=gazes.count)
        most_common_expr = max(set(expressions), key=expressions.count)

        return {
            "looking_at_ai": most_common_gaze == "center",
            "gaze": most_common_gaze,
            "expression": most_common_expr,
            "attention_level": "high" if most_common_gaze == "center" else "medium",
            "frames_analyzed": len(results)
        }

    def interpret_facing_sequence(self, sequence: list[str]) -> dict:
        if not sequence:
            return {"scenario": "unknown", "confidence": 0.0}

        clean_seq = [s for s in sequence if s in ("front", "left", "right", "back")]
        if len(clean_seq) < 3:
            return {"scenario": "insufficient_data", "confidence": 0.3}

        n = len(clean_seq)
        first_half = clean_seq[:n//2]
        second_half = clean_seq[n//2:]

        # Compteurs
        count = {
            "front": clean_seq.count("front"),
            "left": clean_seq.count("left"),
            "right": clean_seq.count("right"),
            "back": clean_seq.count("back")
        }

        dominant = max(count, key=count.get)
        dominant_ratio = count[dominant] / n

        if dominant == "front" and dominant_ratio > 0.7:
            return {
                "scenario": "looking_forward",
                "confidence": 0.85,
            }

        if clean_seq[0] == "left" and clean_seq[-1] == "right":
            return {
                "scenario": "looking_left_to_right",
                "confidence": 0.8,
            }

        if clean_seq[0] == "right" and clean_seq[-1] == "left":
            return {
                "scenario": "looking_right_to_left",
                "confidence": 0.8,
            }

        if first_half.count("front") > len(first_half)*0.6 and clean_seq[-1] == "left":
            return {
                "scenario": "turning_to_left",
                "confidence": 0.75,
            }

        if first_half.count("front") > len(first_half)*0.6 and clean_seq[-1] == "right":
            return {
                "scenario": "turning_to_right",
                "confidence": 0.75,
            }

        changes = sum(1 for i in range(1, n) if clean_seq[i] != clean_seq[i-1])
        if changes >= n * 0.5:
            return {
                "scenario": "scanning",
                "confidence": 0.7,
            }

        if dominant == "left" and dominant_ratio > 0.6:
            return {
                "scenario": "looking_left",
                "confidence": 0.75,
            }

        if dominant == "right" and dominant_ratio > 0.6:
            return {
                "scenario": "looking_right",
                "confidence": 0.75,
            }

        return {
            "scenario": "mixed",
            "confidence": 0.5,
            "details": f"Séquence mixte : {clean_seq}"
        }


    def annotate(self, frame, result):
        if result is None:
            return frame

        if not result.pose_landmarks:
            return frame

        height, width = frame.shape[:2]

        for pose_landmarks in result.pose_landmarks:
            for start_idx, end_idx in self.pose_connections:

                start = pose_landmarks[start_idx]
                end = pose_landmarks[end_idx]

                x1 = int(start.x * width)
                y1 = int(start.y * height)

                x2 = int(end.x * width)
                y2 = int(end.y * height)

                if (
                    0 <= x1 < width
                    and 0 <= y1 < height
                    and 0 <= x2 < width
                    and 0 <= y2 < height
                ):
                    cv2.line(
                        frame,
                        (x1, y1),
                        (x2, y2),
                        (255, 255, 255),
                        2,
                        cv2.LINE_AA
                    )

            for index, landmark in enumerate(pose_landmarks):

                x = int(landmark.x * width)
                y = int(landmark.y * height)

                if not (
                    0 <= x < width
                    and 0 <= y < height
                ):
                    continue

                cv2.circle(
                    frame,
                    (x, y),
                    4,
                    (0, 255, 0),
                    -1,
                    cv2.LINE_AA
                )

            for index, landmark in enumerate(pose_landmarks):

                x = int(landmark.x * width)
                y = int(landmark.y * height)

                if not (
                    0 <= x < width
                    and 0 <= y < height
                ):
                    continue

                cv2.putText(
                    frame,
                    str(index),
                    (x + 5, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.35,
                    (255, 255, 255),
                    1,
                    cv2.LINE_AA
                )

        return frame






class CalculTools:
    def average_position(self, parts: list[PartPosition], use_world: bool = False) -> PartPosition:
        print("average_position")
        valid = [p for p in parts if p is not None and p.visibility > 0.5]
        if not valid:
            return None

        if use_world:
            avg_x = numpy.mean([p.world_x for p in valid])
            avg_y = numpy.mean([p.world_y for p in valid])
            avg_z = numpy.mean([p.world_z for p in valid])
        else:
            avg_x = numpy.mean([p.x for p in valid])
            avg_y = numpy.mean([p.y for p in valid])
            avg_z = numpy.mean([p.z for p in valid])

        avg_vis = numpy.mean([p.visibility for p in valid])

        return PartPosition(
            name="average",
            x=avg_x,
            y=avg_y,
            z=avg_z,
            visibility=avg_vis,
            world_x=avg_x if use_world else 0.0,
            world_y=avg_y if use_world else 0.0,
            world_z=avg_z if use_world else 0.0
        )


    def distance_2d(self, p1: PartPosition, p2: PartPosition) -> float:
        return numpy.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)
    def distance_2d_points(self, x1, y1, x2, y2) -> float:
        return ((x1 - x2)**2 + (y1 - y2)**2) ** 0.5

    def distance_3d(self, p1: PartPosition, p2: PartPosition, use_world: bool = True) -> float:
        if use_world:
            return numpy.sqrt(
                (p1.world_x - p2.world_x)**2 +
                (p1.world_y - p2.world_y)**2 +
                (p1.world_z - p2.world_z)**2
            )
        else:
            return numpy.sqrt(
                (p1.x - p2.x)**2 +
                (p1.y - p2.y)**2 +
                (p1.z - p2.z)**2
            )


    def midpoint(self, p1: PartPosition, p2: PartPosition) -> PartPosition:
        return PartPosition(
            name="midpoint",
            x=(p1.x + p2.x) / 2,
            y=(p1.y + p2.y) / 2,
            z=(p1.z + p2.z) / 2,
            visibility=min(p1.visibility, p2.visibility),
            world_x=(p1.world_x + p2.world_x) / 2,
            world_y=(p1.world_y + p2.world_y) / 2,
            world_z=(p1.world_z + p2.world_z) / 2
        )


    def angle_between_points(self, a: PartPosition, b: PartPosition, c: PartPosition) -> float:
        ba = numpy.array([a.x - b.x, a.y - b.y])
        bc = numpy.array([c.x - b.x, c.y - b.y])

        cosine = numpy.dot(ba, bc) / (numpy.linalg.norm(ba) * numpy.linalg.norm(bc) + 1e-6)
        angle = numpy.degrees(numpy.arccos(numpy.clip(cosine, -1.0, 1.0)))
        return angle

    