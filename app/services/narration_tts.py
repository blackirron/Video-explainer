"""
Turns a scene's narration text into actual narrated audio (MP3), server-side.

Why server-side instead of the browser's built-in speechSynthesis:
- Voice quality/availability is wildly inconsistent across OS/browser, and
  there's no reliable way to guarantee a specific voice character (e.g.
  "friendly adult male") since speechSynthesis just exposes whatever voices
  happen to be installed on the user's device.
- edge-tts uses Microsoft Edge's neural TTS service. It's free, needs no API
  key, and produces genuinely natural-sounding audio with a voice we can
  actually pin down and control consistently across every user/browser.

Trade-off worth knowing: this is a reverse-engineered, unofficial use of
Microsoft's service (there's no public API contract), so it can break if
Microsoft changes something upstream. That's an acceptable trade for a free
tier with no key; if it ever becomes unreliable in production, swapping in a
paid TTS provider (OpenAI, ElevenLabs, Azure Speech proper) is a drop-in
replacement for just this one file.
"""

import base64

import edge_tts

# A single fixed voice/style across every scene - same reasoning as the SVG
# palette: a video where every scene sounds like a different narrator is
# jarring, even if each individual clip sounds fine on its own.
VOICE = "en-US-AndrewNeural"  # natural, friendly adult male, good for narration
RATE = "-5%"  # slightly slower than default -> easier for students to follow


async def generate_narration_audio(text: str) -> str:
    """
    text: the scene's narration string.

    Returns: base64-encoded MP3 audio (as a plain string), ready to embed
    directly in a JSON response and play from a data: URL on the frontend.

    Raises RuntimeError on failure. Unlike the SVG illustrator, there's no
    honest silent fallback for "the audio didn't generate" - a placeholder
    beep or silence would be a worse experience than a clear error, so we
    let the caller decide how to surface it (e.g. falling back to
    browser TTS, or failing the whole request).
    """
    text = text.strip()
    if not text:
        raise RuntimeError("Cannot generate narration for empty text")

    try:
        communicate = edge_tts.Communicate(text=text, voice=VOICE, rate=RATE)
        chunks = bytearray()
        async for message in communicate.stream():
            if message["type"] == "audio":
                chunks.extend(message["data"])
    except Exception as e:
        raise RuntimeError(f"Narration audio generation failed: {e}") from e

    if not chunks:
        raise RuntimeError("Narration audio generation returned no audio data")

    return base64.b64encode(bytes(chunks)).decode("ascii")
