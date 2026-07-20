import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import narration_tts, scene_illustrator, script_generator

router = APIRouter(prefix="/explainer", tags=["explainer"])


class ExplainerRequest(BaseModel):
    concept: str = Field(min_length=3, max_length=300)
    context: str = Field(default="", max_length=300)


class Scene(BaseModel):
    scene_number: int
    narration: str
    svg: str
    duration_estimate_seconds: float
    # None when server-side narration failed for this scene specifically -
    # the frontend falls back to browser speechSynthesis just for that
    # scene rather than failing the whole video over one bad TTS call.
    audio_base64: str | None = None


class ExplainerResponse(BaseModel):
    title: str
    total_estimated_seconds: float
    scenes: list[Scene]


@router.post("/generate", response_model=ExplainerResponse)
async def generate_explainer(payload: ExplainerRequest) -> ExplainerResponse:
    api_key = settings.groq_api_key

    try:
        script = await script_generator.generate_script(
            concept=payload.concept, context=payload.context, groq_api_key=api_key
        )
    except RuntimeError as e:
        # A broken script is a real failure worth surfacing clearly to the user,
        # not something to paper over with a fallback - there's no honest
        # placeholder for "the educational content of the entire video."
        raise HTTPException(status_code=502, detail=f"Couldn't generate a script: {e}")

    # Illustrate + narrate every scene concurrently, and across both
    # services at once (not just within each) - directly matters for how
    # long a student waits looking at a loading spinner.
    svgs, audios = await asyncio.gather(
        asyncio.gather(*[
            scene_illustrator.generate_scene_svg(scene["visual_description"], groq_api_key=api_key)
            for scene in script["scenes"]
        ]),
        # return_exceptions: one scene's narration failing shouldn't sink the
        # whole video - that scene just falls back to browser TTS instead.
        asyncio.gather(*[
            narration_tts.generate_narration_audio(scene["narration"])
            for scene in script["scenes"]
        ], return_exceptions=True),
    )

    scenes = [
        Scene(
            scene_number=scene["scene_number"],
            narration=scene["narration"],
            svg=svg,
            duration_estimate_seconds=scene["duration_estimate_seconds"],
            audio_base64=None if isinstance(audio, Exception) else audio,
        )
        for scene, svg, audio in zip(script["scenes"], svgs, audios)
    ]

    return ExplainerResponse(
        title=script["title"],
        total_estimated_seconds=script["total_estimated_seconds"],
        scenes=scenes,
    )
