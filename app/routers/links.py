from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.schemas import LinkCreate, LinkResponse
from app.services import links as links_service

router = APIRouter(tags=["links"])


@router.post(
    "/links",
    response_model=LinkResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_link(payload: LinkCreate, db: Session = Depends(get_db)) -> LinkResponse:
    try:
        link = links_service.create_link(db, str(payload.url))
    except links_service.ShortCodeGenerationError:
        raise HTTPException(
            status_code=503,
            detail="Could not generate a unique short code, please try again",
        )

    base = str(get_settings().BASE_URL).rstrip("/")
    return LinkResponse(
        short_code=link.short_code,
        short_url=f"{base}/{link.short_code}",
        original_url=link.original_url,
        expires_at=link.expires_at,
    )
