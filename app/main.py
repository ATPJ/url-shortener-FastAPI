from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db

app = FastAPI(title="URL Shorter")

@app.get("/health")
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as E:
        print(E)
        raise HTTPException(status_code=503, detail="Something went wrong!")

    return {'health': "ok!"}
