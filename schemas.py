from pydantic import BaseModel
from datetime import datetime


class StoryCreate(BaseModel):
    hn_id: int
    title: str
    url: str 
    domain: str 
    points: int
    author: str
    age: str   
    comments_link: str
    comments_text: str
    comments_amount: int
    scraped_at: datetime 

