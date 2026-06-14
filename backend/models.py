from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String

from backend.database import Base


class FileMetadata(Base):

    __tablename__ = "files"
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    access_id = Column(
        String,
        unique=True
    )

    filename = Column(
        String
    )

    mime_type = Column(
        String
    )

    drive_file_id = Column(
        String
    )
    password_hash = Column(String)

    upload_date = Column(
        String
    )