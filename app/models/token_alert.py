from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.models.base import Base

class TokenAlert(Base):
    __tablename__ = "token_alerts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    symbol = Column(String, nullable=False)
    price_multiplier = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    last_alert_price = Column(Float, nullable=True)
    last_alert_time = Column(Float, nullable=True)  # Unix timestamp of last alert
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<TokenAlert(user_id={self.user_id}, symbol={self.symbol}, price_multiplier={self.price_multiplier}, is_active={self.is_active})>" 