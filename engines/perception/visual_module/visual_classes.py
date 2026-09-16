from dataclasses import dataclass
from typing import Any


@dataclass
class VisionPerson:
    track_id: int = 0
    database_id: int = 0

    identity: str = ""
    identity_confidence: float = 0.0

    box_sizes: Any = None
    box_positions: Any = None

    previous_box_sizes: Any = None
    previous_box_positions: Any = None

    face_embedding: Any = None

    events: Any = None
        
    last_seen: float = 0.0
    is_focused: bool = False

    def update_from(self, other: "VisionPerson"):
        self.previous_box_sizes = self.box_sizes
        self.previous_box_positions = self.box_positions

        self.box_sizes = other.box_sizes
        self.box_positions = other.box_positions
        
        self.last_seen = 0.0

# xywh = box_sizes = [x_center, y_center, width, height]
# xyxy = box_positions = [x1, y1, x2, y2]

@dataclass
class VisionObject:
    track_id: int = 0

    class_id:int = 0
    class_name:str = ""

    confidence:float = 0.0

    box_sizes: Any = None
    box_positions: Any = None

    previous_box_sizes: Any = None
    previous_box_positions: Any = None

    events: Any = None

    last_seen: float = 0.0
    
    def update_from(self, other: "VisionObject"):
        self.previous_box_sizes = self.box_sizes
        self.previous_box_positions = self.box_positions

        self.box_sizes = other.box_sizes
        self.box_positions = other.box_positions

        self.confidence = other.confidence
        self.last_seen = 0.0


@dataclass
class ValueInfos:
    text: str = "unknown"
    value: float = 0.0
    confidence: float = 0.0


@dataclass
class PerspectiveInfo:
    facing: ValueInfos | None = None          # "front", "left", "right", "back"
    camera_angle: ValueInfos | None = None    # "eye_level", "high", "low" (plongée / contre-plongée)
    overall_confidence: float = 0.0


@dataclass
class PartPosition:
    name: str = ""
    index: int = -1

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    visibility: float = 0.0

    world_x: float = 0.0
    world_y: float = 0.0
    world_z: float = 0.0

    def is_visible(self, threshold: float = 0.5) -> bool:
        return self.visibility >= threshold
    
    def update_from(self, other : "PartPosition"):
        self.x = other.x
        self.y = other.y
        self.z = other.z
        self.visibility = other.visibility

        self.world_x = other.world_x
        self.world_y = other.world_y
        self.world_z = other.world_z

@dataclass
class PersonEyes:
    inner: PartPosition | None = None
    middle: PartPosition | None = None
    outer: PartPosition | None = None

@dataclass
class PersonMouth:
    left: PartPosition | None = None
    right: PartPosition | None = None

@dataclass
class PersonFace:
    eye_l: PersonEyes | None = None
    eye_r: PersonEyes | None = None
    ear_l: PartPosition | None = None
    ear_r: PartPosition | None = None
    nose: PartPosition | None = None
    mouth: PersonMouth | None = None

@dataclass
class PersonHand:
    pinky: PartPosition | None = None
    index: PartPosition | None = None
    thumb: PartPosition | None = None

@dataclass
class PersonArm:
    shoulder: PartPosition | None = None
    elbow: PartPosition | None = None
    wrist: PartPosition | None = None

@dataclass
class PersonLeg:
    hip: PartPosition | None = None
    knee: PartPosition | None = None
    ankle: PartPosition | None = None
    heel: PartPosition | None = None
    foot: PartPosition | None = None 

@dataclass
class Person:
    face: PersonFace | None = None
    arm_l: PersonArm | None = None
    arm_r: PersonArm | None = None
    hand_l: PersonHand | None = None
    hand_r: PersonHand | None = None
    leg_l: PersonLeg | None = None
    leg_r: PersonLeg | None = None












