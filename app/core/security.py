"""
Minimal auth stub.

Why: most of your 20+ small apps don't need real user accounts/login.
But you DO need to stop a random stranger from hitting your deployed
endpoint in a loop and burning through your Claude API credits.

This does that with one shared secret header: `X-API-Token`.

How to use it in a router:

    from fastapi import Depends
    from app.core.security import verify_token

    @router.post("/chat")
    def chat(payload: ChatRequest, _: None = Depends(verify_token)):
        ...

If an app genuinely needs per-user login later (e.g. Officeboard AI,
club websites with admin panels), swap this file for real JWT auth —
everything else in the template stays the same.
"""

from fastapi import Header, HTTPException, status

from app.core.config import settings


def verify_token(x_api_token: str = Header(default="")) -> None:
    if settings.environment == "development":
        # Don't force you to send headers while building locally
        return
    if x_api_token != settings.api_auth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Token header",
        )
