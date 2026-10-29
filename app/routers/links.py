from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.schemas import AnalyticsResponse, LinkCreate, LinkResponse
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


@router.get("/analytics/{code}", response_model=AnalyticsResponse)
def analytics(code: str, db: Session = Depends(get_db)) -> AnalyticsResponse:
    try:
        link = links_service.get_link(db, code)
    except links_service.LinkNotFoundError:
        raise HTTPException(status_code=404, detail="Link not found")

    return AnalyticsResponse(
        short_code=link.short_code,
        original_url=link.original_url,
        click_count=link.click_count,
        created_at=link.created_at,
        expires_at=link.expires_at,
    )


@router.get("/{code}")
def redirect(code: str, db: Session = Depends(get_db)) -> RedirectResponse:
    try:
        url = links_service.resolve_link(db, code)
    except links_service.LinkNotFoundError:
        raise HTTPException(status_code=404, detail="Link not found")
    except links_service.LinkExpiredError:
        raise HTTPException(status_code=410, detail="Link expired")

    return RedirectResponse(url, status_code=302)
