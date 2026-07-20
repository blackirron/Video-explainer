"""
Turns a scene's visual_description into actual SVG markup.

This is the piece that stands in for "the animation" - since true bespoke
hand-drawn animation isn't achievable through an automated pipeline, we
generate clean flat-vector illustrations instead: simple shapes, a fixed
muted color palette, minimal detail. Same visual FAMILY as TED-Ed (flat,
uncluttered, metaphor-driven), not a forgery of its actual hand-drawn art.

Consistency matters more than any single scene's quality here - a script
where every scene uses a wildly different palette/style looks broken even
if each individual SVG is fine. So the style guide (colors, canvas size,
allowed elements) is fixed and injected into every single generation call.
"""

import os
import re

import httpx

GROQ_BASE_URL = os.environ.get("GROQ_BASE_URL_OVERRIDE", "https://api.groq.com/openai/v1")
GROQ_MODEL = "llama-3.3-70b-versatile"

# Fixed across every scene so the whole video looks like one coherent thing,
# not five illustrations that happen to be in the same file.
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 450
PALETTE = {
    "background": "#FBF6EC",  # warm cream, close to TED-Ed's actual background
    "ink": "#2B2B2B",
    "accent_1": "#D9614E",  # muted terracotta red
    "accent_2": "#3F6B8C",  # muted blue
    "accent_3": "#5B8A5A",  # muted green
    "accent_4": "#E8B04B",  # muted gold
}

SYSTEM_PROMPT = f"""You draw simple, clean flat-vector educational illustrations as raw SVG markup.

Canvas: viewBox="0 0 {CANVAS_WIDTH} {CANVAS_HEIGHT}"
Color palette - use ONLY these colors, nothing else:
  background: {PALETTE['background']}
  ink (outlines/text): {PALETTE['ink']}
  accent 1: {PALETTE['accent_1']}
  accent 2: {PALETTE['accent_2']}
  accent 3: {PALETTE['accent_3']}
  accent 4: {PALETTE['accent_4']}

Style rules:
- Flat shapes only: circles, rects, paths, polygons. No gradients, no photorealism, no filters.
- Simple geometric/iconographic style - think clean textbook diagram, not detailed illustration.
- Always fill the full canvas with the background color first.
- Use <text> elements sparingly, only for actual labels the visual needs (not captions - narration
  is spoken separately).
- Give each meaningful group of shapes a class name (e.g. class="leaf-group") so it CAN be targeted
  by CSS animation later, even though you're not writing animation yourself.

Respond with ONLY the raw <svg>...</svg> markup. No markdown fences, no explanation, no other text.
"""


def _extract_svg(raw: str) -> str:
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:svg|xml|html)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    match = re.search(r"<svg.*?</svg>", cleaned, re.DOTALL)
    if not match:
        raise ValueError("No <svg>...</svg> found in model response")
    return match.group(0)


def _placeholder_svg(text: str) -> str:
    """Fail-safe: a plain labeled placeholder rather than a broken/missing scene."""
    safe_text = text[:60].replace("&", "and").replace("<", "").replace(">", "")
    return (
        f'<svg viewBox="0 0 {CANVAS_WIDTH} {CANVAS_HEIGHT}" xmlns="http://www.w3.org/2000/svg">'
        f'<rect width="{CANVAS_WIDTH}" height="{CANVAS_HEIGHT}" fill="{PALETTE["background"]}"/>'
        f'<text x="{CANVAS_WIDTH/2}" y="{CANVAS_HEIGHT/2}" text-anchor="middle" '
        f'fill="{PALETTE["ink"]}" font-size="20" font-family="sans-serif">{safe_text}</text>'
        f'</svg>'
    )


async def generate_scene_svg(visual_description: str, groq_api_key: str = "") -> str:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GROQ_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {groq_api_key}"},
                json={
                    "model": GROQ_MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": visual_description},
                    ],
                    "max_tokens": 2000,
                },
                timeout=45.0,
            )
        response.raise_for_status()
        raw_text = response.json()["choices"][0]["message"]["content"]
        return _extract_svg(raw_text)
    except Exception:
        return _placeholder_svg(visual_description)
