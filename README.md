# App Template (FastAPI + Claude API)

Base template for the 10-day sprint. Fork/copy this folder for every new app,
then edit this README's top section for that specific app.

---

# Lumen — AI Video Explainer

Forked from the sprint's base FastAPI template.

---

## Lumen

**What it does:** enter any school concept (+ optional grade level/angle),
get back a short narrated, animated explainer — a script broken into
4-7 scenes, each with a flat-vector illustration and spoken narration,
playing directly in the browser.

**Honest scope note:** this produces clean flat-vector illustrations in
the same visual *family* as TED-Ed (warm palette, simple shapes,
metaphor-driven), not a reproduction of TED-Ed's actual bespoke
hand-drawn animation — that's not achievable through an automated
pipeline. Narration is generated server-side with `edge-tts` (Microsoft
Edge's free neural TTS, no API key, one consistent voice for every
student) and streamed to the browser as audio; if generation fails for
a specific scene, that scene alone falls back to the browser's built-in
`speechSynthesis` rather than losing narration for the whole video.

**Live demo:** [link once deployed]

## How it works

1. `script_generator.py` — concept + context → structured scene-by-scene
   script (LLM via Groq). Scene duration is computed from word count,
   not trusted from the model's own estimate.
2. `scene_illustrator.py` — each scene's visual description → actual SVG
   markup, styled from a fixed shared palette so all scenes look
   cohesive. Falls back to a plain labeled placeholder if generation
   fails, rather than breaking the whole video.
3. `narration_tts.py` — each scene's narration text → base64 MP3 audio,
   via `edge-tts`, one fixed voice across every scene. Raises on failure
   rather than faking silent/beep audio; the router treats a single
   scene's TTS failure as non-fatal.
4. `routers/explainer.py` — orchestrates all three, illustrating *and*
   narrating every scene concurrently (not one-by-one, and not
   sequentially between the two services) to keep wait time down.
5. Frontend — plays each scene's SVG with a fade transition, plays the
   server-generated MP3 (falling back to `speechSynthesis` per-scene if
   that scene's audio is missing), auto-advances when audio ends (with a
   timeout fallback in case an audio/speech event doesn't fire reliably).

## Possible next steps (not built yet)

- Server-side MP4 export (ffmpeg compositing scenes + audio) for
  downloading/sharing outside the browser — meaningfully heavier than
  the current in-browser player, treat as a separate phase.
- True mid-scene pause/resume for audio (currently "resume" replays the
  current scene from its start, which is simple but not frame-accurate).
- `edge-tts` is a free, unofficial (reverse-engineered) use of
  Microsoft's service — solid for a school project, but if it ever
  becomes unreliable in production, swapping in a paid TTS provider
  (Azure Speech proper, ElevenLabs, OpenAI) only touches
  `narration_tts.py`.


---

## Running locally

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up your environment variables
cp .env.example .env
# then edit .env and paste your real ANTHROPIC_API_KEY

# 4. Run the dev server (auto-reloads on code changes)
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` — FastAPI auto-generates an interactive
API tester here. This is the fastest way to try your endpoints without
building a frontend first.

## Running with Docker

```bash
docker build -t my-app .
docker run -p 8000:8000 --env-file .env my-app
```

## Project structure

```
app/
├── core/       config + auth
├── routers/    HTTP endpoints (thin — no logic)
├── services/   actual logic (Claude API calls, etc.)
└── main.py     wires it together
```

## Adding a new feature to this app

1. Create `app/services/your_feature.py` — the actual logic
2. Create `app/routers/your_feature.py` — request/response models + thin endpoint (copy `chat.py`'s pattern)
3. Register it in `app/main.py`: `app.include_router(your_feature.router)`

## Deployment

Deployed on: [Railway / Render / Fly.io — fill in]

Environment variables to set on the platform dashboard:
- `LLM_PROVIDER` (`groq` by default — free, no card required)
- `GROQ_API_KEY` (get one free at https://console.groq.com/keys)
- `API_AUTH_TOKEN`
- `ENVIRONMENT=production`
- `ALLOWED_ORIGINS` (your frontend's real URL)
