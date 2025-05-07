from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.services import UserService, TokenAlertService, BybitService
from app.keyboards import UserKeyboard
from loguru import logger
import re

router = Router()

# Регулярное выражение для проверки, похоже ли сообщение на тикер криптовалюты
TOKEN_PATTERN = re.compile(r'^[A-Z0-9]{2,10}$')

class AddAlertStates(StatesGroup):
    waiting_for_symbol = State()
    waiting_for_custom_token = State()
    waiting_for_custom_threshold = State()

@router.callback_query(F.data == "add_alert")
async def add_alert_start(callback: CallbackQuery, state: FSMContext):
    """Start process of adding a new alert."""
    user_id = callback.from_user.id
    user = await UserService.get_user(user_id)
    
    if not user or user.is_blocked or not user.is_approved:
        await callback.answer("You don't have permission to add alerts.")
        return
    
    await callback.message.edit_text(
        "Please enter the token symbol you want to track (e.g. BTC, ETH, SOL):"
    )
    await state.set_state(AddAlertStates.waiting_for_symbol)
    await callback.answer()

@router.callback_query(F.data == "enter_custom_token")
async def enter_custom_token(callback: CallbackQuery, state: FSMContext):
    """Handle custom token input."""
    user_id = callback.from_user.id
    user = await UserService.get_user(user_id)
    
    if not user or user.is_blocked or not user.is_approved:
        await callback.answer("You don't have permission to add alerts.")
        return
    
    await callback.message.edit_text(
        "Please enter the token symbol you want to track (e.g. BTC, ETH, SOL, TRUMP):"
    )
    await state.set_state(AddAlertStates.waiting_for_custom_token)
    await callback.answer()

@router.message(AddAlertStates.waiting_for_custom_token)
async def process_custom_token_input(message: Message, state: FSMContext):
    """Process custom token input from user."""
    symbol = message.text.strip().upper()
    
    # Check if token exists
    is_valid = await BybitService.is_token_valid(symbol)
    
    if not is_valid:
        await message.answer(
            f"Token {symbol} not found on Bybit. Please check the symbol and try again. "
            f"You can try another custom token or go back to the token list.",
            reply_markup=UserKeyboard.dashboard_menu()
        )
        await state.clear()
        return
    
    # Token exists, show price multiplier selection
    await message.answer(
        f"Token {symbol} found! Now select the price change step you want to monitor:",
        reply_markup=UserKeyboard.price_multiplier_select(symbol)
    )
    
    # Clear state
    await state.clear()

@router.message(AddAlertStates.waiting_for_symbol)
async def process_symbol_input(message: Message, state: FSMContext):
    """Handler for token input during alert creation."""
    token = message.text.strip().upper()
    user_id = message.from_user.id
    logger.info(f"User {user_id} entered token: {token}")
    
    # First, validate the token
    is_valid = await BybitService.is_token_valid(token)
    if not is_valid:
        logger.warning(f"User {user_id} entered invalid token: {token}")
        await message.answer(
            f"❌ Token '{token}' not found on Bybit.\n\n"
            "Please enter a valid token symbol (e.g., BTC), or type /cancel to abort."
        )
        return
    
    logger.info(f"User {user_id} entered valid token: {token}")
    await state.update_data(token=token)
    
    # Move to the next step (price multiplier)
    await state.set_state(AddAlertStates.waiting_for_custom_threshold)
    await message.answer(
        f"✅ Token '{token}' found on Bybit.\n\n"
        "Now, please enter the price change step for alert (e.g., 1000 for BTC, 10 for SOL, etc.)."
    )

# Добавим обработчик для проверки, является ли сообщение токеном
@router.message(lambda message: TOKEN_PATTERN.match(message.text.strip().upper()))
async def check_token_message(message: Message, state: FSMContext):
    """Check if a message might be a token and validate it."""
    # Пропускаем сообщения, которые совпадают с командами меню
    menu_commands = ["🏠 My Dashboard", "My Dashboard", "👥 User Management", "User Management", "📞 Support", "Support"]
    if message.text.strip() in menu_commands:
        return
    
    current_state = await state.get_state()
    # Если уже в режиме ожидания токена, не обрабатываем
    if current_state in [AddAlertStates.waiting_for_symbol.state, AddAlertStates.waiting_for_custom_token.state]:
        return
    
    symbol = message.text.strip().upper()
    user_id = message.from_user.id
    user = await UserService.get_user(user_id)
    
    if not user or user.is_blocked or not user.is_approved:
        return
    
    # Проверяем, существует ли токен
    is_valid = await BybitService.is_token_valid(symbol)
    
    if is_valid:
        await message.answer(
            f"Token {symbol} found! Now select the price change step you want to monitor:",
            reply_markup=UserKeyboard.price_multiplier_select(symbol)
        )
    else:
        await message.answer(
            f"Token {symbol} not found on Bybit. Please check the symbol or select from the list of available tokens.",
            reply_markup=UserKeyboard.dashboard_menu()
        )

@router.callback_query(F.data.startswith("set_multiplier:"))
async def set_price_multiplier(callback: CallbackQuery):
    """Set price multiplier for a token."""
    user_id = callback.from_user.id
    
    # Parse data
    _, symbol, multiplier_str = callback.data.split(":")
    multiplier = float(multiplier_str)
    
    logger.info(f"User {user_id} is setting up alert for {symbol} with step ${multiplier:g}")
    
    # Add alert
    alert = await TokenAlertService.add_alert(user_id, symbol, multiplier)
    
    if alert:
        logger.info(f"Successfully created alert for {symbol} (step: ${multiplier:g}) for user {user_id}")
        await callback.message.edit_text(
            f"✅ Alert set for {symbol} with ${multiplier:g} step.\n\n"
            f"You will be notified when the price crosses multiples of ${multiplier:g}.",
            reply_markup=UserKeyboard.dashboard_menu()
        )
    else:
        logger.error(f"Failed to create alert for {symbol} (step: ${multiplier:g}) for user {user_id}")
        await callback.message.edit_text(
            f"❌ Failed to set alert for {symbol}. Please try again later.",
            reply_markup=UserKeyboard.dashboard_menu()
        )
    
    await callback.answer()

@router.callback_query(F.data == "my_alerts")
async def show_user_alerts(callback: CallbackQuery):
    """Show user's configured alerts."""
    user_id = callback.from_user.id
    
    # Get alerts for user
    alerts = await TokenAlertService.get_user_alerts(user_id)
    
    if not alerts:
        message_text = "You don't have any alerts set up yet."
    else:
        message_text = "Your configured alerts:\n\n"
        for alert in alerts:
            status = "✅ Active" if alert.is_active else "❌ Disabled"
            price = f"${alert.price_multiplier:g}"
            message_text += f"{status} | {alert.symbol} | Step: {price}\n"
    
    await callback.message.edit_text(
        message_text,
        reply_markup=UserKeyboard.user_alerts(alerts)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("alerts_page:"))
async def paginate_alerts(callback: CallbackQuery):
    """Handle pagination for alerts list."""
    user_id = callback.from_user.id
    page = int(callback.data.split(":")[1])
    
    # Get alerts for user
    alerts = await TokenAlertService.get_user_alerts(user_id)
    
    message_text = "Your configured alerts:\n\n"
    if alerts:
        # Just a header, the individual alerts will be shown in the keyboard
        pass
    else:
        message_text = "You don't have any alerts set up yet."
    
    await callback.message.edit_reply_markup(
        reply_markup=UserKeyboard.user_alerts(alerts, page)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("alert_options:"))
async def show_alert_options(callback: CallbackQuery):
    """Show options for a specific alert."""
    user_id = callback.from_user.id
    alert_id = int(callback.data.split(":")[1])
    
    # Get all user alerts
    alerts = await TokenAlertService.get_user_alerts(user_id)
    
    # Find the specific alert
    alert = next((a for a in alerts if a.id == alert_id), None)
    
    if not alert:
        await callback.message.edit_text(
            "Alert not found. It may have been deleted.",
            reply_markup=UserKeyboard.dashboard_menu()
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        f"Alert options for {alert.symbol} (${alert.price_multiplier:g}):\n"
        f"Status: {'Active' if alert.is_active else 'Disabled'}",
        reply_markup=UserKeyboard.alert_options(alert.id, alert.is_active)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("enable_alert:"))
async def enable_alert(callback: CallbackQuery):
    """Enable a disabled alert."""
    alert_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    
    logger.info(f"User {user_id} is enabling alert {alert_id}")
    
    success = await TokenAlertService.toggle_alert(alert_id, True)
    
    if success:
        logger.info(f"Successfully enabled alert {alert_id} for user {user_id}")
        await callback.answer("Alert enabled")
        
        # Refresh alert options view
        alerts = await TokenAlertService.get_user_alerts(user_id)
        alert = next((a for a in alerts if a.id == alert_id), None)
        
        if alert:
            await callback.message.edit_text(
                f"Alert options for {alert.symbol} (${alert.price_multiplier:g}):\n"
                f"Status: {'Active' if alert.is_active else 'Disabled'}",
                reply_markup=UserKeyboard.alert_options(alert.id, alert.is_active)
            )
    else:
        logger.error(f"Failed to enable alert {alert_id} for user {user_id}")
        await callback.answer("Failed to enable alert")

@router.callback_query(F.data.startswith("disable_alert:"))
async def disable_alert(callback: CallbackQuery):
    """Disable an active alert."""
    alert_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    
    logger.info(f"User {user_id} is disabling alert {alert_id}")
    
    success = await TokenAlertService.toggle_alert(alert_id, False)
    
    if success:
        logger.info(f"Successfully disabled alert {alert_id} for user {user_id}")
        await callback.answer("Alert disabled")
        
        # Refresh alert options view
        alerts = await TokenAlertService.get_user_alerts(user_id)
        alert = next((a for a in alerts if a.id == alert_id), None)
        
        if alert:
            await callback.message.edit_text(
                f"Alert options for {alert.symbol} (${alert.price_multiplier:g}):\n"
                f"Status: {'Active' if alert.is_active else 'Disabled'}",
                reply_markup=UserKeyboard.alert_options(alert.id, alert.is_active)
            )
    else:
        logger.error(f"Failed to disable alert {alert_id} for user {user_id}")
        await callback.answer("Failed to disable alert")

@router.callback_query(F.data.startswith("remove_alert:"))
async def confirm_remove_alert(callback: CallbackQuery):
    """Ask confirmation before removing an alert."""
    alert_id = callback.data.split(":")[1]
    user_id = callback.from_user.id
    
    logger.info(f"User {user_id} wants to remove alert {alert_id}, showing confirmation")
    
    await callback.message.edit_text(
        "Are you sure you want to remove this alert?",
        reply_markup=UserKeyboard.confirmation_keyboard("remove_alert", alert_id)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("confirm_remove_alert:"))
async def remove_alert(callback: CallbackQuery):
    """Remove an alert after confirmation."""
    alert_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    
    logger.info(f"User {user_id} confirmed removal of alert {alert_id}")
    
    success = await TokenAlertService.remove_alert(alert_id)
    
    if success:
        logger.info(f"Successfully removed alert {alert_id} for user {user_id}")
        await callback.answer("Alert removed")
        await show_user_alerts(callback)
    else:
        logger.error(f"Failed to remove alert {alert_id} for user {user_id}")
        await callback.answer("Failed to remove alert")
        await show_user_alerts(callback)

@router.callback_query(F.data.startswith("cancel_remove_alert:"))
async def cancel_remove_alert(callback: CallbackQuery):
    """Cancel alert removal."""
    alert_id = int(callback.data.split(":")[1])
    
    # Get alert details to show options again
    user_id = callback.from_user.id
    alerts = await TokenAlertService.get_user_alerts(user_id)
    alert = next((a for a in alerts if a.id == alert_id), None)
    
    if alert:
        await callback.message.edit_text(
            f"Alert options for {alert.symbol} (${alert.price_multiplier:g}):\n"
            f"Status: {'Active' if alert.is_active else 'Disabled'}",
            reply_markup=UserKeyboard.alert_options(alert.id, alert.is_active)
        )
    else:
        await show_user_alerts(callback)
    
    await callback.answer("Operation cancelled")

@router.callback_query(F.data == "available_tokens")
async def show_available_tokens(callback: CallbackQuery):
    """Show available tokens on Bybit."""
    await callback.answer("Fetching available tokens...", show_alert=True)
    
    # Get top tokens from Bybit
    tokens = await BybitService.get_all_tokens()
    
    if not tokens:
        await callback.message.edit_text(
            "Failed to fetch available tokens. Please try again later.",
            reply_markup=UserKeyboard.dashboard_menu()
        )
        return
    
    # Sort tokens alphabetically
    tokens.sort()
    
    await callback.message.edit_text(
        "Select a token to set up price alerts:",
        reply_markup=UserKeyboard.token_list(tokens)
    )

@router.callback_query(F.data.startswith("token_page:"))
async def paginate_tokens(callback: CallbackQuery):
    """Handle pagination for token list."""
    page = int(callback.data.split(":")[1])
    
    # Get tokens from Bybit
    tokens = await BybitService.get_all_tokens()
    
    if not tokens:
        await callback.message.edit_text(
            "Failed to fetch available tokens. Please try again later.",
            reply_markup=UserKeyboard.dashboard_menu()
        )
        return
    
    # Sort tokens alphabetically
    tokens.sort()
    
    await callback.message.edit_reply_markup(
        reply_markup=UserKeyboard.token_list(tokens, page)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("select_token:"))
async def select_token(callback: CallbackQuery):
    """Handle token selection."""
    symbol = callback.data.split(":")[1]
    
    await callback.message.edit_text(
        f"You selected {symbol}. Now choose the price step for alerts:",
        reply_markup=UserKeyboard.price_multiplier_select(symbol)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("change_threshold:"))
async def change_alert_threshold(callback: CallbackQuery):
    """Show threshold options for changing an alert's threshold."""
    user_id = callback.from_user.id
    alert_id = int(callback.data.split(":")[1])
    
    # Get all user alerts
    alerts = await TokenAlertService.get_user_alerts(user_id)
    
    # Find the specific alert
    alert = next((a for a in alerts if a.id == alert_id), None)
    
    if not alert:
        await callback.message.edit_text(
            "Alert not found. It may have been deleted.",
            reply_markup=UserKeyboard.dashboard_menu()
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        f"Select new alert step for {alert.symbol}:\n"
        f"Current step: ${alert.price_multiplier:g}",
        reply_markup=UserKeyboard.threshold_options(alert.id, alert.symbol)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("update_threshold:"))
async def update_alert_threshold(callback: CallbackQuery):
    """Update an alert's threshold with a predefined value."""
    user_id = callback.from_user.id
    parts = callback.data.split(":")
    alert_id = int(parts[1])
    new_threshold = float(parts[2])
    
    logger.info(f"User {user_id} is updating alert {alert_id} step to ${new_threshold:g}")
    
    success = await TokenAlertService.update_threshold(alert_id, new_threshold)
    
    if success:
        logger.info(f"Successfully updated alert {alert_id} step to ${new_threshold:g} for user {user_id}")
        await callback.answer(f"Alert step updated to ${new_threshold:g}")
        
        # Get updated alert
        alerts = await TokenAlertService.get_user_alerts(user_id)
        alert = next((a for a in alerts if a.id == alert_id), None)
        
        # Show alert options again
        if alert:
            await callback.message.edit_text(
                f"Alert options for {alert.symbol} (${alert.price_multiplier:g}):\n"
                f"Status: {'Active' if alert.is_active else 'Disabled'}",
                reply_markup=UserKeyboard.alert_options(alert.id, alert.is_active)
            )
        else:
            await show_user_alerts(callback)
    else:
        logger.error(f"Failed to update alert {alert_id} step for user {user_id}")
        await callback.answer("Failed to update alert step")

@router.callback_query(F.data.startswith("custom_threshold:"))
async def enter_custom_threshold(callback: CallbackQuery, state: FSMContext):
    """Allow user to enter a custom threshold."""
    alert_id = int(callback.data.split(":")[1])
    
    await state.set_state(AddAlertStates.waiting_for_custom_threshold)
    await state.update_data(alert_id=alert_id)
    
    await callback.message.edit_text(
        "Please enter a custom alert step value (e.g. 0.5, 1.25, 333):"
    )
    await callback.answer()

@router.message(AddAlertStates.waiting_for_custom_threshold)
async def process_custom_threshold(message: Message, state: FSMContext):
    """Process custom threshold input."""
    # Get state data
    state_data = await state.get_data()
    alert_id = state_data.get("alert_id")
    token = state_data.get("token")
    
    user_id = message.from_user.id
    logger.info(f"User {user_id} entered custom threshold: {message.text}")
    
    # Try to parse the threshold
    try:
        text_value = message.text.strip()
        new_threshold = float(text_value)
        if new_threshold <= 0:
            raise ValueError("Alert step must be positive")
        
        logger.info(f"Parsed threshold value: {new_threshold}")
    except ValueError as e:
        logger.warning(f"Invalid threshold value from user {user_id}: {message.text} - {e}")
        await message.answer(
            "Invalid step value. Please enter a positive number (e.g. 0.5, 0.2, 1.25, 333)."
        )
        return
    
    # Если у нас есть токен, то создаем новый алерт
    if token and not alert_id:
        logger.info(f"Creating new alert for token {token} with step {new_threshold}")
        alert = await TokenAlertService.add_alert(user_id, token, new_threshold)
        
        if alert:
            logger.info(f"Successfully created alert for {token} with step ${new_threshold:g}")
            await message.answer(
                f"✅ Alert set for {token} with ${new_threshold:g} step.\n\n"
                f"You will be notified when the price crosses multiples of ${new_threshold:g}.",
                reply_markup=UserKeyboard.dashboard_menu()
            )
        else:
            logger.error(f"Failed to create alert for {token} with step ${new_threshold:g}")
            await message.answer(
                f"❌ Failed to set alert for {token}. Please try again later.",
                reply_markup=UserKeyboard.dashboard_menu()
            )
    # Если у нас есть ID алерта, то обновляем существующий
    elif alert_id:
        logger.info(f"Updating alert {alert_id} with new step {new_threshold}")
        # Update threshold
        success = await TokenAlertService.update_threshold(alert_id, new_threshold)
        
        if success:
            # Get updated alert info
            alerts = await TokenAlertService.get_user_alerts(user_id)
            alert = next((a for a in alerts if a.id == alert_id), None)
            
            if alert:
                logger.info(f"Successfully updated alert for {alert.symbol} with step ${new_threshold:g}")
                await message.answer(
                    f"Step for {alert.symbol} alert updated to ${new_threshold:g}.\n\n"
                    f"Alert options for {alert.symbol} (${alert.price_multiplier:g}):\n"
                    f"Status: {'Active' if alert.is_active else 'Disabled'}",
                    reply_markup=UserKeyboard.alert_options(alert.id, alert.is_active)
                )
            else:
                await message.answer(
                    f"Alert step updated to ${new_threshold:g}",
                    reply_markup=UserKeyboard.dashboard_menu()
                )
        else:
            logger.error(f"Failed to update alert {alert_id} with step ${new_threshold:g}")
            await message.answer(
                "Failed to update alert step. Please try again later.",
                reply_markup=UserKeyboard.dashboard_menu()
            )
    else:
        logger.error(f"Neither token nor alert_id available in state for user {user_id}")
        await message.answer(
            "An error occurred. Please try again from the beginning.",
            reply_markup=UserKeyboard.dashboard_menu()
        )
    
    # Clear state
    await state.clear() 