"""
Example Messaging Agent Implementation
This is a template for adding SMS/WhatsApp functionality to Emese V2

To use:
1. Install: pip install twilio
2. Rename this file to messaging_agent.py
3. Add credentials to .env file
4. Follow integration steps in SYSTEM_ANALYSIS.md
"""

import asyncio
from typing import Optional, List, Dict
import os
from dotenv import load_dotenv

load_dotenv()

# Try to import Twilio (install with: pip install twilio)
try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    print("[MESSAGING] Warning: twilio not installed. Install with: pip install twilio")


class MessagingAgent:
    """
    Handles SMS and WhatsApp messaging via Twilio.
    
    Required .env variables:
    - TWILIO_ACCOUNT_SID
    - TWILIO_AUTH_TOKEN
    - TWILIO_PHONE_NUMBER (your Twilio phone number)
    """
    
    def __init__(self):
        if not TWILIO_AVAILABLE:
            self.client = None
            print("[MESSAGING] Twilio not available")
            return
        
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_PHONE_NUMBER")
        
        if account_sid and auth_token:
            self.client = TwilioClient(account_sid, auth_token)
            print("[MESSAGING] Twilio client initialized")
        else:
            self.client = None
            print("[MESSAGING] Warning: Twilio credentials not set in .env")
    
    async def send_sms(self, to: str, message: str) -> bool:
        """
        Send an SMS message.
        
        Args:
            to: Recipient phone number (E.164 format: +1234567890)
            message: Message text
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.client:
            print("[MESSAGING] Error: Twilio client not initialized")
            return False
        
        if not self.from_number:
            print("[MESSAGING] Error: TWILIO_PHONE_NUMBER not set")
            return False
        
        try:
            # Use asyncio.to_thread for blocking Twilio API call
            msg = await asyncio.to_thread(
                self._send_sms_sync, to, message
            )
            
            if msg and msg.sid:
                print(f"[MESSAGING] SMS sent to {to} (SID: {msg.sid})")
                return True
            else:
                print(f"[MESSAGING] Failed to send SMS to {to}")
                return False
        except Exception as e:
            print(f"[MESSAGING] Error sending SMS: {e}")
            return False
    
    def _send_sms_sync(self, to: str, message: str):
        """Synchronous SMS send (runs in thread)."""
        return self.client.messages.create(
            body=message,
            from_=self.from_number,
            to=to
        )
    
    async def send_whatsapp(self, to: str, message: str) -> bool:
        """
        Send a WhatsApp message via Twilio.
        
        Args:
            to: Recipient WhatsApp number (E.164 format: +1234567890)
            message: Message text
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.client:
            print("[MESSAGING] Error: Twilio client not initialized")
            return False
        
        # Twilio WhatsApp format: whatsapp:+1234567890
        whatsapp_from = f"whatsapp:{self.from_number}" if self.from_number else None
        whatsapp_to = f"whatsapp:{to}"
        
        if not whatsapp_from:
            print("[MESSAGING] Error: TWILIO_PHONE_NUMBER not set")
            return False
        
        try:
            msg = await asyncio.to_thread(
                self._send_whatsapp_sync, whatsapp_to, message, whatsapp_from
            )
            
            if msg and msg.sid:
                print(f"[MESSAGING] WhatsApp sent to {to} (SID: {msg.sid})")
                return True
            else:
                print(f"[MESSAGING] Failed to send WhatsApp to {to}")
                return False
        except Exception as e:
            print(f"[MESSAGING] Error sending WhatsApp: {e}")
            return False
    
    def _send_whatsapp_sync(self, to: str, message: str, from_: str):
        """Synchronous WhatsApp send (runs in thread)."""
        return self.client.messages.create(
            body=message,
            from_=from_,
            to=to
        )
    
    async def get_messages(self, limit: int = 10) -> List[Dict]:
        """
        Get recent messages (SMS/WhatsApp) received.
        
        Args:
            limit: Maximum number of messages to retrieve
        
        Returns:
            List of message dicts with keys: from, to, body, date
        """
        if not self.client:
            print("[MESSAGING] Error: Twilio client not initialized")
            return []
        
        try:
            messages = await asyncio.to_thread(
                self._get_messages_sync, limit
            )
            return messages
        except Exception as e:
            print(f"[MESSAGING] Error getting messages: {e}")
            return []
    
    def _get_messages_sync(self, limit: int) -> List[Dict]:
        """Synchronous message retrieval (runs in thread)."""
        messages = []
        
        try:
            # Get messages sent to our number
            twilio_messages = self.client.messages.list(limit=limit)
            
            for msg in twilio_messages:
                messages.append({
                    "from": msg.from_,
                    "to": msg.to,
                    "body": msg.body,
                    "date": str(msg.date_sent),
                    "status": msg.status
                })
        except Exception as e:
            print(f"[MESSAGING] Error retrieving messages: {e}")
        
        return messages


# Alternative: Discord Bot Example
class DiscordAgent:
    """
    Alternative messaging agent using Discord.
    Requires discord.py library.
    """
    
    def __init__(self):
        self.bot_token = os.getenv("DISCORD_BOT_TOKEN")
        # Implementation would use discord.py
        # See: https://discordpy.readthedocs.io/
        pass


# Standalone test
if __name__ == "__main__":
    async def test():
        agent = MessagingAgent()
        
        # Test SMS (uncomment to test)
        # success = await agent.send_sms(
        #     to="+1234567890",  # Replace with real number
        #     message="Test SMS from Emese"
        # )
        # print(f"SMS result: {success}")
        
        # Test WhatsApp (uncomment to test)
        # success = await agent.send_whatsapp(
        #     to="+1234567890",  # Replace with real number
        #     message="Test WhatsApp from Emese"
        # )
        # print(f"WhatsApp result: {success}")
        
        # Test get messages
        # messages = await agent.get_messages(limit=5)
        # print(f"Found {len(messages)} messages")
        # for m in messages:
        #     print(f"  - From {m['from']}: {m['body'][:50]}")
    
    asyncio.run(test())

