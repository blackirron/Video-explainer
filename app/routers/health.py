"""
Health check endpoint.

Why: Render/Railway/Fly.io periodically ping a URL to check your app
didn't crash. Without this, deploys can be marked unhealthy and get
restarted or killed even if your app is actually fine.

Also just useful for you to quickly check "is my deployed app up?"
by visiting /health in the browser.
"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    return {"status": "ok"}
