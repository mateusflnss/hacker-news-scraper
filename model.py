from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint, create_engine
from datetime import datetime

##title,link,domain,points,author,age,comments_link,comments_text,comments_amount

class Story(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("hn_id", "scraped_at"),)
    id: int = Field(default=None, primary_key=True)
    hn_id: int = Field(index=True)
    title: str
    url: str | None = None
    domain: str | None = Field(default=None, index=True)
    points: int
    author: str
    age: str   
    comments_link: str
    comments_text: str
    comments_amount: int
    scraped_at: datetime = Field(index=True)