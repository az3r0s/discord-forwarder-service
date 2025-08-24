# Discord Forwarder Service

**Purpose**: Listen to Telegram channels and forward messages to Discord with smart routing.

**Hosting**: Railway (FREE tier)

**Dependencies**: Telegram API only

## 🎯 **Service Responsibilities**

- ✅ Telegram client listening
- ✅ Message parsing and filtering
- ✅ Discord channel forwarding  
- ✅ Analysis message detection and routing
- ✅ Signal preprocessing and formatting
- ❌ NO Discord commands (handled by UI service)
- ❌ NO Copy trading logic (handled by copy trading service)

## 🚀 **Quick Deploy to Railway**

1. **Setup Telegram API:**
   - Get API credentials from https://my.telegram.org
   - Create a Telegram bot via @BotFather
   - Add bot to your channel

2. **Deploy to Railway:**
   ```bash
   git init
   git add .
   git commit -m "Discord Forwarder Service"
   git remote add origin https://github.com/yourusername/discord-forwarder-service.git
   git push -u origin main
   ```

3. **Configure Railway:**
   - Connect GitHub repository
   - Add environment variables from `.env`
   - Deploy!

## 📋 **Environment Variables**

```env
# Telegram API (REQUIRED)
TELEGRAM_API_ID=your_telegram_api_id
TELEGRAM_API_HASH=your_telegram_api_hash
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHANNEL_ID=your_telegram_channel_id

# Discord API (REQUIRED)
DISCORD_TOKEN=your_discord_bot_token
SIGNALS_CHANNEL_ID=your_signals_channel_id
VIP_ANALYSIS_CHANNEL_ID=your_vip_analysis_channel_id

# Features
ENABLE_ANALYSIS_ROUTING=true
ENABLE_SIGNAL_FILTERING=true
LOG_LEVEL=INFO
```

## 🔧 **Local Development**

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.template .env
# Edit .env with your values

# Run the service
python main.py
```

## 📡 **Message Processing**

### Signal Forwarding
- All trading signals → `#signals` channel
- Real-time message forwarding
- Preserves formatting and media

### Analysis Routing  
- Daily analysis videos → `#vip-analysis` channel
- Detection based on date patterns
- Smart content filtering

### Message Filtering
- Spam detection and filtering
- Duplicate message prevention
- Format standardization

## 🔗 **Service Communication**

This service operates independently:
- **Input:** Telegram API (direct listening)
- **Output:** Discord API (message forwarding)
- **No dependencies** on other microservices

## 🛡️ **Security Features**

- Telegram session management
- Rate limiting for Discord API
- Error handling and auto-retry
- Secure token storage

## 📈 **Performance**

Railway free tier handles:
- 1000+ messages/day easily
- Real-time forwarding (<1 second delay)
- Auto-restart on errors
- Memory-efficient operation

Perfect for message forwarding without any MT5 overhead!
