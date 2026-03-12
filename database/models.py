from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Planet(Base):
    __tablename__ = "planets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    symbol = Column(String(10), nullable=True)


class Sign(Base):
    __tablename__ = "signs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    element = Column(String(20), nullable=True)  # fire, earth, air, water
    modality = Column(String(20), nullable=True)  # cardinal, fixed, mutable


class House(Base):
    __tablename__ = "houses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    number = Column(Integer, unique=True, nullable=False)  # 1-12
    type_ = Column(String(20), nullable=True)  # angular, succedent, cadent


class Aspect(Base):
    __tablename__ = "aspects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    angle_degrees = Column(Integer, nullable=True)
    symbol = Column(String(10), nullable=True)


class PlanetSignInterpretation(Base):
    __tablename__ = "planet_sign_interpretations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    planet_id = Column(Integer, ForeignKey("planets.id"), nullable=False)
    sign_id = Column(Integer, ForeignKey("signs.id"), nullable=False)
    interpretation_text = Column(Text, nullable=False)
    retrograde_interpretation = Column(Text, nullable=True)  # meaning when planet is retrograde in this sign


class PlanetHouseInterpretation(Base):
    __tablename__ = "planet_house_interpretations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    planet_id = Column(Integer, ForeignKey("planets.id"), nullable=False)
    house_id = Column(Integer, ForeignKey("houses.id"), nullable=False)
    interpretation_text = Column(Text, nullable=False)
    retrograde_interpretation = Column(Text, nullable=True)  # meaning when planet is retrograde in this house


class AspectInterpretation(Base):
    __tablename__ = "aspect_interpretations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    aspect_id = Column(Integer, ForeignKey("aspects.id"), nullable=False)
    interpretation_text = Column(Text, nullable=False)


class ChartShapeInterpretation(Base):
    __tablename__ = "chart_shape_interpretations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    shape_key = Column(String(50), unique=True, nullable=False)
    interpretation_text = Column(Text, nullable=False)


class ChartDistributionInterpretation(Base):
    __tablename__ = "chart_distribution_interpretations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    distribution_key = Column(String(50), unique=True, nullable=False)
    interpretation_text = Column(Text, nullable=False)


class ModalityElementDistributionInterpretation(Base):
    """
    Interpretations for modality (cardinal, fixed, mutable) and element (fire, earth, air, water)
    distribution based on planetary placements in signs.

    Keys follow the pattern:
      element_<fire|earth|air|water>_dominant  - that element has the most planets
      element_balanced                        - no single element dominates
      element_lacking_<fire|earth|air|water>  - that element has 0 planets (optional)

      quality_<cardinal|fixed|mutable>_dominant - that modality has the most planets
      quality_balanced                          - no single modality dominates
    """
    __tablename__ = "modality_element_distribution_interpretations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    distribution_key = Column(String(50), unique=True, nullable=False)
    interpretation_text = Column(Text, nullable=False)


class Reading(Base):
    """Stored natal chart reading, keyed by name-birthdatetime-lat-lng."""
    __tablename__ = "readings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    identifier = Column(String(255), unique=True, nullable=False, index=True)
    chart_data = Column(Text, nullable=False)  # JSON string for SQLite compatibility
    created_at = Column(DateTime, default=datetime.utcnow)
