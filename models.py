from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from database import Base


class SpimexTradingResult(Base):
    __tablename__ = 'spimex_trading_results'

    id = Column(Integer, primary_key=True)
    exchange_product_id = Column(String(20), nullable=False)
    exchange_product_name = Column(String(255))
    oil_id = Column(String(10))
    delivery_basis_id = Column(String(10))
    delivery_basis_name = Column(String(255))
    delivery_type_id = Column(String(1))
    volume = Column(Numeric(20, 2))
    total = Column(Numeric(20, 2))
    count = Column(Integer)
    date = Column(Date, nullable=False)
    created_on = Column(DateTime, default=datetime.now)
    updated_on = Column(DateTime, default=datetime.now, onupdate=datetime.now)
