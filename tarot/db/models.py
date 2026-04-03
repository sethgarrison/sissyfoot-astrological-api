"""Tarot SQLAlchemy models. JSON columns match the spec’s multilingual objects."""

from sqlalchemy import Boolean, Column, Integer, JSON, String

from core.db.base import Base


class Card(Base):
    __tablename__ = "cards"

    name_short = Column(String(64), primary_key=True)
    name = Column(JSON, nullable=False)
    value = Column(JSON, nullable=False)
    meaning_up = Column(JSON, nullable=False)
    meaning_rev = Column(JSON, nullable=False)
    description = Column(JSON, nullable=False)
    suit = Column(JSON, nullable=True)
    type_ = Column("type", String(10), nullable=False)  # major | minor
    value_int = Column(Integer, nullable=False, index=True)
    image_path = Column(String(512), nullable=True)


class Tutorial(Base):
    __tablename__ = "tutorials"

    section_key = Column(String(128), primary_key=True)
    title = Column(JSON, nullable=False)
    content = Column(JSON, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    order_index = Column(Integer, nullable=False, default=0, index=True)
