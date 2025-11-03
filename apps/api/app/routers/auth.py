from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import User
from app.db.session import get_session
from app.schemas import GuestSession

router = APIRouter()


@router.post("/auth/guest", response_model=GuestSession, status_code=status.HTTP_201_CREATED)
def create_guest(session: Session = Depends(get_session)) -> GuestSession:
    token = uuid4().hex
    user = User(session_token=token)
    session.add(user)
    session.flush()
    session.refresh(user)
    return GuestSession(session_token=token)


@router.delete("/auth/sessions/{token}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_session(token: str, session: Session = Depends(get_session)) -> None:
    user = session.scalars(select(User).where(User.session_token == token)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    session.delete(user)
