from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from os import environ

Base = declarative_base()


class Chickens(Base):
    __tablename__ = 'chickens'

    batch_id = Column(String, primary_key=True, index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    line_number = Column(Integer, nullable=False)
    machine_id = Column(Integer, nullable=False)
    count = Column(Integer, nullable=False)
    cross_ = Column(String, nullable=False)


class Camera(Base):
    __tablename__ = 'cameras'

    camera_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=False)
    rtsp_stream = Column(String, nullable=False)

# Указываем параметры подключения к базе данных PostgreSQL
SQLALCHEMY_DATABASE_URL = environ.get("DATABASE_URL")

# Создаем движок базы данных
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Создаем таблицы в базе данных
Base.metadata.create_all(bind=engine)

# Создаем сессию для работы с базой данных
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
