import cv2
import numpy
from insightface.app import FaceAnalysis

from engines.perception.visual_module.visual_database import VisualDatabase
from tools.keyVar import KeyVar

key_var = KeyVar()

class VisualRecognition:
    def __init__(self):
        self.app = FaceAnalysis(
            name="buffalo_l",
            providers=["CUDAExecutionumpyrovider", "CPUExecutionumpyrovider"]
        )

        self.app.prepare(ctx_id=0,det_size=(640, 640))

        self.vision_database = VisualDatabase(key_var.get_vision_database())
        self.vision_data = self.initialize_vision_database()
        
        #self.show_database()

    def initialize_vision_database(self):
        data = self.vision_database.get_all_datas()
        return data

    def add_person(self, identity):
        person_id = self.vision_database.add_person(identity)
        self.vision_data[person_id] = {
                    "identity": identity,
                    "embeddings": []
                }
        return person_id

    def add_face_embedding(self, person_id, filename, embedding):
        #print("VisualRecognition add_face_embedding person_id = ", person_id, "/// filename = ", filename, "//// len(embedding) = ", len(embedding))
        self.vision_database.add_face_embedding(person_id, filename, embedding)
        new_person_data = self.vision_database.get_person_embeddings(person_id)

        self.vision_data[person_id] = {
            "identity": self.vision_data.get(person_id, {}).get("identity", ""),
            "embeddings": new_person_data
        }

    def detect_faces(self, image):
        if image is None:
            return []

        faces = self.app.get(image)
        return faces
    
    def recognize(self, image):
        faces = self.detect_faces(image)
        results = []

        for face in faces:
            embedding = face.embedding

            results.append({
                "bbox": face.bbox,
                "embedding": embedding,
                "det_score": face.det_score
            })

        return results

    def compare(self, image1, image2):
        # Implement your comparison logic here
        # For example, you can compare the recognized objects in both images
        # and return a similarity score or a list of differences.
        similarity_score = 0.0  # Replace with actual comparison results
        return similarity_score

    def face_embedding(self, face_image):
        # Implement your face embedding logic here
        # For example, you can use a pre-trained model to extract facial features
        # and return a vector representation of the face.
        embedding_vector = []  # Replace with actual embedding results
        return embedding_vector

    def database_recognition(self, face_image):
        image_faces = self.recognize(face_image)
        if not image_faces or len(image_faces) != 1:
            return {
                "identity": "unknown",
                "identity_id": None,
                "score": 0.0
            }
        new_embedding = image_faces[0]["embedding"]

        best_person_id = None
        best_score = 0.0
        best_person_identity = None

        for person_id, person in self.vision_data.items():
            data_embedding_list = person["embeddings"]
            person_best_score  = 0.0
            for data_embedding in data_embedding_list:
                score  = self.embedding_compare(new_embedding, data_embedding["embedding"])
                person_best_score  = max(person_best_score , score)
            if person_best_score > best_score:
                best_score = person_best_score
                best_person_identity = person["identity"]
                best_person_id = person_id


        if best_person_id is None or best_score < 0.7:
            return {
                "identity": "unknown",
                "identity_id": None,
                "score": best_score
            }

        return {
            "identity": best_person_identity,
            "identity_id": best_person_id,
            "score": best_score
        }

    def embedding_compare(self, embedding1, embedding2):
        embedding1 = numpy.asarray(embedding1, dtype=numpy.float32)
        embedding2 = numpy.asarray(embedding2, dtype=numpy.float32)

        norm1 = numpy.linalg.norm(embedding1)
        norm2 = numpy.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        result = numpy.dot(embedding1, embedding2) / (norm1 * norm2)
        return float(result)

    def show_database(self):
        self.vision_database.show_database()