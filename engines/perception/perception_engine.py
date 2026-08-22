import asyncio

from engines.perception.audio_module import AudioModule
from engines.perception.transcription_module import TranscriptionModule

class PerceptionEngine:
    def __init__(self, bus):
        self.message_bus = bus
        self.transcription_module = TranscriptionModule(self.message_bus)
        self.audio_module = AudioModule(self.message_bus)

    async def main(self):
        print("PerceptionEngine ----- main")
        await self.audio_module.main()

    def stop(self):
        print("PerceptionEngine.stop()")
        self.audio_module.stop()