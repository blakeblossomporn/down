from sqlalchemy import Column, Integer, String, Boolean, DateTime
from utils.db import Base


class Torrent(Base):
    __tablename__ = 'torrents'

    id = Column(Integer, primary_key=True, index=True)
    torrent_id = Column(String(100), unique=True)
    release_name = Column(String(350), nullable=True)
    is_downloaded = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=True)

