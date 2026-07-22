#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hotmail Master Bot - Main Entry Point
Version: 7.7
Author: @VJF_X
Description: Advanced Hotmail/Outlook Multi-Tool Telegram Bot
"""

import os
import sys
import logging
import atexit
import signal
import asyncio
from datetime import datetime
from typing import List, Tuple

# Suppress SSL warnings early
import warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# Configure logging before imports
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Suppress urllib3 warnings
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("requests").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

# Configuration Constants
class Config:
    """Bot Configuration"""
    BOT_TOKEN = "8277508834:AAEkt2c1zlDfHqZGoxyksYk15jMynXK37Nc"
    
    ADMIN_IDS: List[int] = [
        6341905240,
    ]
    
    REQUIRED_CHANNELS: List[Tuple[str, str]] = [
        ("https://t.me/hotmailLis", "hotmailLis"),
    
    ]
    
    FORCE_CHANNEL_MEMBERSHIP: bool = True
    
    RESULTS_CHANNEL: tuple = ("https://t.me/hotmailLis", -1003813798706)
    RESULTS_CHANNEL_ENABLED: bool = True
    
    PREMIUM_DAILY_LIMIT: int = 10000
    MAX_THREADS: int = 30
    MAX_FILE_SIZE: int = 20 * 1024 * 1024
    MAX_LINES: int = 10000
    
    PREMIUM_DB_FILE: str = "premium_db.json"
    RESULTS_FOLDER: str = "results"
    TEMP_FOLDER: str = "temp"
    
    REQUEST_TIMEOUT: int = 15
    MAX_RETRIES: int = 3
    REQUEST_DELAY: float = 0.2

def setup_directories():
    for folder in [Config.RESULTS_FOLDER, Config.TEMP_FOLDER, "logs"]:
        if not os.path.exists(folder):
            os.makedirs(folder)
            logger.info(f"Created directory: {folder}")

PID_FILE = "bot.pid"

def cleanup_pid():
    try:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
            logger.info("PID file cleaned up")
    except Exception as e:
        logger.error(f"Error cleaning PID file: {e}")

def check_running():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                old_pid = int(f.read().strip())
            os.kill(old_pid, 0)
            logger.error(f"Another instance is running (PID: {old_pid})")
            sys.exit(1)
        except (OSError, ValueError):
            os.remove(PID_FILE)
            logger.warning("Removed stale PID file")
    
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))
    atexit.register(cleanup_pid)

def signal_handler(signum, frame):
    logger.info(f"Received signal {signum}, shutting down...")
    cleanup_pid()
    sys.exit(0)

def validate_config():
    if not Config.BOT_TOKEN or Config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("❌ BOT_TOKEN not configured! Please set your bot token in main.py")
        return False
    
    if not Config.ADMIN_IDS or Config.ADMIN_IDS == [123456789]:
        logger.warning("⚠️ ADMIN_IDS not properly configured!")
    
    if len(Config.BOT_TOKEN) < 20:
        logger.error("❌ BOT_TOKEN appears to be invalid (too short)")
        return False
    
    logger.info("[OK] Configuration validated successfully")
    return True

def print_banner():
    banner = """
    ======================================================
    
    HOTMAIL MASTER BOT v7.7
    
    Version 7.7 - Full Functional
    Author: @VJF_X
    
    ======================================================
    """
    print(banner)
    logger.info("Starting Hotmail Master Bot v7.7")

def main():
    try:
        print_banner()
        setup_directories()
        
        if not validate_config():
            sys.exit(1)
        
        check_running()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        from bot_handlers import HotmailMasterBot
        
        logger.info("Initializing bot components...")
        bot = HotmailMasterBot(
            token=Config.BOT_TOKEN,
            admin_ids=Config.ADMIN_IDS,
            channels=Config.REQUIRED_CHANNELS
        )
        
        logger.info("[RUNNING] Bot is now running! Press Ctrl+C to stop.")
        bot.run()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.exception(f"Fatal error in main: {e}")
        sys.exit(1)
    finally:
        cleanup_pid()

if __name__ == "__main__":
    main()
