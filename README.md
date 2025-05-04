# Bybit Price Alert Bot

A Telegram bot that monitors cryptocurrency prices on Bybit and sends alerts when prices cross specified thresholds.

## Features

- **Price Monitoring**: Track multiple tokens on Bybit exchange
- **Customizable Thresholds**: Set custom price thresholds for each token
- **Real-time Alerts**: Get notified when prices cross your specified thresholds
- **User-friendly Interface**: Easy-to-use inline buttons and keyboard menus
- **User Management**: Admin can approve, block, and manage users
- **Multi-user Support**: Each user can configure their own alerts

## Requirements

- Python 3.8+
- Docker and Docker Compose (for containerized deployment)
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/bybit-alert-bot.git
cd bybit-alert-bot
```

### 2. Configure the environment variables

Copy the example environment file and edit it with your settings:

```bash
cp .env.example .env
```

Edit the `.env` file and add your Telegram Bot Token and other settings:

```
BOT_TOKEN=your_telegram_bot_token
BOT_ADMINS=123456789,987654321  # Your Telegram user ID(s)
POLLING_INTERVAL=60  # How often to check prices (in seconds)
LOG_LEVEL=INFO  # DEBUG or INFO
```

### 3. Deploy using Docker (Recommended)

Run the deployment script:

```bash
chmod +x deploy.sh
./deploy.sh
```

The script will:
- Create the necessary directories
- Build the Docker image
- Start the bot in a container

### 4. Manual installation (Alternative)

If you prefer to run without Docker:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create required directories
mkdir -p logs data

# Run the bot
python main.py
```

## Usage

1. Start the bot by sending `/start` in Telegram
2. Admin will need to approve new users
3. Once approved, you can access your dashboard
4. From the dashboard, you can:
   - Add new price alerts
   - View your existing alerts
   - Enable/disable or remove alerts
   - Browse available tokens on Bybit

## Admin Commands

Admins can:
- Approve new users
- Block/unblock users
- View users' configured alerts
- Set up their own alerts (admins have all user capabilities)

## Architecture

The bot is built with:
- **aiogram**: For Telegram bot functionality
- **SQLAlchemy**: For database operations
- **aiohttp**: For asynchronous API calls to Bybit
- **loguru**: For logging

## Directory Structure

```
bybit-alert-bot/
├── app/
│   ├── handlers/       # Telegram message/command handlers
│   ├── keyboards/      # Telegram keyboard layouts
│   ├── models/         # Database models
│   ├── services/       # Business logic
│   ├── db/             # Database operations
│   ├── utils/          # Utilities
│   ├── bot.py          # Main bot logic
│   └── settings.py     # Bot settings and configuration
├── data/               # Database files
├── logs/               # Log files
├── main.py             # Entry point
├── Dockerfile          # Docker configuration
├── docker-compose.yml  # Docker Compose configuration
├── deploy.sh           # Deployment script
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For support or questions, contact [@Artem_Solovev](https://t.me/Artem_Solovev) on Telegram. 