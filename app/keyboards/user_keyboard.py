from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from app.settings import AVAILABLE_PRICE_MULTIPLIERS

class UserKeyboard:
    @staticmethod
    def main_menu() -> ReplyKeyboardMarkup:
        """Main menu keyboard."""
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(KeyboardButton("🏠 My Dashboard"))
        keyboard.add(KeyboardButton("📞 Support"))
        return keyboard
    
    @staticmethod
    def admin_menu() -> ReplyKeyboardMarkup:
        """Admin menu keyboard."""
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(KeyboardButton("🏠 My Dashboard"))
        keyboard.add(KeyboardButton("👥 User Management"))
        keyboard.add(KeyboardButton("📞 Support"))
        return keyboard
    
    @staticmethod
    def dashboard_menu() -> InlineKeyboardMarkup:
        """Dashboard menu keyboard."""
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("➕ Add New Alert", callback_data="add_alert"))
        keyboard.add(InlineKeyboardButton("📊 My Alerts", callback_data="my_alerts"))
        keyboard.add(InlineKeyboardButton("🔍 Available Tokens", callback_data="available_tokens"))
        return keyboard
    
    @staticmethod
    def token_list(tokens: list, page: int = 0, page_size: int = 5) -> InlineKeyboardMarkup:
        """List of tokens keyboard."""
        keyboard = InlineKeyboardMarkup()
        
        # Calculate pagination
        total_pages = (len(tokens) + page_size - 1) // page_size
        start = page * page_size
        end = min(start + page_size, len(tokens))
        
        # Add token buttons
        for token in tokens[start:end]:
            keyboard.add(InlineKeyboardButton(token, callback_data=f"select_token:{token}"))
        
        # Add pagination controls
        row = []
        if page > 0:
            row.append(InlineKeyboardButton("⬅️", callback_data=f"token_page:{page-1}"))
        
        row.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
        
        if page < total_pages - 1:
            row.append(InlineKeyboardButton("➡️", callback_data=f"token_page:{page+1}"))
        
        if row:
            keyboard.row(*row)
        
        # Add back button
        keyboard.add(InlineKeyboardButton("🔙 Back", callback_data="back_to_dashboard"))
        
        return keyboard
    
    @staticmethod
    def price_multiplier_select(symbol: str) -> InlineKeyboardMarkup:
        """Price multiplier selection keyboard."""
        keyboard = InlineKeyboardMarkup()
        
        # Add price multipliers
        for multiplier in AVAILABLE_PRICE_MULTIPLIERS:
            formatted = f"${multiplier:g}" # Remove trailing zeros
            keyboard.add(InlineKeyboardButton(
                formatted, 
                callback_data=f"set_multiplier:{symbol}:{multiplier}"
            ))
        
        # Add back button
        keyboard.add(InlineKeyboardButton("🔙 Back", callback_data="available_tokens"))
        
        return keyboard
    
    @staticmethod
    def user_alerts(alerts: list, page: int = 0, page_size: int = 5) -> InlineKeyboardMarkup:
        """User alerts keyboard."""
        keyboard = InlineKeyboardMarkup()
        
        # Calculate pagination
        total_pages = (len(alerts) + page_size - 1) // page_size if alerts else 1
        start = page * page_size
        end = min(start + page_size, len(alerts)) if alerts else 0
        
        # Add alert buttons
        if alerts:
            for alert in alerts[start:end]:
                symbol = alert.symbol
                multiplier = alert.price_multiplier
                status = "✅" if alert.is_active else "❌"
                
                keyboard.add(InlineKeyboardButton(
                    f"{status} {symbol} - ${multiplier:g}",
                    callback_data=f"alert_options:{alert.id}"
                ))
        else:
            keyboard.add(InlineKeyboardButton("No alerts set up yet", callback_data="noop"))
        
        # Add pagination controls
        row = []
        if page > 0:
            row.append(InlineKeyboardButton("⬅️", callback_data=f"alerts_page:{page-1}"))
        
        if alerts:
            row.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
        
        if page < total_pages - 1:
            row.append(InlineKeyboardButton("➡️", callback_data=f"alerts_page:{page+1}"))
        
        if row:
            keyboard.row(*row)
        
        # Add back button
        keyboard.add(InlineKeyboardButton("🔙 Back", callback_data="back_to_dashboard"))
        
        return keyboard
    
    @staticmethod
    def alert_options(alert_id: int, is_active: bool) -> InlineKeyboardMarkup:
        """Alert options keyboard."""
        keyboard = InlineKeyboardMarkup()
        
        # Toggle status button
        status_text = "Disable" if is_active else "Enable"
        status_action = "disable" if is_active else "enable"
        keyboard.add(InlineKeyboardButton(
            f"{status_text} Alert", 
            callback_data=f"{status_action}_alert:{alert_id}"
        ))
        
        # Remove button
        keyboard.add(InlineKeyboardButton(
            "🗑️ Remove Alert", 
            callback_data=f"remove_alert:{alert_id}"
        ))
        
        # Back button
        keyboard.add(InlineKeyboardButton("🔙 Back", callback_data="my_alerts"))
        
        return keyboard
    
    @staticmethod
    def confirmation_keyboard(action: str, item_id: str) -> InlineKeyboardMarkup:
        """Confirmation keyboard."""
        keyboard = InlineKeyboardMarkup()
        
        keyboard.row(
            InlineKeyboardButton("✅ Yes", callback_data=f"confirm_{action}:{item_id}"),
            InlineKeyboardButton("❌ No", callback_data=f"cancel_{action}:{item_id}")
        )
        
        return keyboard 