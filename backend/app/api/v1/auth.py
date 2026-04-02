"""Auth API — current user info and logout."""

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/me")
async def get_current_user(request: Request) -> dict:
    """Get current user info from session."""
    user = request.session.get("user")
    if not user:
        return {"authenticated": False, "user": None}
    return {"authenticated": True, "user": user}


@router.post("/logout")
async def logout(request: Request) -> dict:
    """Clear session."""
    request.session.clear()
    return {"ok": True}
