import logging
import secrets
import string
from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Link, utc_now

ALPHABET = string.ascii_letters + string.digits
CODE_LENGTH = 8
MAX_RETRIES = 5

logger = logging.getLogger(__name__)


class ShortCodeGenerationError(Exception):
    """Failed for max retires"""


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
