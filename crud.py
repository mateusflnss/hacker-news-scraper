from sqlmodel import Session, select
from model import Story
from sqlalchemy import func



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



def add_stories_batch(session: Session, data):
    for item in data:
        story = Story(
            hn_id=int(item["hn_id"]),
            title=item["title"],
            url=item["link"],
            domain=item["domain"],
            points=int(item["points"]),
            author=item["author"],
            age=item["age"],
            comments_link=item["comments_link"],
            comments_text=item["comments_text"],
            comments_amount=int(item["comments_amount"]),
            scraped_at=item["scraped_at"]
        )
        added_story = add_story(session, story)


def get_stories(session:Session, domain: str | None = None,
                 min_points: int | None = None,
                 limit: int = 50, offset: int = 0) -> list[Story]:
    query = select(Story)
    if domain:
        query = query.where(Story.domain == domain)
    if min_points:
        query = query.where(Story.points >= min_points)
    return session.exec(query.offset(offset).limit(limit)).all()


def get_story_by_id(session:Session, id: int) -> Story:
    return session.get(Story, id)   # PK lookup, returns Story | None
    

def get_story_by_hn_id(session:Session, id: int) -> list[Story]:
    query = select(Story)
    query = query.where(Story.hn_id == id)
    return session.exec(query).first()


def fetch_distinct_domains(
    session: Session,
    limit: int,
    offset: int):
    query = select(Story.domain)
    query = query.distinct()
    query = query.limit(limit).offset(offset)
    return session.exec(query).all()

def fetch_top_domains(
    session: Session,
    limit: int,
    offset: int):
    query = (select(Story.domain, func.count(Story.domain))
    .group_by(Story.domain)
    .order_by(func.count(Story.domain).desc())
    .limit(limit)
    .offset(offset)
    )

    results = session.exec(query).all()
    return [{"domain": domain, "count": count} for domain, count in results]