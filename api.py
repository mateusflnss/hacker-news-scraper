from crud import (add_story, add_stories_batch, get_stories,
                   get_story_by_id, get_story_by_hn_id, fetch_distinct_domains, fetch_top_domains)
from db import engine, init_db, get_session
from schemas import StoryCreate
from model import Story
from sqlmodel import Session, select
from fastapi import FastAPI, Depends, Query, HTTPException
from sqlalchemy import func


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
    return get_stories(session, domain, min_points, limit, offset)
    

@app.get("/stories/{story_id}")
def get_story(story_id: int,
              session: Session = Depends(get_session),
              ):
    item = get_story_by_id(session, story_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"no story with id {story_id}")
    return item



@app.get("/stories/by-hn-id/{hn_id}")
def get_story_hn(hn_id: int,
              session: Session = Depends(get_session),

              ):
    item = get_story_by_hn_id(session, hn_id)
    if item == None:
        raise HTTPException(status_code = 404, detail={"message" : f"no item with {hn_id} id"})

    return item


@app.get("/domains")
def get_domains(
    session: Session = Depends(get_session),
    limit: int = Query(default=50, le=200),
    offset: int = 0,):
    
    return fetch_distinct_domains(session, limit, offset)



@app.get("/top-domains")
def get_top_domains(
    session: Session = Depends(get_session),
    limit: int = Query(default=50, le=200),
    offset: int = 0,):

    return fetch_top_domains(session, limit, offset)




@app.post("/stories/batch")
def post_stories(stories: list[StoryCreate], session: Session = Depends(get_session)):
    return add_stories_batch(session, [s.model_dump() for s in stories])