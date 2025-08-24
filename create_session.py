"""
Session Creator for Discord Forwarder Service
Run this locally to create a Telegram session file for Railway deployment
"""

import asyncio
import os
from telethon import TelegramClient

# Your Telegram credentials
API_ID = 11855685
API_HASH = "cc0d72cd0cdcbbfea6228b078199bea5"
PHONE_NUMBER = "+447393819476"
SESSION_NAME = "forwarder_session"

async def create_session():
    """Create a Telegram session file for Railway deployment"""
    
    print("🔄 Creating Telegram session for Railway deployment...")
    
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    
    try:
        await client.start(phone=PHONE_NUMBER)
        print("✅ Session created successfully!")
        print(f"📁 Session file: {SESSION_NAME}.session")
        print(f"📁 Session journal: {SESSION_NAME}.session-journal")
        
        # Test the connection
        me = await client.get_me()
        print(f"👤 Logged in as: {me.first_name} {me.last_name or ''}")
        
        # Get channel info
        try:
            channel = await client.get_entity(-2796363074)
            print(f"📡 Can access channel: {channel.title}")
        except Exception as e:
            print(f"⚠️ Channel access issue: {e}")
        
        print("\n🚀 Next steps:")
        print("1. Upload the .session file to Railway as a file")
        print("2. Update Railway environment variables")
        print("3. Redeploy the service")
        
    except Exception as e:
        print(f"❌ Error creating session: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(create_session())
