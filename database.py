from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

DATABASE_URL = "postgresql://postgres.izvwnaeazzytqxtesobl:C6Bk6PSVJJ$mmRz@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"
Base = declarative_base()

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class AudioMessage(Base):
    __tablename__ = "audio_messages"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
