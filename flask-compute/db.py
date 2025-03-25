from sqlalchemy import create_engine, Column, Integer, String, Numeric, Date, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv('DATABASE_URL')

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class OptionData(Base):
    __tablename__ = 'option_data'
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    expiration_date = Column(Date)
    option_type = Column(String) 
    strike = Column(Numeric)
    bid = Column(Numeric)
    ask = Column(Numeric)
    last_price = Column(Numeric)
    fetch_date = Column(DateTime)

class UnderlyingData(Base):
    __tablename__ = 'underlying_data'
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    date = Column(Date)
    close = Column(Numeric)
    fetch_date = Column(DateTime)

class YieldData(Base):
    __tablename__ = 'yield_data'
    id = Column(Integer, primary_key=True, index=True)
    label = Column(String)
    ticker = Column(String)
    date = Column(Date)
    close = Column(Numeric)
    fetch_date = Column(DateTime)

def init_db():
    print(DATABASE_URL, 'DATABASE_URL')
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("Database tables created.")
