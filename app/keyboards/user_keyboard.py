from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from app.settings import AVAILABLE_PRICE_MULTIPLIERS

class UserKeyboard:
    @staticmethod
    def main_menu() -> ReplyKeyboardMarkup:
        """Main menu keyboard."""
        keyboard = [
            [KeyboardButton(text="🏠 My Dashboard")],
            [KeyboardButton(text="📞 Support")]
        ]
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    
    @staticmethod
    def admin_menu() -> ReplyKeyboardMarkup:
        """Admin menu keyboard."""
        keyboard = [
            [KeyboardButton(text="🏠 My Dashboard")],
            [KeyboardButton(text="👥 User Management")],
            [KeyboardButton(text="📞 Support")]
        ]
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    
    @staticmethod
    def dashboard_menu() -> InlineKeyboardMarkup:
        """Dashboard menu keyboard."""
        buttons = [
            [InlineKeyboardButton(text="➕ Add New Alert", callback_data="add_alert")],
            [InlineKeyboardButton(text="📊 My Alerts", callback_data="my_alerts")],
            [InlineKeyboardButton(text="🔍 Available Tokens", callback_data="available_tokens")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def token_list(tokens: list, page: int = 0, page_size: int = 5) -> InlineKeyboardMarkup:
        """List of tokens keyboard."""
        buttons = []
        
        # Add button for manual token input
        buttons.append([InlineKeyboardButton(text="✏️ Enter Custom Token", callback_data="enter_custom_token")])
        
        # Calculate pagination
        total_pages = (len(tokens) + page_size - 1) // page_size
        start = page * page_size
        end = min(start + page_size, len(tokens))
        
        # Add token buttons
        for token in tokens[start:end]:
            buttons.append([InlineKeyboardButton(text=token, callback_data=f"select_token:{token}")])
        
        # Add pagination controls
        pagination_row = []
        if page > 0:
            pagination_row.append(InlineKeyboardButton(text="⬅️", callback_data=f"token_page:{page-1}"))
        
        pagination_row.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="noop"))
        
        if page < total_pages - 1:
            pagination_row.append(InlineKeyboardButton(text="➡️", callback_data=f"token_page:{page+1}"))
        
        if pagination_row:
            buttons.append(pagination_row)
        
        # Add back button
        buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_to_dashboard")])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def price_multiplier_select(symbol: str) -> InlineKeyboardMarkup:
        """Price multiplier selection keyboard."""
        buttons = []
        
        # Add price multipliers
        for multiplier in AVAILABLE_PRICE_MULTIPLIERS:
            formatted = f"${multiplier:g}" # Remove trailing zeros
            buttons.append([InlineKeyboardButton(
                text=formatted, 
                callback_data=f"set_multiplier:{symbol}:{multiplier}"
            )])
        
        # Add back button
        buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="available_tokens")])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def user_alerts(alerts: list, page: int = 0, page_size: int = 5) -> InlineKeyboardMarkup:
        """User alerts keyboard."""
        buttons = []
        
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
                
                buttons.append([InlineKeyboardButton(
                    text=f"{status} {symbol} - ${multiplier:g}",
                    callback_data=f"alert_options:{alert.id}"
                )])
        else:
            buttons.append([InlineKeyboardButton(text="No alerts set up yet", callback_data="noop")])
        
        # Add pagination controls
        pagination_row = []
        if page > 0:
            pagination_row.append(InlineKeyboardButton(text="⬅️", callback_data=f"alerts_page:{page-1}"))
        
        if alerts:
            pagination_row.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="noop"))
        
        if page < total_pages - 1:
            pagination_row.append(InlineKeyboardButton(text="➡️", callback_data=f"alerts_page:{page+1}"))
        
        if pagination_row:
            buttons.append(pagination_row)
        
        # Add back button
        buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_to_dashboard")])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def alert_options(alert_id: int, is_active: bool) -> InlineKeyboardMarkup:
        """Alert options keyboard."""
        buttons = []
        
        # Toggle status button
        status_text = "Disable" if is_active else "Enable"
        status_action = "disable" if is_active else "enable"
        buttons.append([InlineKeyboardButton(
            text=f"{status_text} Alert", 
            callback_data=f"{status_action}_alert:{alert_id}"
        )])
        
        # Remove button
        buttons.append([InlineKeyboardButton(
            text="🗑️ Remove Alert", 
            callback_data=f"remove_alert:{alert_id}"
        )])
        
        # Back button
        buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="my_alerts")])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def confirmation_keyboard(action: str, item_id: str) -> InlineKeyboardMarkup:
        """Confirmation keyboard."""
        buttons = [
            [
                InlineKeyboardButton(text="✅ Yes", callback_data=f"confirm_{action}:{item_id}"),
                InlineKeyboardButton(text="❌ No", callback_data=f"cancel_{action}:{item_id}")
            ]
        ]
        
        return InlineKeyboardMarkup(inline_keyboard=buttons) 