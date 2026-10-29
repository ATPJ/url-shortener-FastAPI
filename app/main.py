from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import models  # noqa: F401
from app.database import Base, engine, get_db
from app.routers import links

Base.metadata.create_all(bind=engine)

app = FastAPI(title="URL Shortener")


@app.get("/health")
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Something went wrong!")

    return {"status": "ok"}


app.include_router(links.router)
