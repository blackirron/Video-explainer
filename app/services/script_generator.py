"""
Turns a raw concept (+ optional context) into a structured, scene-by-scene
educational script - the foundation everything else in this pipeline builds on.

Design choices worth knowing:
- We ask the LLM for narration + a visual description per scene, but we
  compute each scene's DURATION ourselves from word count (average
  speaking pace ~150 words/minute) rather than trusting the model's own
  time estimates - LLMs are consistently unreliable at this kind of
  arithmetic, and duration accuracy directly affects playback sync later.
- Scene count is deliberately capped (4-7) - a school-explainer video
  that rambles across 15 scenes stops being a "quick concept explainer"
  and becomes something nobody finishes watching.
"""

import json
import os
import re

import httpx

GROQ_BASE_URL = os.environ.get("GROQ_BASE_URL_OVERRIDE", "https://api.groq.com/openai/v1")
GROQ_MODEL = "llama-3.3-70b-versatile"
WORDS_PER_SECOND = 2.5  # ~150 wpm, a natural, unhurried educational narration pace

SYSTEM_PROMPT = """You are a script writer for short educational explainer videos in the \
style of TED-Ed - clear, engaging, using concrete visual metaphors rather than dry definitions, \
building from a hook to a clear explanation to a memorable takeaway.

Given a concept (and optional context like grade level or a specific angle to focus on), \
write a script broken into 4-7 scenes. Each scene needs:
- narration: what's spoken during this scene (2-4 sentences, natural spoken language, not written prose)
- visual_description: a clear, concrete description of what should be illustrated - specific
  objects, characters, actions, and how they move or change. Simple flat-vector-illustration
  style, not photorealistic. Describe it precisely enough that an illustrator with no other
  context could draw it correctly.

Rules:
- Scene 1 must hook interest (a question, surprising fact, or relatable scenario) - not a definition
- Explain using concrete analogies a student would already understand, not just restating jargon
- Last scene should land on a clear, memorable takeaway
- Match the language complexity to the stated grade level (default to ages 12-16 if unspecified)
- Do NOT use markdown, headers, or stage directions - narration is spoken words only

Respond with ONLY a JSON object, no markdown fences, no other text:
{"title": "...", "scenes": [{"narration": "...", "visual_description": "..."}]}
"""


def _extract_json(raw: str) -> dict:
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return json.loads(cleaned)


def _estimate_duration(narration: str) -> float:
    word_count = len(narration.split())
    return round(word_count / WORDS_PER_SECOND, 1)


async def generate_script(concept: str, context: str = "", groq_api_key: str = "") -> dict:
    """
    concept: e.g. "how photosynthesis works"
    context: optional free text, e.g. "for 8th graders" or "focus on the chemical equation"

    Returns: {"title": ..., "scenes": [{"scene_number", "narration", "visual_description",
              "duration_estimate_seconds"}], "total_estimated_seconds": ...}

    Raises RuntimeError on failure - unlike the metadata generator, there's no safe
    generic fallback for "the entire educational content of the video," so callers
    should surface this as a real error rather than silently degrading.
    """
    user_message = concept if not context else f"{concept}\n\nAdditional context: {context}"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{GROQ_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {groq_api_key}"},
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                "max_tokens": 2000,
            },
            timeout=45.0,
        )
    response.raise_for_status()
    raw_text = response.json()["choices"][0]["message"]["content"]

    try:
        parsed = _extract_json(raw_text)
    except (json.JSONDecodeError, ValueError) as e:
        raise RuntimeError(f"Could not parse script from model response: {e}") from e

    scenes = []
    total_seconds = 0.0
    for i, scene in enumerate(parsed.get("scenes", []), start=1):
        narration = scene.get("narration", "").strip()
        duration = _estimate_duration(narration)
        total_seconds += duration
        scenes.append({
            "scene_number": i,
            "narration": narration,
            "visual_description": scene.get("visual_description", "").strip(),
            "duration_estimate_seconds": duration,
        })

    if not scenes:
        raise RuntimeError("Model returned no scenes")

    return {
        "title": parsed.get("title", concept)[:150],
        "scenes": scenes,
        "total_estimated_seconds": round(total_seconds, 1),
    }
