from sqlmodel import Session, select
from model import Story
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError



def add_story(session: Session, story: Story) -> dict:
    """
    adds a single story to the database.
    
    Args:
        session: SQLAlchemy session dependency.
        story: Story object with the data to be added
        
    Returns:
        dictionary:
        
        - success (bool): True if added successfully, False otherwise.
        - story (Story): Story object added to the database.
        - error (str): Error message if addition fails.
    """

    try:

        session.add(story)
        session.commit()
        session.refresh(story)
        return {"success" : True, "story": story}
    
    except IntegrityError as e:

        session.rollback()
        return {"success" : False, "error" : "duplicate entry", "hn_id": story.hn_id}
    
    except Exception as e:

        session.rollback()
        return {"success" : False, "error" : str(e), "hn_id": story.hn_id}



def add_stories_batch(session: Session, stories: list[dict]) -> dict:
    """
    adds a multiple stories to the database.
    
    Args:
        session: SQLAlchemy session dependency.
        stories: list of stories objects to be added to the database
        
    Returns:
        dictionary:
        
        - total (int): Total amount of stories to be added to the database
        - total_added (int): Total amount of stories successfully added to the database
        - skipped (int): Amount of stories skipped due to errors
        - errors (dict):
            - hn_id (int): Hackernews ID of failed entry
            - error (str): Entry error

    """

    errors = []
    total_added = 0
    total_errors = 0

    for item in stories:
        story = Story(
            hn_id=int(item["hn_id"]),
            title=item["title"],
            url=item["url"],
            domain=item["domain"],
            points=int(item["points"]),
            author=item["author"],
            age=item["age"],
            comments_link=item["comments_link"],
            comments_text=item["comments_text"],
            comments_amount=int(item["comments_amount"]),
            scraped_at=item["scraped_at"]
        )
        result = add_story(session, story)
        
        if not result["success"]:
            total_errors += 1
            errors.append({"hn_id": result["hn_id"], "error": result["error"]})
        else:
            total_added += 1

    return {
        "total": len(stories),
        "total_added": total_added,
        "skipped" : total_errors,
        "errors" : errors
    }


def get_stories(session:Session, domain: str | None = None,
                 min_points: int | None = None,
                 limit: int = 50, offset: int = 0) -> list[Story]:
    """
    Gets stories from the database.
    
    Args:
        session: SQLAlchemy session dependency.
        domain: Filter results to stories from this exact domain (e.g., "github.com").
        min_points: Minimum points threshold; only stories with points >= this value are returned.
        limit: Maximum number of items to return (default: 50).
        offset: Number of items to skip.

    Returns:
        A list of stories matching the filters

    """

    query = select(Story)
    if domain:
        query = query.where(Story.domain == domain)

    if min_points:
        query = query.where(Story.points >= min_points)

    return session.exec(query.offset(offset).limit(limit)).all()


def get_story_by_id(session:Session, id: int) -> Story:
    """
    Gets a story from the database based on its ID.
    
    Args:
        session: SQLAlchemy session dependency.
        id: Story database ID

    Returns:
        A story matching the ID filter
    
    """
    return session.get(Story, id)   
    

def get_story_by_hn_id(session:Session, id: int) -> list[Story]:
    """
    Gets a story from the database based on its Hackernews ID.
    
    Args:
        session: SQLAlchemy session dependency.
        id: Story database Hackernews ID

    Returns:
        A story matching the Hackernews ID filter
        
    """
    query = select(Story)
    query = query.where(Story.hn_id == id)
    return session.exec(query).first()


def fetch_distinct_domains(
    session: Session,
    limit: int = 50,
    offset: int = 0) -> list[str]:
    """
    Gets distinct domains from the database.

    Starts from offset, up to limit
    
    Args:
        session: SQLAlchemy session dependency.
        limit: Maximum number of items to return (default: 50).
        offset: Number of items to skip.

    Returns:
        list[str]: All distinct domains up to limit.

    """

    query = select(Story.domain)
    query = query.distinct()
    query = query.limit(limit).offset(offset)
    return session.exec(query).all()


def fetch_top_domains(
    session: Session,
    limit: int = 50,
    offset: int = 0) -> list[str]:

    """
    Gets distinct domains from the database sorted by how many times they occur.

    Starts from offset, up to limit
    
    Args:
        session: SQLAlchemy session dependency.
        limit: Maximum number of items to return (default: 50).
        offset: Number of items to skip.

    Returns:
        list[str]: All distinct sorted domains.

    """
    query = (select(Story.domain, func.count(Story.domain))
    .group_by(Story.domain)
    .order_by(func.count(Story.domain).desc())
    .limit(limit)
    .offset(offset)
    )

    results = session.exec(query).all()
    return [{"domain": domain, "count": count} for domain, count in results]