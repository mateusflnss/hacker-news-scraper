from crud import add_story
from db import engine, init_db, get_session
from model import Story
from sqlmodel import Session, select
from fastapi import FastAPI, Depends, Query


init_db()

app = FastAPI()


@app.get("/stories")
def list_stories(
    session: Session = Depends(get_session),
    domain: str | None = None,
    min_points: int | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
):
    query = select(Story)
    if domain:
        query = query.where(Story.domain == domain)
    if min_points:
        query = query.where(Story.points >= min_points)

    query = query.offset(offset).limit(limit)

    return session.exec(query).all()