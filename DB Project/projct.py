from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import Column, Integer, String, ForeignKey, Float, Date, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from pydantic import BaseModel
import random
import datetime

DATABASE_URL = "sqlite:///./formula1.db"  # Для простоты используем SQLite для локального тестирования

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Таблицы базы данных
class Stable(Base):
    __tablename__ = "stables"

    stable_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    country = Column(String, nullable=False)

class Pilot(Base):
    __tablename__ = "pilots"

    pilot_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    stable_id = Column(Integer, ForeignKey("stables.stable_id"))
    experience_years = Column(Integer, nullable=False)
    stable = relationship("Stable")
    additional_info = Column(String, nullable=True)  # JSON field for additional info

class Stage(Base):
    __tablename__ = "stages"

    stage_id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    location = Column(String, nullable=False)
    track_length_km = Column(Float, nullable=False)
    audience_count = Column(Integer)

class Result(Base):
    __tablename__ = "results"

    result_id = Column(Integer, primary_key=True, index=True)
    pilot_id = Column(Integer, ForeignKey("pilots.pilot_id"), nullable=False)
    stage_id = Column(Integer, ForeignKey("stages.stage_id"), nullable=False)
    position = Column(Integer, nullable=False)
    pit_stops = Column(Integer, nullable=False)
    race_time = Column(String, nullable=False)
    pilot = relationship("Pilot")
    stage = relationship("Stage")

# Создание таблиц в базе данных
Base.metadata.create_all(bind=engine)

# Определение приложения FastAPI
app = FastAPI()

# Pydantic models
class StableCreate(BaseModel):
    name: str
    country: str

    class Config:
        orm_mode = True

class StableResponse(StableCreate):
    stable_id: int

    class Config:
        orm_mode = True

class PilotCreate(BaseModel):
    name: str
    stable_id: int
    experience_years: int
    additional_info: str = None

    class Config:
        orm_mode = True

class PilotResponse(PilotCreate):
    pilot_id: int

    class Config:
        orm_mode = True

class StageCreate(BaseModel):
    date: datetime.date
    location: str
    track_length_km: float
    audience_count: int

    class Config:
        orm_mode = True

class StageResponse(StageCreate):
    stage_id: int

    class Config:
        orm_mode = True

class ResultCreate(BaseModel):
    pilot_id: int
    stage_id: int
    position: int
    pit_stops: int
    race_time: str

    class Config:
        orm_mode = True

class ResultResponse(ResultCreate):
    result_id: int

    class Config:
        orm_mode = True

# CRUD для Конюшен
@app.post("/stables/", response_model=StableResponse)
def create_stable(stable: StableCreate, db: Session = Depends(SessionLocal)):
    db_stable = Stable(name=stable.name, country=stable.country)
    db.add(db_stable)
    db.commit()
    db.refresh(db_stable)
    return db_stable

@app.get("/stables/{stable_id}", response_model=StableResponse)
def get_stable(stable_id: int, db: Session = Depends(SessionLocal)):
    db_stable = db.query(Stable).filter(Stable.stable_id == stable_id).first()
    if db_stable is None:
        raise HTTPException(status_code=404, detail="Stable not found")
    return db_stable

# CRUD для Пилотов
@app.post("/pilots/", response_model=PilotResponse)
def create_pilot(pilot: PilotCreate, db: Session = Depends(SessionLocal)):
    db_pilot = Pilot(name=pilot.name, stable_id=pilot.stable_id, experience_years=pilot.experience_years, additional_info=pilot.additional_info)
    db.add(db_pilot)
    db.commit()
    db.refresh(db_pilot)
    return db_pilot

@app.get("/pilots/{pilot_id}", response_model=PilotResponse)
def get_pilot(pilot_id: int, db: Session = Depends(SessionLocal)):
    db_pilot = db.query(Pilot).filter(Pilot.pilot_id == pilot_id).first()
    if db_pilot is None:
        raise HTTPException(status_code=404, detail="Pilot not found")
    return db_pilot

# CRUD для Этапов
@app.post("/stages/", response_model=StageResponse)
def create_stage(stage: StageCreate, db: Session = Depends(SessionLocal)):
    db_stage = Stage(date=stage.date, location=stage.location, track_length_km=stage.track_length_km, audience_count=stage.audience_count)
    db.add(db_stage)
    db.commit()
    db.refresh(db_stage)
    return db_stage

@app.get("/stages/{stage_id}", response_model=StageResponse)
def get_stage(stage_id: int, db: Session = Depends(SessionLocal)):
    db_stage = db.query(Stage).filter(Stage.stage_id == stage_id).first()
    if db_stage is None:
        raise HTTPException(status_code=404, detail="Stage not found")
    return db_stage

# CRUD для Результатов
@app.post("/results/", response_model=ResultResponse)
def create_result(result: ResultCreate, db: Session = Depends(SessionLocal)):
    db_result = Result(
        pilot_id=result.pilot_id, 
        stage_id=result.stage_id, 
        position=result.position,
        pit_stops=result.pit_stops,
        race_time=result.race_time
    )
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    return db_result

@app.get("/results/{result_id}", response_model=ResultResponse)
def get_result(result_id: int, db: Session = Depends(SessionLocal)):
    db_result = db.query(Result).filter(Result.result_id == result_id).first()
    if db_result is None:
        raise HTTPException(status_code=404, detail="Result not found")
    return db_result

# Генерация тестовых данных
@app.post("/generate_sample_data")
def generate_sample_data(db: Session = Depends(SessionLocal)):
    stable_names = ["Red Bull Racing", "Ferrari", "Mercedes", "McLaren"]
    countries = ["Austria", "Italy", "Germany", "UK"]
    pilots = ["Max Verstappen", "Charles Leclerc", "Lewis Hamilton", "Lando Norris"]

    # Создание Конюшен
    for name, country in zip(stable_names, countries):
        create_stable(StableCreate(name=name, country=country), db)

    # Создание Пилотов
    for i, name in enumerate(pilots):
        create_pilot(PilotCreate(name=name, stable_id=(i % len(stable_names)) + 1, experience_years=random.randint(1, 10)), db)

    # Создание Этапов
    for i in range(5):
        create_stage(StageCreate(
            date=datetime.date.today() - datetime.timedelta(days=i*30),
            location=f"Location_{i}",
            track_length_km=random.uniform(3.5, 7.0),
            audience_count=random.randint(5000, 100000)
        ), db)

    # Создание Результатов
    for i in range(10):
        create_result(ResultCreate(
            pilot_id=random.randint(1, len(pilots)),
            stage_id=random.randint(1, 5),
            position=random.randint(1, 20),
            pit_stops=random.randint(1, 5),
            race_time=str(datetime.timedelta(seconds=random.randint(3600, 7200)))
        ), db)

    return {"message": "Sample data generated successfully"}

# Дополнительные запросы
@app.get("/results/filter")
def get_results_filtered(position: int, pit_stops: int, db: Session = Depends(SessionLocal)):
    return db.query(Result).filter(Result.position <= position, Result.pit_stops >= pit_stops).all()

@app.get("/pilots/details")
def get_pilots_with_stables(db: Session = Depends(SessionLocal)):
    return db.query(Pilot, Stable).join(Stable, Pilot.stable_id == Stable.stable_id).all()

@app.put("/results/update_position")
def update_result_position(result_id: int, new_position: int, db: Session = Depends(SessionLocal)):
    db_result = db.query(Result).filter(Result.result_id == result_id).first()
    if db_result:
        db_result.position = new_position
        db.commit()
        return db_result
    raise HTTPException(status_code=404, detail="Result not found")

@app.get("/stages/group")
def get_stages_grouped_by_location(db: Session = Depends(SessionLocal)):
    return db.query(Stage.location, func.count(Stage.stage_id).label("stage_count")).group_by(Stage.location).all()

# Сортировка выдачи результатов
@app.get("/results/sorted")
def get_sorted_results(order_by: str, db: Session = Depends(SessionLocal)):
    if order_by not in ["position", "pit_stops", "race_time"]:
        raise HTTPException(status_code=400, detail="Invalid order_by parameter")
    return db.query(Result).order_by(order_by).all()

# Полнотекстовый поиск
@app.get("/pilots/search")
def search_pilots(query: str, db: Session = Depends(SessionLocal)):
    return db.query(Pilot).filter(Pilot.additional_info.contains(query)).all()