from elevenlabs.client import ElevenLabs
from app.core.config import settings

def synthesize_speech_elevenlabs(text: str) -> bytes:
    """Synthesizes speech from text using ElevenLabs and returns the audio data."""
    try:
        client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
        audio = client.generate(
            text=text,
            voice="Rachel",  # A popular, high-quality free voice
            model="eleven_multilingual_v2"
        )
        # The result is a generator, so we concatenate the chunks
        audio_data = b"".join(audio)
        return audio_data
    except Exception as e:
        print(f"ElevenLabs synthesis failed: {e}")
        return None