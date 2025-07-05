from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()
engine = create_engine('sqlite:///milkie.db', echo=True)

from utils.models import Torrent

Base.metadata.create_all(engine)

