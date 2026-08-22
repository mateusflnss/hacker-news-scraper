from crud import (add_story, add_stories_batch, get_stories,
                   get_story_by_id, get_story_by_hn_id, fetch_distinct_domains, fetch_top_domains)
from db import engine, init_db, get_session
from schemas import StoryCreate
from model import Story
from sqlmodel import Session, select
from fastapi import FastAPI, Depends, Query, HTTPException
from sqlalchemy import func
import os
from dotenv import load_dotenv
from fastapi.security import APIKeyHeader

init_db()


app = FastAPI(title="Hacker News Data Pipeline API",
    description="REST API for accessing scraped Hacker News stories. Supports filtering, pagination, and batch insertion.",
    version="1.0.0"
)

load_dotenv()
API_SECRET_KEY = os.getenv("API_KEY")
api_key_header = APIKeyHeader(name="X_API_Key", auto_error=False)

async def verify_api_key(api_key: str = Depends(api_key_header)):
    if not api_key or api_key != API_SECRET_KEY:
        raise HTTPException(status_code=403, detail="invalid or missing API Key")
    return True


@app.get("/stories/")
def list_stories(
    session: Session = Depends(get_session),
    domain: str | None = None,
    min_points: int | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
) -> list[Story]:
    """
    list stories from the Hacker News database.

    Supports filtering by domain and minimum points, with pagination controlls
    
    Args:
        session: SQLAlchemy session dependency.
        domain: Filter results to stories from this exact domain (e.g., "github.com").
        min_points: Minimum points threshold; only stories with points >= this value are returned.
        limit: Maximum number of items to return (max: 200, default: 50).
        offset: Number of items to skip for pagination.
        
    Returns:
        A list of Story objects matching the filters.

    """
    return get_stories(session, domain, min_points, limit, offset)
    

@app.get("/stories/{story_id}")
def get_story(story_id: int , session: Session = Depends(get_session)):
    """
    get a story from the hackernews database based off its database ID.
    
    Args:
        story_id: Story database ID
        session: SQLAlchemy session dependency.
        
    Returns:
        The story with corresponding ID.

    Raises:
        404 not found: If no story exists with provided ID

    """
    item = get_story_by_id(session, story_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"no story with id {story_id}")
    return item



@app.get("/stories/by-hn-id/{hn_id}")
def get_story_hn(hn_id: int,
              session: Session = Depends(get_session),
              ):
    """
    get a story from the hackernews database based off its hackernews ID.
    
    Args:
        hn_id: Story database ID
        session: SQLAlchemy session dependency.
        
    Returns:
        The story with corresponding hackernews ID.

    Raises:
        404 not found: If no story exists with provided hackernews ID
    
        """
    item = get_story_by_hn_id(session, hn_id)
    if item == None:
        raise HTTPException(status_code = 404, detail={"message" : f"no item with {hn_id} id"})

    return item


@app.get("/domains")
def get_domains(
    session: Session = Depends(get_session),
    limit: int = Query(default=50, le=200),
    offset: int = 0,) -> list[str]:
    """
    gets all distinct domains from the hackernews database.
    
    Args:
        session: SQLAlchemy session dependency.
        limit: Maximum number of items to return (max: 200, default: 50).
        offset: Number of items to skip for pagination.
        
    Returns:
        A list of domains up to the limit amount.
    
    """
    return fetch_distinct_domains(session, limit, offset)



@app.get("/top-domains")
def get_top_domains(
    session: Session = Depends(get_session),
    limit: int = Query(default=50, le=200),
    offset: int = 0,) -> list[str]:
    """
    gets all distinct domains from the hackernews database ordered by how often they appear.
    
    Args:
        session: SQLAlchemy session dependency.
        limit: Maximum number of items to return (max: 200, default: 50).
        offset: Number of items to skip for pagination.
        
    Returns:
        A list of domains up to the limit amount.
    
    """
    return fetch_top_domains(session, limit, offset)




@app.post("/stories/batch")
async def post_stories(stories: list[StoryCreate], session: Session = Depends(get_session), _: bool = Depends(verify_api_key)):
    """
    Add multiple stories to the database in a single batch request.

    Each story in the list is validated and inserted individually.
    If one story fails (e.g., due to a duplicate), the others are still processed.
    
    Args:
        stories: list of StoryCreate object with stories to be added.
        session: SQLAlchemy session dependency.
        
        Returns:
        A dictionary containing the following keys:
            - total: Total number of stories received in the request.
            - added: Number of stories successfully added to the database.
            - skipped: Number of stories that were not added (e.g., duplicates).
            - errors: List of error messages for skipped items (empty list if none).
    
    """
    
    return add_stories_batch(session, [s.model_dump() for s in stories])