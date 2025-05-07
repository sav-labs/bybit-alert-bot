from app.db import get_session, TokenAlert
from app.services.bybit_service import BybitService
from loguru import logger
from sqlalchemy.exc import SQLAlchemyError
import math
import time
from app.settings import POLLING_INTERVAL

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
            
            # Create new alert without last_alert_time parameter
            alert = TokenAlert(
                user_id=user_id,
                symbol=symbol,
                price_multiplier=price_multiplier,
                last_alert_price=current_price
            )
            
            session.add(alert)
            session.commit()
            
            # After commit, set last_alert_time manually if needed
            try:
                alert.last_alert_time = time.time()
                session.commit()
                logger.debug(f"Set last_alert_time for new alert {alert.id} to {alert.last_alert_time}")
            except Exception as e:
                logger.warning(f"Could not set last_alert_time for alert: {e}")
            
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
        
        # Определяем абсолютную разницу между текущей и последней ценой алерта
        price_diff = abs(current_price - last_alert_price)
        
        # Алерт срабатывает только если изменение цены больше или равно заданному порогу
        return price_diff >= price_multiplier
    
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
        current_time = time.time()  # Текущее время в секундах
        
        try:
            # Get all active alerts
            active_alerts = session.query(TokenAlert).filter(TokenAlert.is_active == True).all()
            
            if not active_alerts:
                logger.debug("No active alerts found to check")
                return []
                
            logger.debug(f"Checking {len(active_alerts)} active alerts")
            
            # Group alerts by symbol to minimize API calls
            symbols = set(alert.symbol for alert in active_alerts)
            logger.debug(f"Fetching prices for {len(symbols)} symbols: {', '.join(symbols)}")
            
            # Get prices for all symbols
            prices = {}
            for symbol in symbols:
                price = await BybitService.get_token_price(symbol)
                if price:
                    prices[symbol] = price
                    logger.debug(f"Fetched price for {symbol}: ${price:,.2f}")
                else:
                    logger.warning(f"Failed to fetch price for {symbol}")
            
            # Check each alert
            for alert in active_alerts:
                if alert.symbol not in prices:
                    continue
                
                current_price = prices[alert.symbol]
                previous_price = alert.last_alert_price  # Запоминаем предыдущую цену
                price_diff = abs(current_price - previous_price)
                
                logger.debug(f"Checking alert for {alert.symbol} (user: {alert.user_id}): current=${current_price:,.2f}, prev=${previous_price:,.2f}, diff=${price_diff:,.2f}, step=${alert.price_multiplier:g}")
                
                # Проверяем, нужно ли отправлять уведомление
                should_send = TokenAlertService.should_alert(current_price, previous_price, alert.price_multiplier)
                
                # Только при отправке уведомления добавляем в список для отправки
                if should_send:
                    logger.debug(f"Alert condition triggered for {alert.symbol}: price change (${price_diff:,.2f}) >= step (${alert.price_multiplier:g})")
                    
                    alerts_to_send.append({
                        "alert": alert,
                        "current_price": current_price,
                        "previous_price": previous_price
                    })
                    
                    # ВАЖНО: обновляем last_alert_price и last_alert_time ТОЛЬКО при отправке уведомления
                    alert.last_alert_price = current_price
                    # Пробуем обновить last_alert_time, если он есть
                    try:
                        if hasattr(alert, 'last_alert_time'):
                            alert.last_alert_time = current_time
                            logger.debug(f"Updated last_alert_time for {alert.symbol} to {current_time}")
                    except Exception as e:
                        logger.warning(f"Could not update last_alert_time for alert {alert.id}: {e}")
                    
                    logger.debug(f"Updated last_alert_price for {alert.symbol} to ${current_price:,.2f}")
            
            # Выполняем явный коммит для сохранения изменений
            session.commit()
            logger.debug(f"Committed changes for {len(active_alerts)} alerts")
            
            if alerts_to_send:
                logger.debug(f"Found {len(alerts_to_send)} alerts to send")
            else:
                logger.debug("No alerts triggered")
                
            return alerts_to_send
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error checking price alerts: {e}")
            return []
        finally:
            session.close()
    
    @staticmethod
    async def update_threshold(alert_id: int, new_threshold: float) -> bool:
        """Update the threshold for an alert."""
        if new_threshold <= 0:
            return False
        
        session = get_session()
        try:
            alert = session.query(TokenAlert).filter(TokenAlert.id == alert_id).first()
            if alert:
                # Обновляем threshold
                alert.price_multiplier = new_threshold
                # Получаем текущую цену для нового расчета алертов
                current_price = await BybitService.get_token_price(alert.symbol)
                # Обновляем last_alert_price, чтобы расчет начался с новой точки
                if current_price:
                    alert.last_alert_price = current_price
                    # Пробуем обновить время последнего алерта, если оно есть
                    try:
                        if hasattr(alert, 'last_alert_time'):
                            alert.last_alert_time = time.time()
                    except Exception as e:
                        logger.warning(f"Could not update last_alert_time for alert {alert_id}: {e}")
                
                session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error updating threshold for alert {alert_id}: {e}")
            return False
        finally:
            session.close() 