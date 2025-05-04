from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from app.services import UserService, TokenAlertService
from app.keyboards import AdminKeyboard, UserKeyboard
from loguru import logger

router = Router()

@router.message(F.text.in_(["👥 User Management", "User Management"]))
async def show_user_management(message: Message):
    """Show user management options for admin."""
    user_id = message.from_user.id
    user = await UserService.get_user(user_id)
    
    if not user or not user.is_admin:
        await message.answer("You don't have permission to access user management.")
        return
    
    await message.answer(
        "User Management Panel",
        reply_markup=AdminKeyboard.user_management()
    )

@router.callback_query(F.data == "admin_user_list")
async def show_user_list(callback: CallbackQuery):
    """Show list of all users for admin."""
    user_id = callback.from_user.id
    user = await UserService.get_user(user_id)
    
    if not user or not user.is_admin:
        await callback.answer("You don't have admin privileges.")
        return
    
    users = await UserService.get_all_users()
    
    await callback.message.edit_text(
        "User List:",
        reply_markup=AdminKeyboard.user_list(users)
    )
    await callback.answer()

@router.callback_query(F.data == "admin_pending_users")
async def show_pending_users(callback: CallbackQuery):
    """Show users waiting for approval."""
    user_id = callback.from_user.id
    user = await UserService.get_user(user_id)
    
    if not user or not user.is_admin:
        await callback.answer("You don't have admin privileges.")
        return
    
    users = await UserService.get_pending_users()
    
    if not users:
        message_text = "No pending users found."
    else:
        message_text = "Users awaiting approval:"
    
    await callback.message.edit_text(
        message_text,
        reply_markup=AdminKeyboard.user_list(users)
    )
    await callback.answer()

@router.callback_query(F.data == "admin_blocked_users")
async def show_blocked_users(callback: CallbackQuery):
    """Show blocked users."""
    user_id = callback.from_user.id
    user = await UserService.get_user(user_id)
    
    if not user or not user.is_admin:
        await callback.answer("You don't have admin privileges.")
        return
    
    # Get all users
    all_users = await UserService.get_all_users()
    
    # Filter blocked users
    blocked_users = [u for u in all_users if u.is_blocked]
    
    if not blocked_users:
        message_text = "No blocked users found."
    else:
        message_text = "Blocked users:"
    
    await callback.message.edit_text(
        message_text,
        reply_markup=AdminKeyboard.user_list(blocked_users)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_users_page:"))
async def paginate_users(callback: CallbackQuery):
    """Handle pagination for user list."""
    user_id = callback.from_user.id
    user = await UserService.get_user(user_id)
    
    if not user or not user.is_admin:
        await callback.answer("You don't have admin privileges.")
        return
    
    page = int(callback.data.split(":")[1])
    
    # Get users based on current view
    # Check message text to determine what's being shown
    message_text = callback.message.text
    
    if "pending" in message_text.lower():
        users = await UserService.get_pending_users()
    elif "blocked" in message_text.lower():
        all_users = await UserService.get_all_users()
        users = [u for u in all_users if u.is_blocked]
    else:
        users = await UserService.get_all_users()
    
    await callback.message.edit_reply_markup(
        reply_markup=AdminKeyboard.user_list(users, page)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_user_options:"))
async def show_user_options(callback: CallbackQuery):
    """Show options for managing a specific user."""
    admin_id = callback.from_user.id
    admin = await UserService.get_user(admin_id)
    
    if not admin or not admin.is_admin:
        await callback.answer("You don't have admin privileges.")
        return
    
    user_id = int(callback.data.split(":")[1])
    user = await UserService.get_user(user_id)
    
    if not user:
        await callback.answer("User not found.")
        return
    
    username = user.username or f"User {user.user_id}"
    status = "Approved" if user.is_approved else "Pending Approval"
    block_status = "Blocked" if user.is_blocked else "Active"
    
    await callback.message.edit_text(
        f"User: {username}\n"
        f"ID: {user.user_id}\n"
        f"Status: {status}\n"
        f"Account: {block_status}\n",
        reply_markup=AdminKeyboard.user_options(user.user_id, user.is_approved, user.is_blocked)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_approve_user:"))
async def confirm_approve_user(callback: CallbackQuery):
    """Ask confirmation before approving a user."""
    admin_id = callback.from_user.id
    admin = await UserService.get_user(admin_id)
    
    if not admin or not admin.is_admin:
        await callback.answer("You don't have admin privileges.")
        return
    
    user_id = callback.data.split(":")[1]
    
    await callback.message.edit_text(
        "Are you sure you want to approve this user?",
        reply_markup=AdminKeyboard.confirmation_keyboard("approve_user", int(user_id))
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_block_user:"))
async def confirm_block_user(callback: CallbackQuery):
    """Ask confirmation before blocking a user."""
    admin_id = callback.from_user.id
    admin = await UserService.get_user(admin_id)
    
    if not admin or not admin.is_admin:
        await callback.answer("You don't have admin privileges.")
        return
    
    user_id = callback.data.split(":")[1]
    
    await callback.message.edit_text(
        "Are you sure you want to block this user?",
        reply_markup=AdminKeyboard.confirmation_keyboard("block_user", int(user_id))
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_unblock_user:"))
async def confirm_unblock_user(callback: CallbackQuery):
    """Ask confirmation before unblocking a user."""
    admin_id = callback.from_user.id
    admin = await UserService.get_user(admin_id)
    
    if not admin or not admin.is_admin:
        await callback.answer("You don't have admin privileges.")
        return
    
    user_id = callback.data.split(":")[1]
    
    await callback.message.edit_text(
        "Are you sure you want to unblock this user?",
        reply_markup=AdminKeyboard.confirmation_keyboard("unblock_user", int(user_id))
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_confirm_approve_user:"))
async def approve_user(callback: CallbackQuery):
    """Approve a user after confirmation."""
    admin_id = callback.from_user.id
    admin = await UserService.get_user(admin_id)
    
    if not admin or not admin.is_admin:
        await callback.answer("You don't have admin privileges.")
        return
    
    user_id = int(callback.data.split(":")[1])
    
    success = await UserService.approve_user(user_id)
    
    if success:
        await callback.answer("User approved")
        
        # Notify the user that they've been approved
        from app.bot import bot
        user = await UserService.get_user(user_id)
        try:
            await bot.send_message(
                user_id,
                "✅ Your account has been approved! You can now use the bot."
            )
        except Exception as e:
            logger.error(f"Failed to notify user {user_id} about approval: {e}")
        
        # Refresh user options
        await show_user_options(callback)
    else:
        await callback.answer("Failed to approve user")

@router.callback_query(F.data.startswith("admin_confirm_block_user:"))
async def block_user(callback: CallbackQuery):
    """Block a user after confirmation."""
    admin_id = callback.from_user.id
    admin = await UserService.get_user(admin_id)
    
    if not admin or not admin.is_admin:
        await callback.answer("You don't have admin privileges.")
        return
    
    user_id = int(callback.data.split(":")[1])
    
    success = await UserService.block_user(user_id)
    
    if success:
        await callback.answer("User blocked")
        
        # Notify the user that they've been blocked
        from app.bot import bot
        try:
            await bot.send_message(
                user_id,
                "🚫 Your account has been blocked. Please contact @Artem_Solovev for assistance."
            )
        except Exception as e:
            logger.error(f"Failed to notify user {user_id} about block: {e}")
        
        # Refresh user options
        await show_user_options(callback)
    else:
        await callback.answer("Failed to block user")

@router.callback_query(F.data.startswith("admin_confirm_unblock_user:"))
async def unblock_user(callback: CallbackQuery):
    """Unblock a user after confirmation."""
    admin_id = callback.from_user.id
    admin = await UserService.get_user(admin_id)
    
    if not admin or not admin.is_admin:
        await callback.answer("You don't have admin privileges.")
        return
    
    user_id = int(callback.data.split(":")[1])
    
    success = await UserService.unblock_user(user_id)
    
    if success:
        await callback.answer("User unblocked")
        
        # Notify the user that they've been unblocked
        from app.bot import bot
        try:
            await bot.send_message(
                user_id,
                "✅ Your account has been unblocked. You can now use the bot again."
            )
        except Exception as e:
            logger.error(f"Failed to notify user {user_id} about unblock: {e}")
        
        # Refresh user options
        await show_user_options(callback)
    else:
        await callback.answer("Failed to unblock user")

@router.callback_query(F.data.startswith("admin_cancel_"))
async def cancel_admin_action(callback: CallbackQuery):
    """Cancel an admin action."""
    admin_id = callback.from_user.id
    admin = await UserService.get_user(admin_id)
    
    if not admin or not admin.is_admin:
        await callback.answer("You don't have admin privileges.")
        return
    
    # Parse callback data to extract user_id and return to user options
    parts = callback.data.split("_")
    action = parts[2]
    user_id = int(parts[3].split(":")[1])
    
    await show_user_options(callback)
    await callback.answer("Operation cancelled")

@router.callback_query(F.data.startswith("admin_view_user_alerts:"))
async def view_user_alerts(callback: CallbackQuery):
    """View alerts configured by a specific user."""
    admin_id = callback.from_user.id
    admin = await UserService.get_user(admin_id)
    
    if not admin or not admin.is_admin:
        await callback.answer("You don't have admin privileges.")
        return
    
    user_id = int(callback.data.split(":")[1])
    user = await UserService.get_user(user_id)
    
    if not user:
        await callback.answer("User not found.")
        return
    
    alerts = await TokenAlertService.get_user_alerts(user_id)
    
    username = user.username or f"User {user.user_id}"
    
    if not alerts:
        message_text = f"User {username} has no alerts configured."
    else:
        message_text = f"Alerts for {username}:\n\n"
        for alert in alerts:
            status = "✅ Active" if alert.is_active else "❌ Disabled"
            price = f"${alert.price_multiplier:g}"
            message_text += f"{status} | {alert.symbol} | Threshold: {price}\n"
    
    await callback.message.edit_text(
        message_text,
        reply_markup=AdminKeyboard.view_user_alerts(alerts, user_id)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_user_alerts_page:"))
async def paginate_user_alerts(callback: CallbackQuery):
    """Handle pagination for user alerts view."""
    admin_id = callback.from_user.id
    admin = await UserService.get_user(admin_id)
    
    if not admin or not admin.is_admin:
        await callback.answer("You don't have admin privileges.")
        return
    
    # Parse user_id and page from callback data
    parts = callback.data.split(":")
    user_id = int(parts[1])
    page = int(parts[2])
    
    alerts = await TokenAlertService.get_user_alerts(user_id)
    
    await callback.message.edit_reply_markup(
        reply_markup=AdminKeyboard.view_user_alerts(alerts, user_id, page)
    )
    await callback.answer()

@router.callback_query(F.data == "admin_back_to_management")
async def back_to_management(callback: CallbackQuery):
    """Return to user management menu."""
    await callback.message.edit_text(
        "User Management Panel",
        reply_markup=AdminKeyboard.user_management()
    )
    await callback.answer() 