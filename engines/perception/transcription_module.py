import asyncio

import numpy
import torch
from faster_whisper import WhisperModel

from core.messages import Message

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

class TranscriptionModule:
    def __init__(self, bus):
        self.message_bus = bus

        print("DEVICE ", DEVICE)
        self.model = WhisperModel("large-v3", device=DEVICE, compute_type="float16")
        self.message_bus.subscribe("AudioSpeakerOrganized", self.audio_message)


    async def audio_message(self, message):
        audio_list = message.data["audio"]
        #print("TranscriptionModule audio audio_list ", audio_list)

        discussion = []

        for audio_file in audio_list:
            speaker = audio_file["speaker"]
            audio = audio_file["audio"]
            text = self.audio_transcribe(audio)

            if text is not None:
                discussion.append({"speaker":speaker, "text":text})
        
        #print("TranscriptionModule discussion ", discussion)
        request = Message(
                    id="",
                    type="SttReceived",
                    timestamp= "",
                    source="audio_discussion",
                    correlation_id="",
                    data={
                        "input": discussion,
                    }
                )
        await self.message_bus.publish(request)


    def audio_transcribe(self, audio):
        audio = numpy.asarray(audio, dtype=numpy.float32)
        segments, info = self.model.transcribe(audio, beam_size=5)
        segments = list(segments)

        text = " ".join(segment.text.strip() for segment in segments)

        return {
            "text": text,
            "language": info.language,
            "language_probability": info.language_probability
        }








