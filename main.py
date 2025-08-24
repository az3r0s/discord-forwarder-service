"""
Discord Forwarder Service - Telegram to Discord Message Forwarding
Optimized for Railway deployment (FREE tier)
Handles signal forwarding and analysis routing
"""

import discord
from discord.ext import commands
import asyncio
import logging
import json
import os
import re
from typing import Optional, Dict, Any
from datetime import datetime
from telethon import TelegramClient, events
from telethon.tl.types import Channel, User, MessageMediaPhoto, MessageMediaDocument

# Import shared utilities (embedded for Railway deployment)
import sys
import os
import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any

class ServiceType(Enum):
    DISCORD_UI = "discord-ui"
    DISCORD_FORWARDER = "discord-forwarder"  
    COPY_TRADING = "copy-trading"

@dataclass
class ServiceConfig:
    """Shared configuration for all services"""
    # Discord
    discord_token: str
    signals_channel_id: str
    vip_analysis_channel_id: str
    
    # Telegram (using phone authentication like main bot)
    telegram_api_id: str
    telegram_api_hash: str
    telegram_phone_number: str
    telegram_channel_id: str
    
    # Feature Flags
    enable_analysis_routing: bool = True
    enable_performance_monitoring: bool = True
    
    @classmethod
    def from_env(cls) -> 'ServiceConfig':
        """Load configuration from environment variables"""
        return cls(
            # Discord
            discord_token=os.getenv('DISCORD_TOKEN', ''),
            signals_channel_id=os.getenv('SIGNALS_CHANNEL_ID', ''),
            vip_analysis_channel_id=os.getenv('VIP_ANALYSIS_CHANNEL_ID', ''),
            
            # Telegram (phone authentication)
            telegram_api_id=os.getenv('TELEGRAM_API_ID', ''),
            telegram_api_hash=os.getenv('TELEGRAM_API_HASH', ''),
            telegram_phone_number=os.getenv('TELEGRAM_PHONE_NUMBER', ''),
            telegram_channel_id=os.getenv('TELEGRAM_CHANNEL_ID', ''),
            
            # Feature Flags
            enable_analysis_routing=os.getenv('ENABLE_ANALYSIS_ROUTING', 'true').lower() == 'true',
            enable_performance_monitoring=os.getenv('ENABLE_PERFORMANCE_MONITORING', 'true').lower() == 'true',
        )

def setup_logging(service_type: ServiceType, log_level: str = "INFO"):
    """Setup logging for a specific service"""
    
    # Create service-specific logger
    logger = logging.getLogger(f"discord-bot.{service_type.value}")
    
    # Set log level
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Create formatter
    formatter = logging.Formatter(
        f'%(asctime)s - {service_type.value} - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Prevent duplicate logs
    logger.propagate = False
    
    return logger

def is_analysis_message(text: str) -> bool:
    """Check if a message contains daily analysis based on date patterns"""
    
    # Pattern for date formats like "210825", "25/08/21", "Aug 25", etc.
    date_patterns = [
        r'\b\d{6}\b',  # 210825 format
        r'\b\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}\b',  # Date separators
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\b',  # Month names
        r'\banalysis\b',  # Direct analysis mention
        r'\bdaily\b.*\breview\b',  # Daily review
        r'\bmarket\b.*\bupdate\b',  # Market update
    ]
    
    text_lower = text.lower()
    return any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in date_patterns)

async def health_check(service_type: ServiceType):
    """Generic health check for any service"""
    import psutil
    import time
    
    return {
        "service": service_type.value,
        "status": "healthy",
        "timestamp": time.time(),
        "memory_usage": psutil.virtual_memory().percent,
        "cpu_usage": psutil.cpu_percent(interval=1),
        "uptime": time.time() - psutil.boot_time()
    }

class RateLimiter:
    """Simple rate limiter for API calls"""
    
    def __init__(self, max_calls: int, time_window: int):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    async def acquire(self) -> bool:
        """Check if we can make another API call"""
        import time
        
        now = time.time()
        
        # Remove old calls outside the time window
        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
        
        # Check if we're under the limit
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        
        return False

# Setup logging
logger = setup_logging(ServiceType.DISCORD_FORWARDER)

# Load configuration
config = ServiceConfig.from_env()

# Discord bot setup (for sending messages only)
intents = discord.Intents.default()
intents.message_content = True
discord_bot = commands.Bot(command_prefix='!forwarder_', intents=intents)

# Telegram client setup (using phone authentication like your main bot)
telegram_client = TelegramClient(
    'forwarder_session',
    config.telegram_api_id,
    config.telegram_api_hash
)

# Rate limiters
discord_rate_limiter = RateLimiter(max_calls=50, time_window=60)  # 50 messages per minute
telegram_rate_limiter = RateLimiter(max_calls=30, time_window=60)  # 30 requests per minute

# Message tracking to prevent duplicates
processed_messages = set()
MAX_TRACKED_MESSAGES = 1000

class MessageProcessor:
    """Process and format messages for Discord forwarding"""
    
    @staticmethod
    def clean_message_text(text: str) -> str:
        """Clean and format message text for Discord"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Limit message length for Discord
        if len(text) > 1900:  # Leave room for embeds
            text = text[:1897] + "..."
        
        return text.strip()
    
    @staticmethod
    def extract_signal_info(text: str) -> Dict[str, Any]:
        """Extract trading signal information from message"""
        signal_info = {
            "symbol": None,
            "action": None,
            "entry": None,
            "stop_loss": None,
            "take_profit": None,
            "risk": None
        }
        
        text_upper = text.upper()
        
        # Extract symbol (common forex pairs)
        symbol_patterns = [
            r'\b(EUR/USD|GBP/USD|USD/JPY|USD/CHF|AUD/USD|USD/CAD|NZD/USD)\b',
            r'\b(EUR/GBP|EUR/JPY|GBP/JPY|CHF/JPY|AUD/JPY|CAD/JPY)\b',
            r'\b(XAU/USD|XAG/USD|WTI|BRENT)\b',  # Gold, Silver, Oil
            r'\b([A-Z]{3}/[A-Z]{3})\b'  # Generic forex pattern
        ]
        
        for pattern in symbol_patterns:
            match = re.search(pattern, text_upper)
            if match:
                signal_info["symbol"] = match.group(1)
                break
        
        # Extract action (BUY/SELL)
        if re.search(r'\b(BUY|LONG)\b', text_upper):
            signal_info["action"] = "BUY"
        elif re.search(r'\b(SELL|SHORT)\b', text_upper):
            signal_info["action"] = "SELL"
        
        # Extract prices
        price_patterns = {
            "entry": r'\b(?:ENTRY|BUY|SELL)[\s:]*([0-9]+\.?[0-9]*)\b',
            "stop_loss": r'\b(?:SL|STOP[\s\-]?LOSS)[\s:]*([0-9]+\.?[0-9]*)\b',
            "take_profit": r'\b(?:TP|TAKE[\s\-]?PROFIT)[\s:]*([0-9]+\.?[0-9]*)\b'
        }
        
        for key, pattern in price_patterns.items():
            match = re.search(pattern, text_upper)
            if match:
                try:
                    signal_info[key] = float(match.group(1))
                except ValueError:
                    pass
        
        return signal_info
    
    @staticmethod
    def format_signal_embed(text: str, signal_info: Dict[str, Any], media_type: str = None) -> discord.Embed:
        """Create a formatted embed for trading signals"""
        
        # Determine embed color based on action
        color = 0x00ff00 if signal_info["action"] == "BUY" else 0xff0000 if signal_info["action"] == "SELL" else 0x3498db
        
        embed = discord.Embed(
            title="📈 Trading Signal",
            description=MessageProcessor.clean_message_text(text),
            color=color,
            timestamp=datetime.now()
        )
        
        # Add signal details if extracted
        if signal_info["symbol"]:
            embed.add_field(name="📊 Symbol", value=signal_info["symbol"], inline=True)
        
        if signal_info["action"]:
            action_emoji = "🟢" if signal_info["action"] == "BUY" else "🔴"
            embed.add_field(name="⚡ Action", value=f"{action_emoji} {signal_info['action']}", inline=True)
        
        if signal_info["entry"]:
            embed.add_field(name="🎯 Entry", value=str(signal_info["entry"]), inline=True)
        
        if signal_info["stop_loss"]:
            embed.add_field(name="🛑 Stop Loss", value=str(signal_info["stop_loss"]), inline=True)
        
        if signal_info["take_profit"]:
            embed.add_field(name="💰 Take Profit", value=str(signal_info["take_profit"]), inline=True)
        
        # Add media indicator
        if media_type:
            embed.add_field(name="📎 Media", value=f"Contains {media_type}", inline=True)
        
        embed.set_footer(text="Signal Forwarder • Real-time from Telegram")
        return embed

    @staticmethod
    def format_analysis_embed(text: str, media_type: str = None) -> discord.Embed:
        """Create a formatted embed for analysis messages"""
        
        embed = discord.Embed(
            title="📊 Market Analysis",
            description=MessageProcessor.clean_message_text(text),
            color=0xffd700,
            timestamp=datetime.now()
        )
        
        # Add VIP indicator
        embed.add_field(name="⭐ Access Level", value="VIP Analysis", inline=True)
        
        # Add media indicator
        if media_type:
            embed.add_field(name="📎 Content", value=f"Includes {media_type}", inline=True)
        
        embed.set_footer(text="VIP Analysis • Exclusive Content")
        return embed

async def get_discord_channel(channel_id: str) -> Optional[discord.TextChannel]:
    """Get Discord channel by ID"""
    try:
        channel = discord_bot.get_channel(int(channel_id))
        if not channel:
            # Try fetching if not in cache
            channel = await discord_bot.fetch_channel(int(channel_id))
        return channel
    except Exception as e:
        logger.error(f"Error getting Discord channel {channel_id}: {e}")
        return None

async def forward_to_discord(text: str, media_type: str = None, is_analysis: bool = False) -> bool:
    """Forward message to appropriate Discord channel"""
    
    try:
        # Check rate limiting
        if not await discord_rate_limiter.acquire():
            logger.warning("Discord rate limit exceeded, skipping message")
            return False
        
        # Determine target channel
        target_channel_id = config.vip_analysis_channel_id if is_analysis else config.signals_channel_id
        channel = await get_discord_channel(target_channel_id)
        
        if not channel:
            logger.error(f"Could not access Discord channel: {target_channel_id}")
            return False
        
        if is_analysis:
            # Format as analysis
            embed = MessageProcessor.format_analysis_embed(text, media_type)
            await channel.send(embed=embed)
            logger.info(f"Forwarded analysis message to {channel.name}")
        else:
            # Format as trading signal
            signal_info = MessageProcessor.extract_signal_info(text)
            embed = MessageProcessor.format_signal_embed(text, signal_info, media_type)
            await channel.send(embed=embed)
            logger.info(f"Forwarded signal to {channel.name}")
        
        return True
        
    except discord.Forbidden:
        logger.error("Bot lacks permission to send messages to Discord channel")
        return False
    except discord.HTTPException as e:
        logger.error(f"Discord HTTP error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error forwarding to Discord: {e}")
        return False

async def process_telegram_message(event) -> None:
    """Process incoming Telegram message"""
    
    try:
        message = event.message
        
        # Create unique message ID to prevent duplicates
        message_id = f"{message.chat_id}_{message.id}"
        
        if message_id in processed_messages:
            return
        
        # Add to processed set (with size limit)
        processed_messages.add(message_id)
        if len(processed_messages) > MAX_TRACKED_MESSAGES:
            # Remove oldest 100 messages
            for _ in range(100):
                processed_messages.pop()
        
        # Check rate limiting
        if not await telegram_rate_limiter.acquire():
            logger.warning("Telegram rate limit exceeded, skipping message")
            return
        
        # Get message text
        text = message.message or ""
        
        # Skip empty messages
        if not text.strip():
            logger.debug("Skipping empty message")
            return
        
        # Determine media type
        media_type = None
        if message.media:
            if isinstance(message.media, MessageMediaPhoto):
                media_type = "Image"
            elif isinstance(message.media, MessageMediaDocument):
                if message.media.document.mime_type.startswith('video/'):
                    media_type = "Video"
                elif message.media.document.mime_type.startswith('audio/'):
                    media_type = "Audio"
                else:
                    media_type = "Document"
        
        # Check if this is an analysis message
        is_analysis = is_analysis_message(text)
        
        # Forward to Discord
        success = await forward_to_discord(text, media_type, is_analysis)
        
        if success:
            message_type = "analysis" if is_analysis else "signal"
            logger.info(f"Successfully processed {message_type} message: {text[:50]}...")
        else:
            logger.warning(f"Failed to forward message: {text[:50]}...")
    
    except Exception as e:
        logger.error(f"Error processing Telegram message: {e}")

@discord_bot.event
async def on_ready():
    """Discord bot ready event"""
    logger.info(f'Discord Forwarder Service connected as {discord_bot.user}')
    logger.info(f'Monitoring signals channel: {config.signals_channel_id}')
    logger.info(f'Monitoring VIP analysis channel: {config.vip_analysis_channel_id}')

@telegram_client.on(events.NewMessage)
async def telegram_message_handler(event):
    """Handle new Telegram messages"""
    # Only process messages from the configured channel
    if str(event.chat_id) == str(config.telegram_channel_id):
        await process_telegram_message(event)

# Health check command
@discord_bot.command()
async def forwarder_health(ctx):
    """Health check for forwarder service"""
    try:
        health_data = await health_check(ServiceType.DISCORD_FORWARDER)
        
        embed = discord.Embed(
            title="🏥 Forwarder Service Health",
            color=0x2ecc71,
            timestamp=datetime.now()
        )
        
        # Service status
        telegram_status = "🟢 Connected" if telegram_client.is_connected() else "🔴 Disconnected"
        discord_status = "🟢 Connected" if discord_bot.is_ready() else "🔴 Disconnected"
        
        embed.add_field(
            name="📡 Connections",
            value=f"**Telegram:** {telegram_status}\n**Discord:** {discord_status}",
            inline=True
        )
        
        embed.add_field(
            name="📊 Performance",
            value=f"**Memory:** {health_data['memory_usage']:.1f}%\n**CPU:** {health_data['cpu_usage']:.1f}%",
            inline=True
        )
        
        embed.add_field(
            name="📈 Statistics",
            value=f"**Messages Processed:** {len(processed_messages)}\n**Uptime:** {str(datetime.fromtimestamp(health_data['uptime'])).split('.')[0]}",
            inline=True
        )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Health check error: {str(e)}")

async def start_services():
    """Start both Telegram and Discord services"""
    
    try:
        # Start Telegram client (using phone number like your main bot)
        logger.info("Starting Telegram client...")
        await telegram_client.start(phone=config.telegram_phone_number)
        logger.info("Telegram client connected successfully")
        
        # Start Discord bot
        logger.info("Starting Discord bot...")
        await discord_bot.start(config.discord_token)
        
    except Exception as e:
        logger.error(f"Error starting services: {e}")
        raise

async def main():
    """Main service entry point"""
    
    try:
        # Validate configuration
        if not config.telegram_api_id or not config.telegram_api_hash:
            logger.error("Telegram API credentials are required")
            return
        
        if not config.discord_token:
            logger.error("Discord token is required")
            return
        
        if not config.telegram_channel_id:
            logger.error("Telegram channel ID is required")
            return
        
        # Start services
        await start_services()
        
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
    except Exception as e:
        logger.error(f"Service error: {e}")
    finally:
        # Cleanup
        if telegram_client.is_connected():
            await telegram_client.disconnect()
        if not discord_bot.is_closed():
            await discord_bot.close()

if __name__ == "__main__":
    try:
        logger.info("Starting Discord Forwarder Service...")
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Failed to start service: {e}")
        exit(1)
