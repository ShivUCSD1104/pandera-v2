from sqlalchemy import create_engine, Column, Integer, String, Numeric, Date, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import os
import logging

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv('DATABASE_URL')

# Configure connection pooling for performance optimization
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,          # Number of connections to maintain in pool
    max_overflow=20,       # Additional connections beyond pool_size
    pool_pre_ping=True,    # Validate connections before use
    pool_recycle=3600,     # Recycle connections after 1 hour
    echo=False             # Set to True for SQL debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class OptionData(Base):
    __tablename__ = 'option_data'
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    expiration_date = Column(Date, index=True)
    option_type = Column(String, index=True) 
    strike = Column(Numeric, index=True)
    bid = Column(Numeric)
    ask = Column(Numeric)
    last_price = Column(Numeric)
    fetch_date = Column(DateTime, index=True)
    
    # Composite indexes for performance optimization
    __table_args__ = (
        Index('idx_option_ticker_expiry', 'ticker', 'expiration_date'),
        Index('idx_option_ticker_type', 'ticker', 'option_type'),
        Index('idx_option_ticker_strike', 'ticker', 'strike'),
        Index('idx_option_ticker_expiry_type', 'ticker', 'expiration_date', 'option_type'),
        Index('idx_option_fetch_date', 'fetch_date'),
    )

class UnderlyingData(Base):
    __tablename__ = 'underlying_data'
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    date = Column(Date, index=True)
    close = Column(Numeric)
    fetch_date = Column(DateTime, index=True)
    
    # Composite indexes for performance optimization
    __table_args__ = (
        Index('idx_underlying_ticker_date', 'ticker', 'date'),
        Index('idx_underlying_fetch_date', 'fetch_date'),
    )

class YieldData(Base):
    __tablename__ = 'yield_data'
    id = Column(Integer, primary_key=True, index=True)
    label = Column(String, index=True)
    ticker = Column(String, index=True)
    date = Column(Date, index=True)
    close = Column(Numeric)
    fetch_date = Column(DateTime, index=True)
    
    # Composite indexes for performance optimization
    __table_args__ = (
        Index('idx_yield_ticker_date', 'ticker', 'date'),
        Index('idx_yield_label_date', 'label', 'date'),
        Index('idx_yield_fetch_date', 'fetch_date'),
    )

def init_db():
    print(DATABASE_URL, 'DATABASE_URL')
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("Database tables created.")
