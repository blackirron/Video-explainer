import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import scene_illustrator, script_generator

router = APIRouter(prefix="/explainer", tags=["explainer"])


class ExplainerRequest(BaseModel):
    concept: str = Field(min_length=3, max_length=300)
    context: str = Field(default="", max_length=300)


class Scene(BaseModel):
    scene_number: int
    narration: str
    svg: str
    duration_estimate_seconds: float


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

    # Illustrate all scenes concurrently rather than one-by-one - directly
    # matters for how long a student waits looking at a loading spinner.
    svgs = await asyncio.gather(*[
        scene_illustrator.generate_scene_svg(scene["visual_description"], groq_api_key=api_key)
        for scene in script["scenes"]
    ])

    scenes = [
        Scene(
            scene_number=scene["scene_number"],
            narration=scene["narration"],
            svg=svg,
            duration_estimate_seconds=scene["duration_estimate_seconds"],
        )
        for scene, svg in zip(script["scenes"], svgs)
    ]

    return ExplainerResponse(
        title=script["title"],
        total_estimated_seconds=script["total_estimated_seconds"],
        scenes=scenes,
    )
