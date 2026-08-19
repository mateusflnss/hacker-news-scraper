from sqlmodel import Session, select
from model import Story

def add_story(session: Session, story: Story):
    try:
        session.add(story)
        session.commit()
        session.refresh(story)
    except Exception as e:
        session.rollback()
        print(f"add_story failed for hn_id={story.hn_id}: {type(e).__name__}: {e}")
        return None
    return story

def get_stories(session:Session, domain: str | None = None,
                 min_points: int | None = None,
                 limit: int = 50, offset: int = 0) -> list[Story]:
    query = select(Story)
    if domain:
        query = query.where(Story.domain == domain)
    if min_points:
        query = query.where(Story.points >= min_points)
    return session.exec(query.offset(offset).limit(limit)).all()