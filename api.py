from crud import add_story
from db import engine, init_db, get_session
from model import Story
from sqlmodel import Session, select
from fastapi import FastAPI, Depends, Query, HTTPException


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


@app.get("/stories/{story_id}")
def get_story(story_id: int,
              session: Session = Depends(get_session),

              ):
    item = session.get(Story, story_id)   # PK lookup, returns Story | None
    if not item:
        raise HTTPException(status_code=404, detail=f"no story with id {story_id}")
    return item



@app.get("/stories/by-hn-id/{hn_id}")
def get_story_hn(hn_id: int,
              session: Session = Depends(get_session),

              ):
    query = select(Story)
    query = query.where(Story.hn_id == hn_id)
    item = session.exec(query).first()
    if item == None:
        raise HTTPException(status_code = 404, detail={"message" : f"no item with {hn_id} id"})

    return item


@app.get("/domains")
def get_domains(
    session: Session = Depends(get_session),
    limit: int = Query(default=50, le=200),
    offset: int = 0,):
    query = select(Story.domain)
    query = query.distinct()
    query = query.limit(limit).offset(offset)
    return session.exec(query).all()
