from datetime import datetime
from sqlmodel import Session
from fastapi.testclient import TestClient
from datetime import datetime
from model import Story

def test_get_story_success(session:Session, client: TestClient):
    story = Story(
        hn_id=111,
        title="HN test",
        url="https://example.com",
        domain="example.com",
        points=42,
        author="mateus",
        age="2 hours ago",
        comments_link="https://example.com/comments",
        comments_text="10 comments",
        comments_amount=10,
        scraped_at=datetime.utcnow(),

    )
    session.add(story)
    session.commit()
    session.refresh(story)

    response = client.get(f"/stories/{story.id}")

    assert response.status_code == 200

    data = response.json()
    assert data["title"] == "HN test"
    assert data["points"] == 42
    assert data["hn_id"] == 111


def test_get_story_not_found(client: TestClient):
    response = client.get(f"/stories/12")

    assert response.status_code == 404

    assert "no story with id 12" in response.json()["detail"]