import sqlite3
import numpy
import soundfile

from pathlib import Path
from datetime import datetime

from tools.utils import Utils

utils = Utils()

class VoiceDatabase:
    def __init__(self, database_path):
        self.database_path = Path(database_path)

        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        #self.connection = sqlite3.connect(self.database_path)
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
                name TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'unknown',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS voice_samples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    person_id INTEGER,

                    filename TEXT NOT NULL,
                    duration REAL,

                    created_at TEXT NOT NULL,

                    FOREIGN KEY (person_id)
                    REFERENCES persons(id)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS voice_embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    sample_id INTEGER NOT NULL,

                    dimensions INTEGER NOT NULL,
                    embedding BLOB NOT NULL,

                    created_at TEXT NOT NULL,

                    FOREIGN KEY (sample_id)
                    REFERENCES voice_samples(id)
                )
            """)

            connection.commit()
        finally:
            connection.close()

    def add_person(self, name, status):
        connection = self.get_connection()
        try:
            now = datetime.now().isoformat()
            cursor = connection.cursor()

            id = utils.generate_id_number()
            print(id)
            cursor.execute("""
                INSERT INTO persons (
                    id,
                    name,
                    status,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                id,
                name,
                status,
                now,
                now
            ))
            connection.commit()
            return id
        finally:
            connection.close()

    def add_voice_sample(self, filename, duration, person_id=None):
        connection = self.get_connection()
        try:
            now = datetime.now().isoformat()
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO voice_samples (
                    person_id,
                    filename,
                    duration,
                    created_at
                )
                VALUES (?, ?, ?, ?)
            """, (
                person_id,
                str(filename),
                float(duration),
                now
            ))

            connection.commit()
            sample_id = cursor.lastrowid

            return sample_id
        finally:
            connection.close()
            
    def add_voice_embedding(self, sample_id, embedding):
        embedding = numpy.asarray(embedding, dtype=numpy.float32)
        dimensions = embedding.shape[0]
        embedding_blob = embedding.tobytes()
        connection = self.get_connection()

        try:
            cursor = connection.cursor()
            time = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO voice_embeddings (
                    sample_id,
                    dimensions,
                    embedding,
                    created_at
                )
                VALUES (?, ?, ?, ?)
            """, (
                sample_id,
                dimensions,
                embedding_blob,
                time
            ))

            connection.commit()
            return cursor.lastrowid
        finally:
            connection.close()



    def show_database(self):
        connection = self.get_connection()
        try:
            cursor = connection.cursor()


            print("DATABASE")
            print("TABLES")

            cursor.execute("""
                SELECT name
                FROM sqlite_master
                WHERE type='table'
                ORDER BY name
            """)

            tables = cursor.fetchall()

            for table in tables:
                print(f" - {table[0]}")

            print("PERSONS")

            cursor.execute("""
                SELECT
                    id,
                    name,
                    status,
                    created_at,
                    updated_at
                FROM persons
                ORDER BY id
            """)

            persons = cursor.fetchall()

            if not persons:
                print("Aucune personne.")

            else:
                for person in persons:
                    print(
                        f"ID={person[0]} | "
                        f"Nom={person[1]} | "
                        f"Status={person[2]} | "
                        f"Created={person[3]}"
                    )

            print()
            print("VOICE SAMPLES")

            cursor.execute("""
                SELECT
                    voice_samples.id,
                    persons.name,
                    voice_samples.filename,
                    voice_samples.duration,
                    voice_samples.created_at
                FROM voice_samples
                LEFT JOIN persons
                    ON persons.id = voice_samples.person_id
                ORDER BY voice_samples.id
            """)

            samples = cursor.fetchall()

            if not samples:
                print("Aucun échantillon vocal.")
            else:
                for sample in samples:

                    print(
                        f"ID={sample[0]} | "
                        f"Person={sample[1]} | "
                        f"File={sample[2]} | "
                        f"Duration={sample[3]}s"
                    )

            print()
            print("VOICE EMBEDDINGS")

            cursor.execute("""
                SELECT
                    id,
                    sample_id,
                    dimensions,
                    length(embedding)
                FROM voice_embeddings
                ORDER BY id
            """)

            embeddings = cursor.fetchall()

            if not embeddings:
                print("Aucun embedding.")
            else:
                for embedding in embeddings:

                    print(
                        f"ID={embedding[0]} | "
                        f"Sample={embedding[1]} | "
                        f"Dimensions={embedding[2]} | "
                        f"Bytes={embedding[3]}"
                    )


            print()
            print("STRUCTURE VOICE_SAMPLES")

            cursor.execute("""
                PRAGMA table_info(voice_samples)
            """)
            columns = cursor.fetchall()
            for column in columns:
                print(column)
            connection.commit()
        finally:
            connection.close()

    def add_audio_sample(self, audio, sample_rate, audio_path, filename, person_id=None ):
        audio = numpy.asarray(audio,dtype=numpy.float32)
        duration = len(audio) / sample_rate

        #id = utils.generate_id()
        #filename = (f"voice_{id}.wav")
        audio_directory = (self.database_path.parent / "unknown")
        audio_directory.mkdir(parents=True, exist_ok=True)

        #audio_path = (audio_directory / filename)
        #soundfile.write(audio_path,audio,sample_rate )

        sample_id = self.add_voice_sample(
            filename=str(audio_path),
            duration=duration,
            person_id=person_id
        )

        print()
        print("============================================")
        print("ADD AUDIO SAMPLE")
        print("============================================")
        print(f"Audio duration : {duration:.3f}s")
        print(f"Generated ID   : {id}")
        print(f"Filename       : {filename}")
        print(f"Audio path     : {audio_path}")
        print(f"sample id     : {sample_id}")

        return {
            "sample_id": sample_id,
            "filename": str(audio_path),
            "duration": duration,
            "person_id": person_id
        }

