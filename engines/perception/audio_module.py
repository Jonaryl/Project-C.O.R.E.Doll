import os
import queue
from datetime import datetime
import time
import threading
import asyncio

import numpy
import sounddevice
import torch
import soundfile

from pyannote.audio import Pipeline
#from pyannote.audio import Model
from pyannote.audio.pipelines.speaker_verification import PretrainedSpeakerEmbedding

from transformers import AutoFeatureExtractor
from transformers import AutoModelForAudioClassification

from silero_vad import load_silero_vad

from tools.keyVar import KeyVar
from tools.file_r import FileRead
from core.messages import Message
from engines.perception.voice_database import VoiceDatabase

key_var = KeyVar()
file_read = FileRead()

is_activated = True

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
HF_TOKEN = os.environ.get("HF_TOKEN")

class AudioModule:
    def __init__(self, bus):
        self.message_bus = bus
        self.vad_queue = queue.Queue()
        self.sound_queue = queue.Queue()
        self.pyannote_queue = queue.Queue()

        self.audio_config = file_read.read_json_file(key_var.get_audio_config())

        self.stop_event = threading.Event()

        self.vad_module = VADModule(self.message_bus, self.vad_queue, self.pyannote_queue, self.stop_event)
        self.sound_module = SoundModule(self.message_bus, self.sound_queue, self.stop_event)
        self.pyannote_module = PyannoteModule(self.message_bus, self.pyannote_queue, self.stop_event)
        self.voice_manager = VoiceManager(self.message_bus, self.pyannote_module)

    def audio_callback(self, indata, frames, time_info, status):
        if status:
            print("Audio status:", status)

        audio = indata[:, 0].copy()

        self.vad_queue.put(audio)
        self.sound_queue.put(audio)

    async def main(self):
        print("AudioModule main")
        sample_rate = self.audio_config["vad_config"]["sample_rate"]
        channels = self.audio_config["vad_config"]["channels"]
        chunk_size = self.audio_config["vad_config"]["chunk_size"]
        
        sound_thread = threading.Thread(
            target=self.sound_module.run,
            name="SoundModule",
            daemon=True
        )
        vad_thread = threading.Thread(
            target=self.vad_module.run,
            name="VADModule",
            daemon=True
        )

        sound_thread.start()
        vad_thread.start()
        pyannote_task = asyncio.create_task(self.pyannote_module.run(), name="PyannoteModule")

        with sounddevice.InputStream(
            samplerate=sample_rate,
            channels=channels,
            dtype="float32",
            blocksize=chunk_size,
            callback=self.audio_callback
        ):
            print("Microphone ACTIVATED.")
            try:
                while is_activated:
                    await asyncio.sleep(0.1)

            except asyncio.CancelledError:
                print("AudioModule cancelled")

            finally:
                print("ARRÊT AUDIO")
                self.stop_event.set()
                pyannote_task.cancel()
                try:
                    await pyannote_task
                except asyncio.CancelledError:
                    pass

                # 3. Attendre les threads
                sound_thread.join(timeout=2)
                vad_thread.join(timeout=2)

                print("AudioModule stoped.")

    def stop(self):
        print("AudioModule.stop()")
        self.stop_event.set()

class VADModule:
    def __init__(self, bus, queue, pyqueue, stop):
        self.message_bus = bus
        self.vad_queue = queue
        self.pyannote_queue = pyqueue
        self.stop_event = stop

        self.audio_config = file_read.read_json_file(key_var.get_audio_config())

        self.audio_buffer = []
        self.is_speaking = False
        self.timer_paused = False
        self.timer_duration = self.audio_config["pyannote_confing"]["timer_duration"]
        self.timer_end = None

        self.audio_duration = 0.0
        self.max_audio_duration = self.audio_config["pyannote_confing"]["max_audio_duration"]
        self.chunk_overlimit = False

        self.vad_model = load_silero_vad()

    def reset_timer(self):
        self.timer_paused = False
        self.timer_end = time.monotonic() + self.timer_duration
    def timer_running(self):
            return (
                self.timer_end is not None
                and time.monotonic() < self.timer_end
            )
    def pause_timer(self):
        if self.timer_running():
            print("!----- pause_timer. self.timer_running")
            self.timer_end = None
            self.timer_paused = True
    def timer_finished(self):
        if self.timer_paused:
            return False
        else:
            return (
                self.timer_end is not None
                and time.monotonic() >= self.timer_end
            )

    def run(self):
        sample_rate = self.audio_config["vad_config"]["sample_rate"]
        threshold = self.audio_config["vad_config"]["threshold"]

        print("VAD")

        previous_state = None

        while not self.stop_event.is_set():
            if is_activated:
                try:
                    audio_chunk = self.vad_queue.get(timeout=0.2)
                    audio_tensor = torch.from_numpy(audio_chunk)
                    speech_probability = self.vad_model(audio_tensor,sample_rate).item()
                    is_speech = speech_probability >= threshold

                    if is_speech:
                        self.audio_buffer.append(audio_chunk.copy())
                        chunk_duration = len(audio_chunk) / sample_rate
                        self.audio_duration += chunk_duration
                        self.is_speaking = True
                        #print(f"[{timestamp}] - VOICE OK - (probabilité={speech_probability:.2f})")
                    else:
                        if previous_state:
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                            print(f"[{timestamp}] - VOICE VOID - (probabilité={speech_probability:.2f})")
                        self.is_speaking = False
                        if self.audio_duration >= self.max_audio_duration:
                            print(f"self.is_speaking = False -- Audio accumulé : {self.audio_duration:.2f}s")
                            self.chunk_overlimit = True

                    if is_speech != previous_state:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                        if is_speech:
                            #print(f"[{timestamp}] - VOICE OK - (probabilité={speech_probability:.2f})")
                            self.pause_timer()
                        else:
                            self.reset_timer()
                        previous_state = is_speech  

                    if self.is_speaking is False and self.timer_finished() or self.chunk_overlimit:
                            if not self.audio_buffer:
                                #print("ATTENTION : buffer audio vide.")
                                continue
                            #print(f"Timer end  Audio accumulé : {self.audio_duration:.2f}s")

                            speech_audio = numpy.concatenate(self.audio_buffer)
                            duration = (len(speech_audio)/ sample_rate)
                            #print("Timer end duration", duration)  
                            self.pyannote_queue.put(speech_audio)
                            
                            self.timer_end = None
                            self.chunk_overlimit = False
                            self.audio_duration = 0.0
                            self.audio_buffer.clear()
                    else:
                        if self.timer_end != None:
                            remaining = self.timer_end - time.monotonic()
                            #print("TIMER =", remaining) 
                except queue.Empty:
                    continue       
                except KeyboardInterrupt:
                    print("\nVAD AUDIO Stop.")


class SoundModule:
    def __init__(self, bus, queue, stop):
        self.message_bus = bus
        self.audio_queue = queue
        self.stop_event = stop

        self.audio_config = file_read.read_json_file(key_var.get_audio_config())
        self.sample_rate = self.audio_config["vad_config"]["sample_rate"]

        print("SOUND EVENT DETECTION")
        print(f"Device : {DEVICE}")
        if DEVICE == "cuda":
            print(f"GPU    : {torch.cuda.get_device_name(0)}")
    
        model_name = self.audio_config["sound_config"]["model"]

        self.processor = AutoFeatureExtractor.from_pretrained(model_name)
        self.model = AutoModelForAudioClassification.from_pretrained(model_name)

        self.model.to(DEVICE)
        self.model.eval()

        self.top_k = self.audio_config["sound_config"]["top_k"]
        self.target_sample = self.audio_config["vad_config"]["sample_rate"]
        self.buffer_duration = self.audio_config["sound_config"]["buffer_duration"]

        self.buffer_size = int(self.sample_rate * self.buffer_duration)
        self.audio_buffer = numpy.zeros(self.buffer_size, dtype=numpy.float32)


        print("Model Loaded.")
        print(f"AST buffer : {self.buffer_duration}s")

    def run(self):  
        while not self.stop_event.is_set():
            if is_activated:
                try:
                    audio_chunk = self.audio_queue.get(timeout=0.2)
                    chunk_size = len(audio_chunk)

                    if chunk_size >= self.buffer_size:
                        self.audio_buffer = (audio_chunk[-self.buffer_size:])
                    else:
                        self.audio_buffer = numpy.roll(self.audio_buffer, -chunk_size)
                        self.audio_buffer[-chunk_size:] = (audio_chunk)

                    if not hasattr(self, "_buffer_filled"):
                        self._buffer_filled = 0

                    self._buffer_filled += chunk_size
                    if self._buffer_filled < self.buffer_size:
                        continue

                    self.detect_events()
                    self._buffer_filled = 0
                except queue.Empty:
                    continue    
                except KeyboardInterrupt:
                    print("\nSoundModule Stop.")
                    break

    def detect_events(self):
        inputs = self.processor(
            self.audio_buffer,
            sampling_rate=self.sample_rate,
            return_tensors="pt"
        )
        inputs = {
            key: value.to(DEVICE)
            for key, value in inputs.items()
        }     

        with torch.no_grad():
            outputs = self.model(**inputs)
            probabilities = torch.softmax(
                outputs.logits,
                dim=-1
            )[0]

        top_probabilities, top_indices = torch.topk(
            probabilities,
            self.top_k
        )

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        #print()
        #print(f"[{timestamp}] SOUND DETECTED")

        for probability, index in zip(
            top_probabilities,
            top_indices
        ):
            label = self.model.config.id2label[
                index.item()
            ]
            score = probability.item()
            #print(f"{label:35} {score:.3f}")

class PyannoteModule:
    def __init__(self, bus, queue, stop):
        self.message_bus = bus
        self.pyannote_queue = queue
        self.stop_event = stop

        self.pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-community-1",token=HF_TOKEN)
        self.pipeline.to(torch.device(DEVICE))

        #self.embedding_model = PretrainedSpeakerEmbedding("pyannote/embedding", device=torch.device(DEVICE), token=HF_TOKEN)

        self.audio_config = file_read.read_json_file(key_var.get_audio_config())
        self.sample_rate = self.audio_config["vad_config"]["sample_rate"]
        self.voice_database = VoiceDatabase(key_var.get_voice_database())

        self.similarity_threshold = self.audio_config["pyannote_confing"]["similarity_threshold"]

    async def run(self):
        while not self.stop_event.is_set():
            try:
                speech_audio = await asyncio.to_thread( self.pyannote_queue.get)

                duration = (len(speech_audio)/ self.sample_rate)
                #print(f"PyannoteModule run duration {duration:.2f}s")

                waveform = torch.from_numpy(speech_audio).float()
                waveform = waveform.unsqueeze(0)

                audio = {
                    "waveform": waveform,
                    "sample_rate": self.sample_rate
                }

                start_time = time.perf_counter()
                output = self.pipeline(audio)
                elapsed = (time.perf_counter()- start_time)
                #print(f"Temps Pyannote : {elapsed:.3f}s")

                diarization = (output.speaker_diarization)
                #print("LOCUTEURS :")
                speakers = set()

                for (segment,_,speaker) in diarization.itertracks(yield_label=True):

                    speakers.add(speaker)

                    #print(
                    #    f"    "
                    #    f"{segment.start:.2f}s -> "
                    #    f"{segment.end:.2f}s "
                    #    f"{speaker}"
                    #)

                    print("Nombre de locuteurs :",len(speakers))

                request = Message(
                            id="",
                            type="VoicesMessageReceived",
                            timestamp= "",
                            source="",
                            correlation_id="",
                            data={
                                "audio": speech_audio,
                                "diarization": diarization,
                            }
                        )
                await self.message_bus.publish(request)
            
            except asyncio.CancelledError:
                print("PyannoteModule Stop.")
                raise
            except Exception as e:
                print("ERREUR PYANNOTE")
                print(type(e).__name__, ":", e)

    def find_matching_person(self, audio, people):
        best_match = None
        best_similarity = -1.0

        new_embedding = (self.extract_embedding(audio))

        for person_directory in people:
            embeddings = (self.load_person_embeddings(person_directory))

            for embedding in embeddings:
                similarity = (self.cosine_similarity(new_embedding, embedding))

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = { "directory": person_directory, "similarity": similarity}

        if (best_match is not None and best_match["similarity"] >= self.similarity_threshold):
            return best_match

        return None

    def cosine_similarity(self, embedding_a, embedding_b):
        embedding_a = numpy.asarray(embedding_a, dtype=numpy.float32)
        embedding_b = numpy.asarray(embedding_b, dtype=numpy.float32)

        norm_a = numpy.linalg.norm(embedding_a)
        norm_b = numpy.linalg.norm(embedding_b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(numpy.dot(embedding_a, embedding_b)/ (norm_a * norm_b))
    def load_person_embeddings(self, person_directory):
        embeddings = []
        person_name = person_directory.name
        connection = self.voice_database.get_connection()

        try:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT
                    voice_embeddings.embedding,
                    voice_embeddings.dimensions
                FROM voice_embeddings
                INNER JOIN voice_samples
                    ON voice_samples.id =
                    voice_embeddings.sample_id
                INNER JOIN persons
                    ON persons.id =
                    voice_samples.person_id
                WHERE persons.name = ?
            """, (
                person_name,
            ))

            rows = cursor.fetchall()
            for embedding_blob, dimensions in rows:
                embedding = numpy.frombuffer(embedding_blob, dtype=numpy.float32)

                if len(embedding) != dimensions:
                    print("Attention : dimensions embedding === incorrectes.")
                    continue
                embeddings.append(embedding)
            return embeddings
        finally:
            connection.close()

    def extract_embedding(self, audio):
        waveform = torch.from_numpy(numpy.asarray(audio, dtype=numpy.float32))

        if waveform.dim() == 1:
            waveform = waveform.unsqueeze(0)

        audio_input = {
            "waveform": waveform,
            "sample_rate": self.sample_rate
        }

        with torch.inference_mode():
            output = self.pipeline(audio_input)

        embeddings = output.speaker_embeddings

        if isinstance(embeddings, torch.Tensor):
            embeddings = embeddings.detach().cpu().numpy()

        embeddings = numpy.asarray(embeddings, dtype=numpy.float32)
        #print("Embedding pipeline :", embeddings.shape)

        # 1 embedding
        if embeddings.ndim == 1:
            return embeddings

        # ++ embeddings
        if embeddings.ndim == 2:
            embedding = numpy.mean(embeddings, axis=0)
            return embedding.astype(numpy.float32)

        raise ValueError(f"Shape embedding inattendue : {embeddings.shape}")

    def add_person_to_database(self, speaker, status):
        id = self.voice_database.add_person(speaker, status)
        return id
    def add_audio_to_database(self, audio, person_id, audio_path, filename):
        sample = self.voice_database.add_audio_sample(
                audio=audio,
                sample_rate=self.sample_rate,
                person_id=person_id,
                filename=filename,
                audio_path=audio_path
            )
                    
        #print("VOICE SAMPLE SAUVEGARDÉ")
        #print( f"ID       : {sample['sample_id']}")
        #print(f"Fichier  : {sample['filename']}")
        #print(f"Durée    : {sample['duration']:.2f}s")
        #print( f"Personne : {sample['person_id']}")
        return sample
    def add_embeddings_to_database(self, audio, sample_id):
        embedding = self.extract_embedding(audio)

        print("Embedding :",type(embedding),embedding.shape)

        self.voice_database.add_voice_embedding(sample_id, embedding)

    def show_database(self):
        self.voice_database.show_database()

class VoiceManager:
    def __init__(self, bus, pyannote):
        self.message_bus = bus
        self.pyannote_module = pyannote
        
        self.unknown_directory = (key_var.get_voice_database().parent / "unknown")
        self.known_directory = (key_var.get_voice_database().parent / "known")

        self.audio_config = file_read.read_json_file(key_var.get_audio_config())
        self.max_samples_per_person = self.audio_config["voice_config"]["max_samples_per_person"]     
        self.sample_rate = self.audio_config["vad_config"]["sample_rate"]
        self.min_audio_duration = self.audio_config["voice_config"]["min_audio_duration"]

        self.message_bus.subscribe("VoicesMessageReceived", self.manage_voices)

    async def manage_voices(self, message):
        speech_audio = message.data["audio"]
        diarization = message.data["diarization"]

        print(" ================  diarization === ", diarization)

        speakers_audio = self.extract_speaker_audio(speech_audio, diarization)
        speakers_audio_merged = self.merge_speaker_audio(speakers_audio)

        data = self.process_speakers(speakers_audio_merged)

        organized_audio = self.save_speaker_audio(data)

        request = Message(
            id="",
            type="AudioSpeakerOrganized",
            timestamp= "",
            source="",
            correlation_id="",
            data={
                "audio": organized_audio,
            }
        )
        await self.message_bus.publish(request)

        self.pyannote_module.show_database()
    
    def extract_speaker_audio(self, speech_audio, diarization):
        speakers_audio = {}

        for segment, _, speaker in diarization.itertracks( yield_label=True):
            duration = segment.end - segment.start

            if duration < self.min_audio_duration:
                print(
                    f"Segment ignoré : "
                    f"{speaker} "
                    f"{segment.start:.2f}s -> "
                    f"{segment.end:.2f}s "
                    f"({duration:.3f}s)"
                )
                continue
            start_sample = int(segment.start * self.sample_rate)
            end_sample = int(segment.end * self.sample_rate)

            segment_audio = speech_audio[start_sample:end_sample]

            if speaker not in speakers_audio:
                speakers_audio[speaker] = []

            speakers_audio[speaker].append(segment_audio)

        return speakers_audio

    def merge_speaker_audio(self, speakers_audio):
        merged_audio = {}

        for speaker, segments in speakers_audio.items():
            if not segments:
                continue

            merged_audio[speaker] = numpy.concatenate(segments)
        
        return merged_audio

    def get_known_people(self):
        if not self.known_directory.exists():
            return []

        return [
            directory
            for directory in self.known_directory.iterdir()
            if directory.is_dir()
        ]
    def get_unknown_people(self):
        if not self.unknown_directory.exists():
            return []

        return [
            directory
            for directory in self.unknown_directory.iterdir()
            if directory.is_dir()
        ]

    def get_audio_files(self, directory):
        extensions = {".wav",".mp3",".flac",".ogg"}

        return [
            file
            for file in directory.iterdir()
            if (
                file.is_file()
                and file.suffix.lower() in extensions
            )
        ]

    def add_audio_to_person(self, audio, sample_rate, person_directory):
        #print("----------- VoiceManager add_audio_to_person")
        audio_files = self.get_audio_files(person_directory)

        if len(audio_files) >= self.max_samples_per_person:
            print(f"Limite atteinte : "f"{person_directory.name}")
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = (f"voice_{timestamp}.wav")

        audio_path = (person_directory / filename)
        #soundfile.write(audio_path, audio, sample_rate)

        return audio_path

    def process_speakers(self, speakers_audio):
        unmatched = []
        matched = []

        known_people = self.get_known_people()
        unknown_people = self.get_unknown_people()

        for speaker, audio in speakers_audio.items():
            #print("=" * 60)
            print(f"TRAITEMENT : {speaker}")
            #print("=" * 60)

            # KNOWN
            match = self.pyannote_module.find_matching_person(audio, known_people)
            if match is not None:
                person_directory = match["directory"]
                #print(f"Correspondance KNOWN : {person_directory.name}")

                self.add_audio_to_person(audio, self.sample_rate, person_directory)
                matched.append({"speaker": speaker,"audio": audio})
                continue

            # UNKNOWN
            match = self.pyannote_module.find_matching_person(audio, unknown_people)
            if match is not None:
                person_directory = match["directory"]
                #print(f"Correspondance UNKNOWN : {person_directory.name}")

                self.add_audio_to_person(audio, self.sample_rate, person_directory)
                matched.append({"speaker": speaker,"audio": audio})
                continue


            #print(f"Aucune correspondance : {speaker}")
            unmatched.append({"speaker": speaker,"audio": audio})

        return {
            "unmatched":unmatched,
            "matched":matched
        }

    def save_speaker_audio(self, data):
        print("----------- VoiceManager save_speaker_audio")

        unmatched = data["unmatched"]
        matched = data["matched"]

        for item in unmatched:
            speaker_audio = item["speaker"]
            audio = numpy.asarray(item["audio"], dtype=numpy.float32)

            name = "new_person"
            number = 1
            while True:
                folder = self.unknown_directory / f"{name}_{number:03d}"

                if not folder.exists():
                    folder.mkdir(parents=True)
                    break
                number += 1


            speaker = f"new_person_{number:03d}"
            filename = (f"{speaker}.wav")
            audio_path = (self.unknown_directory / f"{name}_{number:03d}" / filename)

            try:
                soundfile.write(audio_path, audio, self.sample_rate)
            except Exception as e:
                print("ERREUR SOUND FILE")
                print(type(e).__name__, ":", e)
                continue
            if not audio_path.exists():
                print("ERREUR : fichier WAV non créé.")
                continue

            person_id = self.pyannote_module.add_person_to_database(speaker, "unknown")
            sample = self.pyannote_module.add_audio_to_database(audio, person_id, audio_path, filename)
            self.pyannote_module.add_embeddings_to_database(audio, sample['sample_id'])

            matched.append({"speaker": speaker,"audio": audio})

        return matched






    