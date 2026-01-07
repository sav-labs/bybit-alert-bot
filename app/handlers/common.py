from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

from app.services import UserService
from app.keyboards import UserKeyboard, AdminKeyboard
from loguru import logger
import re

router = Router()

# Регулярное выражение для проверки, является ли сообщение возможным токеном
TOKEN_PATTERN = re.compile(r'^[A-Z0-9]{2,10}$')

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command."""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    # Create or get user
    user = await UserService.get_or_create_user(user_id, username, first_name, last_name)
    
    if not user:
        await message.answer("An error occurred while processing your request. Please try again later.")
        return
    
    is_blocked = user.is_blocked if hasattr(user, 'is_blocked') else False
    is_approved = user.is_approved if hasattr(user, 'is_approved') else False
    is_admin = user.is_admin if hasattr(user, 'is_admin') else False
    
    if is_blocked:
        await message.answer("You have been blocked from using this bot.")
        return
    
    if not is_approved:
        await message.answer(
            "Thank you for registering! Your account is pending approval by an administrator. "
            "You will be notified once your account is approved."
        )
        # Notify admins about new user
        await notify_admins_about_new_user(user_id, username or first_name)
        return
    
    # User is approved
    keyboard = UserKeyboard.admin_menu() if is_admin else UserKeyboard.main_menu()
    
    await message.answer(
        f"Welcome, {first_name or username or 'User'}! "
        f"Use the buttons below to navigate.",
        reply_markup=keyboard
    )

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Cancel current operation and clear FSM state."""
    current_state = await state.get_state()
    
    if current_state is None:
        await message.answer(
            "No active operation to cancel.",
            reply_markup=UserKeyboard.dashboard_menu()
        )
        return
    
    await state.clear()
    await message.answer(
        "✅ Operation cancelled.",
        reply_markup=UserKeyboard.dashboard_menu()
    )
    logger.info(f"User {message.from_user.id} cancelled operation from state: {current_state}")

@router.message(F.text.in_(["🏠 My Dashboard", "My Dashboard"]))
async def show_dashboard(message: Message, state: FSMContext):
    """Show user dashboard."""
    # Clear any active FSM state
    await state.clear()
    
    user_id = message.from_user.id
    user = await UserService.get_user(user_id)
    
    if not user:
        await message.answer("An error occurred while processing your request. Please try again later.")
        return
    
    is_blocked = user.is_blocked if hasattr(user, 'is_blocked') else False
    is_approved = user.is_approved if hasattr(user, 'is_approved') else False
    
    if is_blocked:
        await message.answer("You don't have access to this bot.")
        return
    
    if not is_approved:
        await message.answer("Your account is pending approval.")
        return
    
    display_name = user.first_name or user.username or 'User'
    
    await message.answer(
        f"Welcome to your dashboard, {display_name}!",
        reply_markup=UserKeyboard.dashboard_menu()
    )

@router.message(F.text.in_(["📞 Support", "Support"]))
async def show_support(message: Message):
    """Show support contact."""
    await message.answer(
        "If you need help or have questions, please contact @Artem_Solovev"
    )

@router.callback_query(F.data == "back_to_dashboard")
async def back_to_dashboard(callback: CallbackQuery):
    """Return to dashboard."""
    await callback.message.edit_text(
        "Welcome to your dashboard!",
        reply_markup=UserKeyboard.dashboard_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery):
    """Handle no-operation callback."""
    await callback.answer()

async def notify_admins_about_new_user(user_id: int, username: str):
    """Notify all admins about a new user registration."""
    from app.settings import BOT_ADMINS
    from app.bot import bot
    
    for admin_id in BOT_ADMINS:
        try:
            await bot.send_message(
                admin_id,
                f"New user registered:\nID: {user_id}\nUsername: {username}\n\n"
                f"Use the User Management menu to approve this user."
            )
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")

@router.message(lambda message: not TOKEN_PATTERN.match(message.text.strip().upper()) and message.text.strip() not in ["🏠 My Dashboard", "My Dashboard", "👥 User Management", "User Management", "📞 Support", "Support"])
async def echo(message: Message, state: FSMContext):
    """Echo all messages that didn't match other handlers and aren't potential tokens."""
    # Check if user is in any FSM state - if so, don't respond (let state handler process it)
    current_state = await state.get_state()
    if current_state:
        return
    
    # Проверяем, что сообщение не похоже на тикер и не является командой меню, прежде чем отвечать
    await message.answer("I don't understand this command. Please use the menu buttons.") 