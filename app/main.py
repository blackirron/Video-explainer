"""
Entrypoint. This is what actually runs when you (or Docker) start the app.

When you build a new app from this template:
1. Add a new router file in app/routers/ (copy chat.py's pattern)
2. Import it below and add one line: app.include_router(your_router.router)
That's it — no other file needs to change.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.routers import explainer, health

app = FastAPI(title=settings.app_name)

# CORS: lets your frontend (React/plain HTML on a different domain)
# actually call this backend. Without this, browsers block the request.
origins = (
    ["*"]
    if settings.allowed_origins == "*"
    else [o.strip() for o in settings.allowed_origins.split(",")]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Register routers here as you build new apps ---
app.include_router(health.router)
app.include_router(explainer.router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
def root():
    return FileResponse("app/static/index.html")
