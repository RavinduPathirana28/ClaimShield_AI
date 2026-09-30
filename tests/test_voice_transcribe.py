import unittest
import asyncio
from unittest.mock import AsyncMock, patch
from io import BytesIO
from fastapi import UploadFile, HTTPException
from app.api import transcribe_audio
from app import config

class TestVoiceTranscribe(unittest.TestCase):
    def test_empty_audio_raises_400(self):
        upload = UploadFile(filename="empty.webm", file=BytesIO(b""))
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(transcribe_audio(file=upload))
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Empty audio file", ctx.exception.detail)

    def test_successful_transcription(self):
        fake_response = AsyncMock()
        fake_response.status_code = 200
        fake_response.json = lambda: {"text": "The moon orbits the Earth once every 27 days."}

        upload = UploadFile(filename="speech.webm", file=BytesIO(b"RIFF_FAKE_AUDIO_DATA"))
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = fake_response
            res = asyncio.run(transcribe_audio(file=upload))
            self.assertEqual(res["status"], "success")
            self.assertEqual(res["text"], "The moon orbits the Earth once every 27 days.")
            self.assertIn("Groq Whisper", res["engine"])

if __name__ == "__main__":
    unittest.main()
