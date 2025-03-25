from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date, DateTime, JSON, func

Base = declarative_base()

class OptionChain(Base):
    __tablename__ = 'option_chain'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, index=True, nullable=False)
    contract_type = Column(String, nullable=False)  # "calls" or "puts"
    expiration_date = Column(Date, nullable=False)
    data = Column(JSON, nullable=False)  # raw JSON of the option chain for this expiry
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())
