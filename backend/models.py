from sqlalchemy import Column, Integer, String
from backend.database import Base

class FileMetadata(Base):
    __tablename__ = 'files'
    id = Column(Integer, primary_key=True)
    access_id = Column(String, unique=True, nullable=False)
    username = Column(String, index=True, nullable=False)
    filename = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    password_hash = Column(String, nullable=False)
    upload_date = Column(String, nullable=False)
