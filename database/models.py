from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship


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


class PlanetHouseInterpretation(Base):
    __tablename__ = "planet_house_interpretations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    planet_id = Column(Integer, ForeignKey("planets.id"), nullable=False)
    house_id = Column(Integer, ForeignKey("houses.id"), nullable=False)
    interpretation_text = Column(Text, nullable=False)


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
