# TARS V2 System Analysis

## 📋 Table of Contents
1. [System Architecture Overview](#system-architecture-overview)
2. [Task Processing Flow](#task-processing-flow)
3. [What Works](#what-works)
4. [What Doesn't Work / Issues](#what-doesnt-work--issues)
5. [API Keys Required](#api-keys-required)
6. [How to Add New Features (Email/Messaging)](#how-to-add-new-features-emailmessaging)

---

## System Architecture Overview

### Core Components

**Backend (Python 3.11 + FastAPI)**
- `server.py` - FastAPI + Socket.IO server (main entry point)
- `TARS.py` - Gemini Live API integration, audio loop, tool orchestration
- `cad_agent.py` - 3D CAD generation using build123d
- `web_agent.py` - Browser automation using Playwright + Gemini Computer Use
- `printer_agent.py` - 3D printer discovery, slicing, print job management
- `kasa_agent.py` - TP-Link Kasa smart home device control
- `authenticator.py` - Face recognition using MediaPipe
- `project_manager.py` - Project context and file management
- `tools.py` - Tool definitions for Gemini function calling

**Frontend (React + Electron)**
- React components for UI (Chat, CAD viewer, Browser, Printer, etc.)
- Socket.IO client for real-time communication
- Three.js for 3D model visualization
- MediaPipe for hand gesture tracking

### Communication Flow

```
User Voice/Text → Frontend → Socket.IO → server.py → TARS.py → Gemini API
                                                              ↓
                                                         Tool Calls
                                                              ↓
                    ┌──────────┬──────────┬──────────┬──────────┐
                    │          │          │          │          │
                 CAD Agent  Web Agent  Printer  Kasa Agent  File Ops
                    │          │          │          │          │
                    └──────────┴──────────┴──────────┴──────────┘
                              ↓
                    Results sent back via Socket.IO → Frontend
```

---

## Task Processing Flow

### 1. **Voice/Text Input**
- User speaks or types → Frontend captures
- Sent via Socket.IO `user_input` event to `server.py`
- `server.py` forwards to `TARS.py` AudioLoop session
- Gemini processes with transcription enabled

### 2. **Tool Call Detection**
- Gemini analyzes user request
- Determines which tool(s) to call from available tools list
- Tools defined in `TARS.py` (lines 40-183) and `tools.py`

### 3. **Permission Check**
- System checks `SETTINGS["tool_permissions"]` for the tool
- If `True` (default), requires user confirmation
- If `False`, auto-executes
- Confirmation handled via `on_tool_confirmation` callback

### 4. **Tool Execution**
- Tool handler in `TARS.py` `receive_audio()` method (lines 808-1202)
- Each tool has specific handler:
  - `generate_cad` → `handle_cad_request()` → `cad_agent.generate_prototype()`
  - `run_web_agent` → `handle_web_agent_request()` → `web_agent.run_task()`
  - `write_file` → `handle_write_file()` → writes to project directory
  - `control_light` → `kasa_agent.turn_on/off/set_color()`
  - `print_stl` → `printer_agent.print_stl()` → slice → upload → print

### 5. **Result Handling**
- Tool returns result
- Result sent back to Gemini via `FunctionResponse`
- Gemini generates audio/text response
- Response streamed to frontend via Socket.IO

### 6. **Project Context**
- All operations scoped to current project (default: "temp")
- Files saved to `projects/{project_name}/cad/` or root
- Chat history logged to `projects/{project_name}/chat_history.jsonl`

---

## What Works

### ✅ **Fully Functional**

1. **Voice Interaction**
   - Real-time audio streaming to Gemini 2.5 Native Audio
   - Voice Activity Detection (VAD) for video frame sending
   - Interrupt handling (stops AI speech when user speaks)
   - Transcription streaming to frontend

2. **3D CAD Generation**
   - Uses Gemini 3 Pro to generate build123d Python scripts
   - Executes scripts locally to generate STL files
   - Retry logic (3 attempts) with error feedback
   - Streaming thoughts during generation
   - Saves to project directory with timestamps

3. **Web Agent**
   - Playwright browser automation
   - Gemini Computer Use model for autonomous navigation
   - Screenshot streaming to frontend
   - Handles clicks, typing, scrolling, navigation

4. **3D Printing**
   - mDNS discovery of printers (Moonraker, OctoPrint)
   - Auto-detection of OrcaSlicer profiles
   - STL slicing with progress callbacks
   - G-code upload and print job start
   - Real-time print status monitoring

5. **Smart Home (Kasa)**
   - Device discovery on local network
   - Turn on/off, brightness, color control
   - Device state caching
   - Settings persistence

6. **Project Management**
   - Project creation and switching
   - File organization (cad/, browser/ folders)
   - Chat history logging
   - Context gathering for AI

7. **Face Authentication**
   - MediaPipe face landmarker
   - Local processing (no cloud)
   - Reference image matching
   - Optional (can be disabled in settings)

8. **File Operations**
   - Read/write files in project directory
   - Directory listing
   - Auto-project creation if stuck in "temp"

---

## What Doesn't Work / Issues

### ⚠️ **Known Issues**

1. **Duplicate Confirmation Logic** (TARS.py lines 859-869)
   - There's duplicate `if not confirmed:` check
   - Second check is unreachable (dead code)

2. **Video Frame Handling**
   - VAD sends frames on speech detection
   - But video mode can be "none" - frames may not be captured
   - `get_frames()` only runs if `video_mode == "camera"`

3. **Error Handling**
   - Some tool failures don't properly notify user
   - Web agent errors may not surface clearly
   - Printer discovery can hang on network issues

4. **Settings Persistence**
   - Settings saved to `backend/settings.json`
   - But some state (like device cache) not fully persisted
   - Kasa devices need re-discovery on restart

5. **Windows Path Handling**
   - Some path operations may fail on Windows
   - Backslash escaping in CAD scripts (partially handled)

6. **Memory Management**
   - Long chat sessions may accumulate context
   - No automatic context trimming
   - Project context can get large

7. **Tool Permission Defaults**
   - Default is `True` (require confirmation)
   - But many tools in settings.json are `False`
   - Inconsistency in behavior

8. **Audio Queue Clearing**
   - `clear_audio_queue()` may not fully stop playback
   - Race conditions possible during interruption

9. **Reconnection Logic**
   - Auto-reconnect on connection loss
   - But may lose some context during reconnection
   - Chat history restoration works but may be incomplete

10. **Slicer Detection**
    - OrcaSlicer path detection may fail on non-standard installs
    - Profile matching could be more robust
    - No fallback if slicer not found

---

## API Keys Required

### 🔑 **Currently Required**

1. **GEMINI_API_KEY** (Required)
   - Location: `.env` file in project root
   - Used for:
     - Voice interaction (Gemini 2.5 Native Audio)
     - CAD generation (Gemini 3 Pro)
     - Web agent (Gemini 2.5 Computer Use)
   - How to get: https://aistudio.google.com/app/apikey
   - Status: ✅ **MUST BE SET** - system won't work without it

### 🔑 **Not Currently Required (But Could Be Added)**

- **Email API Keys** (for email feature):
  - Gmail: OAuth2 credentials
  - SMTP: Server credentials
  - SendGrid/Mailgun: API keys

- **Messaging API Keys** (for messaging feature):
  - Twilio: Account SID + Auth Token
  - WhatsApp Business API: Access Token
  - Discord: Bot Token
  - Slack: Bot Token

---

## How to Add New Features (Email/Messaging)

### Step-by-Step Guide

### **1. Create Agent Module**

Create `backend/email_agent.py`:

```python
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
import os
from dotenv import load_dotenv

load_dotenv()

class EmailAgent:
    def __init__(self):
        # Load credentials from .env
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_address = os.getenv("EMAIL_ADDRESS")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        
    async def send_email(self, to: str, subject: str, body: str, 
                        is_html: bool = False) -> bool:
        """Send an email."""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = to
            msg['Subject'] = subject
            
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Use asyncio.to_thread for blocking SMTP
            await asyncio.to_thread(self._send_sync, msg, to)
            return True
        except Exception as e:
            print(f"[EMAIL] Error: {e}")
            return False
    
    def _send_sync(self, msg, to):
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.email_address, self.email_password)
            server.send_message(msg)
    
    async def read_emails(self, limit: int = 10) -> List[dict]:
        """Read recent emails (requires IMAP)."""
        # Implementation using imaplib
        pass
```

### **2. Add Tool Definitions**

In `TARS.py`, add tool definitions (around line 183):

```python
send_email_tool = {
    "name": "send_email",
    "description": "Sends an email to a recipient.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "to": {"type": "STRING", "description": "Recipient email address"},
            "subject": {"type": "STRING", "description": "Email subject"},
            "body": {"type": "STRING", "description": "Email body content"}
        },
        "required": ["to", "subject", "body"]
    }
}

read_emails_tool = {
    "name": "read_emails",
    "description": "Reads recent emails from inbox.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "limit": {"type": "INTEGER", "description": "Number of emails to retrieve"}
        }
    }
}

# Add to tools list (line 183)
tools = [{'google_search': {}}, {"function_declarations": [
    generate_cad, run_web_agent, create_project_tool, switch_project_tool, 
    list_projects_tool, list_smart_devices_tool, control_light_tool, 
    discover_printers_tool, print_stl_tool, get_print_status_tool, 
    iterate_cad_tool, send_email_tool, read_emails_tool  # ADD HERE
] + tools_list[0]['function_declarations'][1:]}]
```

### **3. Initialize Agent in AudioLoop**

In `TARS.py` `__init__` (around line 258):

```python
from email_agent import EmailAgent  # Add import at top

# In __init__:
self.email_agent = EmailAgent()
```

### **4. Add Tool Handler**

In `TARS.py` `receive_audio()` method, add handler (around line 1202):

```python
elif fc.name == "send_email":
    to = fc.args["to"]
    subject = fc.args["subject"]
    body = fc.args["body"]
    print(f"[TARS DEBUG] [TOOL] Tool Call: 'send_email' to='{to}'")
    
    success = await self.email_agent.send_email(to, subject, body)
    result_msg = f"Email sent to {to}" if success else f"Failed to send email to {to}"
    
    function_response = types.FunctionResponse(
        id=fc.id, name=fc.name, response={"result": result_msg}
    )
    function_responses.append(function_response)

elif fc.name == "read_emails":
    limit = fc.args.get("limit", 10)
    print(f"[TARS DEBUG] [TOOL] Tool Call: 'read_emails' limit={limit}")
    
    emails = await self.email_agent.read_emails(limit)
    result_msg = f"Found {len(emails)} emails:\n" + "\n".join([
        f"- {e['subject']} from {e['from']}" for e in emails
    ])
    
    function_response = types.FunctionResponse(
        id=fc.id, name=fc.name, response={"result": result_msg}
    )
    function_responses.append(function_response)
```

### **5. Add Permission Setting**

In `server.py` `DEFAULT_SETTINGS` (around line 60):

```python
"tool_permissions": {
    # ... existing permissions ...
    "send_email": True,  # Require confirmation
    "read_emails": True,
}
```

### **6. Update .env File**

Add to `.env`:
```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
```

### **7. Add to Requirements**

In `requirements.txt`:
```
# Email support (if using IMAP)
secure-smtplib  # Already included in stdlib, but for advanced features
```

---

## Example: Adding Messaging (Twilio SMS)

### **1. Create `backend/messaging_agent.py`:**

```python
from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

class MessagingAgent:
    def __init__(self):
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_PHONE_NUMBER")
        self.client = Client(account_sid, auth_token) if account_sid else None
    
    async def send_sms(self, to: str, message: str) -> bool:
        if not self.client:
            return False
        try:
            msg = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to
            )
            return msg.sid is not None
        except Exception as e:
            print(f"[SMS] Error: {e}")
            return False
```

### **2. Follow same steps as email (tool definition, handler, etc.)**

---

## Testing New Features

1. **Test Tool Definition:**
   ```bash
   # Check if tool appears in Gemini's available tools
   # Look for tool in logs when starting audio loop
   ```

2. **Test Permission System:**
   - Set permission to `True` → should request confirmation
   - Set to `False` → should auto-execute

3. **Test Error Handling:**
   - Invalid credentials → should return error message
   - Network failure → should handle gracefully

4. **Test Integration:**
   - Voice command: "Send an email to test@example.com"
   - Should trigger tool call → confirmation → execution

---

## Best Practices

1. **Always use async/await** for I/O operations
2. **Use `asyncio.to_thread()`** for blocking operations (SMTP, file I/O)
3. **Return structured results** that Gemini can understand
4. **Log errors** with `[AGENT_NAME]` prefix for debugging
5. **Handle missing credentials** gracefully
6. **Add permission checks** in settings.json
7. **Update README.md** with new feature documentation

---

## Summary

The system is well-architected for extensibility. Adding new features follows a consistent pattern:
1. Create agent module
2. Define tool in `TARS.py`
3. Add handler in `receive_audio()`
4. Initialize in `AudioLoop.__init__`
5. Add permissions to settings
6. Update `.env` with credentials

The main entry point for tool execution is `TARS.py`'s `receive_audio()` method around line 808, where all tool calls are routed to their respective handlers.


