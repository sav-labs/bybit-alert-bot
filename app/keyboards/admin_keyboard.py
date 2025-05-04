from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

class AdminKeyboard:
    @staticmethod
    def user_management() -> InlineKeyboardMarkup:
        """User management keyboard."""
        buttons = [
            [InlineKeyboardButton(text="👤 User List", callback_data="admin_user_list")],
            [InlineKeyboardButton(text="🔔 Pending Approvals", callback_data="admin_pending_users")],
            [InlineKeyboardButton(text="🚫 Blocked Users", callback_data="admin_blocked_users")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def user_list(users: list, page: int = 0, page_size: int = 5) -> InlineKeyboardMarkup:
        """User list keyboard."""
        buttons = []
        
        # Calculate pagination
        total_pages = (len(users) + page_size - 1) // page_size if users else 1
        start = page * page_size
        end = min(start + page_size, len(users)) if users else 0
        
        # Add user buttons
        if users:
            for user in users[start:end]:
                username = user.username or f"User {user.user_id}"
                status = "✅" if user.is_approved else "❌"
                
                buttons.append([InlineKeyboardButton(
                    text=f"{status} {username}",
                    callback_data=f"admin_user_options:{user.user_id}"
                )])
        else:
            buttons.append([InlineKeyboardButton(text="No users found", callback_data="noop")])
        
        # Add pagination controls
        pagination_row = []
        if page > 0:
            pagination_row.append(InlineKeyboardButton(text="⬅️", callback_data=f"admin_users_page:{page-1}"))
        
        if users:
            pagination_row.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="noop"))
        
        if page < total_pages - 1:
            pagination_row.append(InlineKeyboardButton(text="➡️", callback_data=f"admin_users_page:{page+1}"))
        
        if pagination_row:
            buttons.append(pagination_row)
        
        # Add back button
        buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="admin_back_to_management")])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def user_options(user_id: int, is_approved: bool, is_blocked: bool) -> InlineKeyboardMarkup:
        """User options keyboard."""
        buttons = []
        
        # Add options based on current status
        if not is_approved:
            buttons.append([InlineKeyboardButton(
                text="✅ Approve User", 
                callback_data=f"admin_approve_user:{user_id}"
            )])
        
        if is_blocked:
            buttons.append([InlineKeyboardButton(
                text="🔓 Unblock User", 
                callback_data=f"admin_unblock_user:{user_id}"
            )])
        else:
            buttons.append([InlineKeyboardButton(
                text="🔒 Block User", 
                callback_data=f"admin_block_user:{user_id}"
            )])
        
        # View user alerts
        buttons.append([InlineKeyboardButton(
            text="👁️ View User Alerts", 
            callback_data=f"admin_view_user_alerts:{user_id}"
        )])
        
        # Back button
        buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="admin_user_list")])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def view_user_alerts(alerts: list, user_id: int, page: int = 0, page_size: int = 5) -> InlineKeyboardMarkup:
        """View user alerts keyboard for admin."""
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
                    callback_data="noop"  # Admin can't modify user alerts directly
                )])
        else:
            buttons.append([InlineKeyboardButton(text="No alerts set up", callback_data="noop")])
        
        # Add pagination controls
        pagination_row = []
        if page > 0:
            pagination_row.append(InlineKeyboardButton(text="⬅️", callback_data=f"admin_user_alerts_page:{user_id}:{page-1}"))
        
        if alerts:
            pagination_row.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="noop"))
        
        if page < total_pages - 1:
            pagination_row.append(InlineKeyboardButton(text="➡️", callback_data=f"admin_user_alerts_page:{user_id}:{page+1}"))
        
        if pagination_row:
            buttons.append(pagination_row)
        
        # Back button
        buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data=f"admin_user_options:{user_id}")])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def confirmation_keyboard(action: str, user_id: int) -> InlineKeyboardMarkup:
        """Confirmation keyboard for admin actions."""
        buttons = [
            [
                InlineKeyboardButton(text="✅ Yes", callback_data=f"admin_confirm_{action}:{user_id}"),
                InlineKeyboardButton(text="❌ No", callback_data=f"admin_cancel_{action}:{user_id}")
            ]
        ]
        
        return InlineKeyboardMarkup(inline_keyboard=buttons) 