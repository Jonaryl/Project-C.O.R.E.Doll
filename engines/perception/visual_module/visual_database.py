import sqlite3

from pathlib import Path
from datetime import datetime

import numpy

from tools.utils import Utils

utils = Utils()

class VisualDatabase:
    def __init__(self, database_path):
        self.database_path = Path(database_path)

        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.create_tables()

    def get_connection(self):
        connection = sqlite3.connect(self.database_path, timeout=10)
        return connection

    def create_tables(self):
        connection = self.get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS persons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    identity TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS face_embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    person_id INTEGER NOT NULL,
                    filename TEXT,
                    embedding BLOB NOT NULL,
                    created_at TEXT NOT NULL,

                    FOREIGN KEY (person_id)
                        REFERENCES persons(id)
                        ON DELETE CASCADE
                )
            """)
            connection.commit()
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")
        finally:
            connection.close()

    def add_person(self, identity):
        connection = self.get_connection()

        try:
            cursor = connection.cursor()
            created_at = datetime.now().isoformat()

            cursor.execute("""
                INSERT INTO persons (identity, created_at)
                VALUES (?, ?)
            """, (identity, created_at))

            connection.commit()

            return cursor.lastrowid

        except sqlite3.Error as e:
            print(f"Error adding person: {e}")
            return None

        finally:
            connection.close()  

    def add_face_embedding(self, person_id, filename, embedding):
        print("VisualDatabase add_face_embedding")
        connection = self.get_connection()
        try:
            cursor = connection.cursor()
            created_at = datetime.now().isoformat()
            embedding_count = self.get_person_embeddings_count(person_id, cursor)
            #embedding_count = cursor.fetchone()[0]

            if embedding_count >= 10:
                print(f"Person ID {person_id} already has 10 embeddings. Skipping addition.")
                return

            embedding_blob = embedding.astype(numpy.float32).tobytes()
            cursor.execute("""
                INSERT INTO face_embeddings (
                    person_id,
                    filename,
                    embedding,
                    created_at
                )
                VALUES (?, ?, ?, ?)
            """, (
                person_id,
                filename,
                embedding_blob,
                created_at
            ))

            connection.commit()

        except sqlite3.Error as e:
            print(f"Error adding face embedding: {e}")
        finally:
            print("5 : VisualDatabase add_face_embedding finally")
            connection.close()

    def get_person_embeddings_count(self, person_id, cursor):
        cursor.execute("""
            SELECT COUNT(*)
            FROM face_embeddings
            WHERE person_id = ?
        """, (person_id,))
        count = cursor.fetchone()[0]
        return count

    def get_person_embeddings(self, person_id):
        print("VisualDatabase get_person_embeddings")
        connection = self.get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT filename, embedding
                FROM face_embeddings
                WHERE person_id = ?
            """, (person_id,))
            rows = cursor.fetchall()

            embeddings = []
            for row in rows:
                filename, embedding_blob = row
                embedding = numpy.frombuffer(embedding_blob, dtype=numpy.float32)
                embeddings.append((filename, embedding))

            return embeddings

        except sqlite3.Error as e:
            print(f"Error retrieving embeddings: {e}")
            return []

        finally:
            connection.close()

    def get_all_datas(self):
        connection = self.get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT persons.id, persons.identity, face_embeddings.filename, face_embeddings.embedding
                FROM persons
                LEFT JOIN face_embeddings ON persons.id = face_embeddings.person_id
            """)
            rows = cursor.fetchall()

            data = {}
            for row in rows:
                person_id, identity, filename, embedding_blob = row
                if person_id not in data:
                    data[person_id] = {
                        "identity": identity,
                        "embeddings": []
                    }
                if embedding_blob is not None:
                    embedding = numpy.frombuffer(embedding_blob, dtype=numpy.float32)
                    data[person_id]["embeddings"].append({
                        "filename": filename,
                        "embedding": embedding
                    })

            return data

        except sqlite3.Error as e:
            print(f"Error retrieving data: {e}")
            return {}

        finally:
            connection.close()

    def show_database(self):
        connection = self.get_connection()

        try:
            cursor = connection.cursor()

            print("=== Table: persons ===")
            cursor.execute("SELECT * FROM persons")
            rows = cursor.fetchall()

            if rows:
                for row in rows:
                    print(row)
            else:
                print("(vide)")

            print("\n=== Table: face_embeddings ===")
            cursor.execute("SELECT * FROM face_embeddings")
            rows = cursor.fetchall()

            if rows:
                for row in rows:
                    person_id = row[1]
                    filename = row[2]
                    embedding = row[3]
                    created_at = row[4]

                    print(
                        f"id={row[0]}, "
                        f"person_id={person_id}, "
                        f"filename={filename}, "
                        f"embedding=BLOB({len(embedding)} bytes), "
                        f"created_at={created_at}"
                    )
            else:
                print("(vide)")

        finally:
            connection.close()