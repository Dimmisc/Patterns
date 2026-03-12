from db import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

engine = create_engine("sqlite:///site.db", echo=False)

Base.metadata.create_all(engine)

SessionLocal = sessionmaker(bind=engine)


def get_session() -> Session:
    return SessionLocal()
