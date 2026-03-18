from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Planet(Base):
    __tablename__ = "planets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    symbol = Column(String(10), nullable=True)
    description = Column(Text, nullable=True)
    keywords = Column(String(255), nullable=True)


class Sign(Base):
    __tablename__ = "signs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    element = Column(String(20), nullable=True)  # fire, earth, air, water
    modality = Column(String(20), nullable=True)  # cardinal, fixed, mutable
    archetypes_balanced = Column(String(200), nullable=True)
    archetypes_unbalanced = Column(String(200), nullable=True)
    journey = Column(String(100), nullable=True)
    gifts = Column(Text, nullable=True)
    challenges = Column(Text, nullable=True)
    interpretation = Column(Text, nullable=True)


class House(Base):
    __tablename__ = "houses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    number = Column(Integer, unique=True, nullable=False)  # 1-12
    type_ = Column(String(20), nullable=True)  # angular, succedent, cadent
    description = Column(Text, nullable=True)
    subtitle = Column(String(100), nullable=True)
    keywords = Column(String(255), nullable=True)


class Aspect(Base):
    __tablename__ = "aspects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    angle_degrees = Column(Integer, nullable=True)
    symbol = Column(String(10), nullable=True)


class PlanetSignInterpretation(Base):
    __tablename__ = "planet_sign_interpretations"
    __table_args__ = (UniqueConstraint("planet_id", "sign_id", name="uq_planet_sign"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    planet_id = Column(Integer, ForeignKey("planets.id"), nullable=False)
    sign_id = Column(Integer, ForeignKey("signs.id"), nullable=False)
    interpretation_text = Column(Text, nullable=False)
    interpretation_long = Column(Text, nullable=True)
    interpretation_short = Column(Text, nullable=True)
    keywords = Column(String(500), nullable=True)
    retrograde_interpretation = Column(Text, nullable=True)  # meaning when planet is retrograde in this sign


class PlanetHouseInterpretation(Base):
    __tablename__ = "planet_house_interpretations"
    __table_args__ = (UniqueConstraint("planet_id", "house_id", name="uq_planet_house"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    planet_id = Column(Integer, ForeignKey("planets.id"), nullable=False)
    house_id = Column(Integer, ForeignKey("houses.id"), nullable=False)
    interpretation_text = Column(Text, nullable=False)
    short_interpretation = Column(Text, nullable=True)
    retrograde_interpretation = Column(Text, nullable=True)  # meaning when planet is retrograde in this house


class AspectInterpretation(Base):
    __tablename__ = "aspect_interpretations"
    __table_args__ = (UniqueConstraint("aspect_id", name="uq_aspect_interpretation"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    aspect_id = Column(Integer, ForeignKey("aspects.id"), nullable=False)
    interpretation_text = Column(Text, nullable=False)


class PlanetAspectInterpretation(Base):
    """Planet-pair specific aspect interpretations (e.g. Sun conjunct Moon). From aspect_interpretations.csv."""
    __tablename__ = "planet_aspect_interpretations"
    __table_args__ = (
        UniqueConstraint("planet_1_id", "planet_2_id", "aspect_id", name="uq_planet_aspect"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    planet_1_id = Column(Integer, ForeignKey("planets.id"), nullable=False)
    planet_2_id = Column(Integer, ForeignKey("planets.id"), nullable=False)
    aspect_id = Column(Integer, ForeignKey("aspects.id"), nullable=False)
    interpretation_text = Column(Text, nullable=False)


class ChartShapeInterpretation(Base):
    __tablename__ = "chart_shape_interpretations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    shape_key = Column(String(50), unique=True, nullable=False)
    interpretation_text = Column(Text, nullable=False)


class SignHouseInterpretation(Base):
    """
    Interpretation for a sign on a house cusp (e.g. Aries on 1st house = Aries Rising).
    house + sign uniquely identifies the combination.
    """
    __tablename__ = "sign_house_interpretations"
    __table_args__ = (UniqueConstraint("house_id", "sign_id", name="uq_sign_house"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    house_id = Column(Integer, ForeignKey("houses.id"), nullable=False)
    sign_id = Column(Integer, ForeignKey("signs.id"), nullable=False)
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
