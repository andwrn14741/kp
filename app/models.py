from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

Base = declarative_base()

class Car(Base):
    __tablename__ = "cars"

    id = Column(Integer, primary_key=True)
    brand = Column(String)
    model = Column(String)
    generation = Column(String)
    body = Column(String)
    engines = Column(String)
    drive = Column(String)
    car_class = Column(String)
    years = Column(String)
    country = Column(String)
    weak_points = Column(String)
    photo_filename = Column(String)
    avg_price_min = Column(Integer)
    avg_price_max = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class ExternalCache(Base):
    __tablename__ = "external_cache"

    id = Column(Integer, primary_key=True)
    car_id = Column(Integer, ForeignKey("cars.id"))
    title = Column(String)
    price = Column(String)
    link = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

engine = create_engine("sqlite:///app/cars.db", echo=False)
SessionLocal = sessionmaker(bind=engine)
