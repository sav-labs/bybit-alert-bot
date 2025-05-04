from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

from app.services import UserService
from app.keyboards import UserKeyboard, AdminKeyboard
from loguru import logger

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command."""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    # Create or get user
    user = await UserService.get_or_create_user(user_id, username, first_name, last_name)
    
    if user.is_blocked:
        await message.answer("You have been blocked from using this bot.")
        return
    
    if not user.is_approved:
        await message.answer(
            "Thank you for registering! Your account is pending approval by an administrator. "
            "You will be notified once your account is approved."
        )
        # Notify admins about new user
        await notify_admins_about_new_user(user_id, username or first_name)
        return
    
    # User is approved
    keyboard = UserKeyboard.admin_menu() if user.is_admin else UserKeyboard.main_menu()
    
    await message.answer(
        f"Welcome, {first_name or username or 'User'}! "
        f"Use the buttons below to navigate.",
        reply_markup=keyboard
    )

@router.message(F.text == "🏠 My Dashboard")
async def show_dashboard(message: Message):
    """Show user dashboard."""
    user_id = message.from_user.id
    user = await UserService.get_user(user_id)
    
    if not user or user.is_blocked:
        await message.answer("You don't have access to this bot.")
        return
    
    if not user.is_approved:
        await message.answer("Your account is pending approval.")
        return
    
    await message.answer(
        f"Welcome to your dashboard, {user.first_name or user.username or 'User'}!",
        reply_markup=UserKeyboard.dashboard_menu()
    )

@router.message(F.text == "📞 Support")
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

@router.message()
async def echo(message: Message):
    """Echo all messages that didn't match other handlers."""
    await message.answer("I don't understand this command. Please use the menu buttons.") 