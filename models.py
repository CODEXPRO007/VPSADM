from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from database import Base

class Paste(Base):
    __tablename__ = "pastes"

    id = Column(Integer, primary_key=True)
    paste_id = Column(String(8), unique=True)
    content = Column(Text)
    language = Column(String(20))
    password = Column(String(100), nullable=True)
    expire_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)