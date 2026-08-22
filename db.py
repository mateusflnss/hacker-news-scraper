from sqlmodel import SQLModel, create_engine, Session
import os

DATABASE_URL = os.getenv("DATABASE_URL", "")

if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
else:
     engine = create_engine("sqlite:///hn.db")
    
def init_db() -> None:
    """
    Initializes the database by creating all tables defined in the SQLModel metadata.
    """
    SQLModel.metadata.create_all(engine)

def get_session() -> Session:
    
    """
    Returns a new database session.
    """
    with Session(engine) as session:
        yield session