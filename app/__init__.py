"""
Bybit Price Alert Bot

A Telegram bot for tracking cryptocurrency prices on Bybit exchange
and sending alerts when prices cross specified thresholds.
"""
import os
from pathlib import Path

# Create necessary directories
data_dir = Path('data')
logs_dir = Path('logs')

if not data_dir.exists():
    os.makedirs(data_dir, exist_ok=True)

if not logs_dir.exists():
    os.makedirs(logs_dir, exist_ok=True)

__version__ = "1.0.0" 