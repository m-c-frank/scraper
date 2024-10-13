from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime
import pytz

Base = declarative_base()

def local_now():
    return datetime.datetime.now(pytz.timezone('Europe/Berlin'))

class Item(Base):
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True)
    title = Column(Text, nullable=False)
    location = Column(Text, nullable=False)
    distance = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False)
    image = Column(Text)
    link = Column(Text, unique=True, nullable=False)
    created_at = Column(DateTime, default=local_now)

    description = relationship("Description", uselist=False, back_populates="item")
    # Other relationships can be added here

class Description(Base):
    __tablename__ = 'descriptions'

    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey('items.id'), unique=True, nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=local_now)

    item = relationship("Item", back_populates="description")

class ServiceProcessed(Base):
    __tablename__ = 'services_processed'
    __table_args__ = (UniqueConstraint('item_id', 'service_name', name='_item_service_uc'),)

    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey('items.id'), nullable=False)
    service_name = Column(String, nullable=False)
    processed_at = Column(DateTime, default=local_now)