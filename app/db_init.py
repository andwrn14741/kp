from models import Base, engine, SessionLocal, Car

def init_db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()

    if session.query(Car).count() == 0:
        sample = Car(
            avg_price_min=700,
            avg_price_max=800,
            brand="Ford",
            model="Escort",
            generation="V рестайлинг",
            body="Седан, хетчбек",
            engines="1.3-1.8 бензин",
            drive="Передний",
            car_class="C",
            years="1995-2000",
            country="Америка",
            weak_points="Электрика, подвеска",
            photo_filename=None
        )
        session.add(sample)
        session.commit()

    session.close()

if __name__ == "__main__":
    init_db()
    print("База инициализирована: cars.db")
