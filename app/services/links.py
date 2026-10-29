import logging
import secrets
import string
from datetime import datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Link, utc_now

ALPHABET = string.ascii_letters + string.digits
CODE_LENGTH = 8
MAX_RETRIES = 5

logger = logging.getLogger(__name__)


class ShortCodeGenerationError(Exception):
    """Failed for max retries"""


class LinkNotFoundError(Exception):
    """No link with this short code."""


class LinkExpiredError(Exception):
    """The link exists but has expired."""


def generate_short_code() -> str:
    the_code = ""
    for _ in range(CODE_LENGTH):
        the_code += secrets.choice(ALPHABET)

    return the_code


def create_link(db: Session, original_url: str) -> Link:
    settings = get_settings()
    expires_at: datetime = utc_now() + timedelta(days=settings.LINK_TTL_DAYS)

    for _ in range(MAX_RETRIES):
        link = Link(
            original_url=original_url,
            short_code=generate_short_code(),
            expires_at=expires_at,
        )
        db.add(link)

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            continue

        db.refresh(link)
        return link

    logger.error("Short code generation failed after %d retries.", MAX_RETRIES)
    raise ShortCodeGenerationError()


def get_link(db: Session, code: str) -> Link:
    link = db.scalar(select(Link).where(Link.short_code == code))
    if link is None:
        raise LinkNotFoundError
    return link


def resolve_link(db: Session, code: str) -> str:
    link = get_link(db, code)

    if link.expires_at <= utc_now():
        raise LinkExpiredError

    url = link.original_url

    db.execute(
        update(Link).where(Link.id == link.id).values(click_count=Link.click_count + 1)
    )
    db.commit()

    return url
