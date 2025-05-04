from app.db import get_session, TokenAlert
from app.services.bybit_service import BybitService
from loguru import logger
from sqlalchemy.exc import SQLAlchemyError
import math

class TokenAlertService:
    @staticmethod
    async def get_user_alerts(user_id: int) -> list:
        """Get all alerts for a user."""
        session = get_session()
        try:
            alerts = session.query(TokenAlert).filter(TokenAlert.user_id == user_id).all()
            
            # Загружаем необходимые атрибуты для каждого алерта
            for alert in alerts:
                _ = alert.symbol
                _ = alert.price_multiplier 
                _ = alert.is_active
                _ = alert.last_alert_price
            
            return alerts
        except SQLAlchemyError as e:
            logger.error(f"Error getting alerts for user {user_id}: {e}")
            return []
        finally:
            session.close()
    
    @staticmethod
    async def add_alert(user_id: int, symbol: str, price_multiplier: float) -> TokenAlert:
        """Add a new token alert."""
        # First check if the token is valid
        is_valid = await BybitService.is_token_valid(symbol)
        if not is_valid:
            return None
        
        session = get_session()
        try:
            # Check if alert already exists
            existing = session.query(TokenAlert).filter(
                TokenAlert.user_id == user_id,
                TokenAlert.symbol == symbol,
                TokenAlert.price_multiplier == price_multiplier
            ).first()
            
            if existing:
                # If exists but not active, reactivate it
                if not existing.is_active:
                    existing.is_active = True
                    session.commit()
                
                # Загружаем необходимые атрибуты
                _ = existing.symbol
                _ = existing.price_multiplier
                _ = existing.is_active
                _ = existing.last_alert_price
                
                return existing
            
            # Get current price
            current_price = await BybitService.get_token_price(symbol)
            
            # Create new alert
            alert = TokenAlert(
                user_id=user_id,
                symbol=symbol,
                price_multiplier=price_multiplier,
                last_alert_price=current_price
            )
            
            session.add(alert)
            session.commit()
            
            # Загружаем необходимые атрибуты
            _ = alert.id
            _ = alert.symbol
            _ = alert.price_multiplier
            _ = alert.is_active
            _ = alert.last_alert_price
            
            return alert
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error adding alert for user {user_id}, symbol {symbol}: {e}")
            return None
        finally:
            session.close()
    
    @staticmethod
    async def toggle_alert(alert_id: int, active: bool) -> bool:
        """Toggle an alert on or off."""
        session = get_session()
        try:
            alert = session.query(TokenAlert).filter(TokenAlert.id == alert_id).first()
            if alert:
                alert.is_active = active
                session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error toggling alert {alert_id}: {e}")
            return False
        finally:
            session.close()
    
    @staticmethod
    async def remove_alert(alert_id: int) -> bool:
        """Remove an alert."""
        session = get_session()
        try:
            alert = session.query(TokenAlert).filter(TokenAlert.id == alert_id).first()
            if alert:
                session.delete(alert)
                session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error removing alert {alert_id}: {e}")
            return False
        finally:
            session.close()
    
    @staticmethod
    def should_alert(current_price: float, last_alert_price: float, price_multiplier: float) -> bool:
        """Determine if an alert should be triggered."""
        if last_alert_price is None:
            return True
        
        # Get the price multiples
        current_multiple = math.floor(current_price / price_multiplier)
        last_multiple = math.floor(last_alert_price / price_multiplier)
        
        # Alert if the price has crossed a multiple boundary
        return current_multiple != last_multiple
    
    @staticmethod
    async def update_last_alert_price(alert_id: int, new_price: float) -> bool:
        """Update the last alert price for a token."""
        session = get_session()
        try:
            alert = session.query(TokenAlert).filter(TokenAlert.id == alert_id).first()
            if alert:
                alert.last_alert_price = new_price
                session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error updating last alert price for alert {alert_id}: {e}")
            return False
        finally:
            session.close()
    
    @staticmethod
    async def check_price_alerts() -> list:
        """Check all active alerts for price changes that trigger notifications."""
        session = get_session()
        alerts_to_send = []
        
        try:
            # Get all active alerts
            active_alerts = session.query(TokenAlert).filter(TokenAlert.is_active == True).all()
            
            # Загружаем необходимые атрибуты для каждого алерта
            for alert in active_alerts:
                _ = alert.symbol
                _ = alert.price_multiplier
                _ = alert.last_alert_price
                _ = alert.user_id
            
            # Group alerts by symbol to minimize API calls
            symbols = set(alert.symbol for alert in active_alerts)
            
            # Get prices for all symbols
            prices = {}
            for symbol in symbols:
                price = await BybitService.get_token_price(symbol)
                if price:
                    prices[symbol] = price
            
            # Check each alert
            for alert in active_alerts:
                if alert.symbol not in prices:
                    continue
                
                current_price = prices[alert.symbol]
                
                if TokenAlertService.should_alert(current_price, alert.last_alert_price, alert.price_multiplier):
                    alerts_to_send.append({
                        "alert": alert,
                        "current_price": current_price
                    })
                    
                    # Update last alert price
                    alert.last_alert_price = current_price
            
            session.commit()
            return alerts_to_send
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error checking price alerts: {e}")
            return []
        finally:
            session.close() 