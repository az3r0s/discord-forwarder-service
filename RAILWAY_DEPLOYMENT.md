# Railway Deployment Guide - Production Discord Forwarder

## Quick Deployment Steps

### 1. Install Railway CLI (if not already installed)
```powershell
npm install -g @railway/cli
```

### 2. Login to Railway
```powershell
railway login
```

### 3. Initialize Project
```powershell
# Navigate to the service directory
cd "c:\Users\aidan\OneDrive\Desktop\Zinrai\Discord\microservices\discord-forwarder-service"

# Initialize Railway project
railway init
```

### 4. Deploy the Service
```powershell
# Deploy all files to Railway
railway up
```

### 5. Upload Session Files (Critical!)
The Telegram session files need to be uploaded manually:
- `discord_bot_session.session`
- `discord_bot_session.session-journal`

**Upload via Railway Dashboard:**
1. Go to https://railway.app/dashboard
2. Select your project
3. Go to "Files" tab
4. Upload the session files

### 6. Monitor Deployment
```powershell
# Watch logs in real-time
railway logs --follow

# Check service status
railway status

# View environment variables
railway variables
```

## Files Being Deployed

✅ **Core Application**
- `production_forwarder.py` - Main service
- `config.json` - Configuration
- `requirements.txt` - Dependencies
- `Procfile` - Railway startup command

✅ **Session Files** (Upload manually)
- `discord_bot_session.session`
- `discord_bot_session.session-journal`

## Expected Behavior After Deployment

🟢 **Service Startup**
```
INFO - Starting Production Discord Forwarder Service...
INFO - Connected to Telegram
INFO - Discord Forwarder Service connected as Signal Bot#3279
INFO - 🚀 Production Forwarder Service is running!
INFO - 📊 Signal tracking: 1 in 10 forwarded to free channel
```

🟢 **Message Processing**
```
INFO - Processing trading_signal message: BUY @ 3373/3371...
INFO - Forwarded signal #127 to VIP channel only
INFO - Forwarded signal #130 to both VIP and FREE channels
```

🟢 **Database Operations**
- `persistent_message_mapping.db` automatically created
- Message relationships stored persistently
- Signal counter resumes from last number

## Monitoring Commands

```powershell
# Real-time logs
railway logs --follow

# Recent logs
railway logs

# Service restart (if needed)
railway service restart

# Check resource usage
railway status

# Update environment variables
railway variables set KEY=VALUE
```

## Troubleshooting

**If service fails to start:**
1. Check logs: `railway logs`
2. Verify session files are uploaded
3. Check config.json is properly formatted
4. Restart service: `railway service restart`

**If Telegram authentication fails:**
- Re-upload session files via dashboard
- Check phone number in config.json matches session

**If Discord connection fails:**
- Verify bot token in config.json
- Check bot permissions in Discord servers

## Success Indicators

✅ Both Telegram and Discord connections established
✅ Channel IDs resolved successfully  
✅ Database file created
✅ Message processing starts automatically
✅ Signal counter initialized

## Ready for 24/7 Operation! 🚀

The service will now:
- Process all messages with 100% accuracy
- Forward 1-in-10 signals to free channel
- Handle weekly recaps with dual posting
- Maintain persistent message tracking
- Recover gracefully from any restarts
