# TARS V2 Quick Reference Guide

## 🚀 How It Works (TL;DR)

1. **User speaks/types** → Frontend → Socket.IO → `server.py` → `TARS.py`
2. **Gemini processes** → Determines tool to call
3. **Permission check** → User confirms (if required)
4. **Tool executes** → Agent handles task
5. **Result returns** → Gemini responds → Frontend displays

## 📁 Key Files

| File | Purpose |
|------|---------|
| `backend/server.py` | Socket.IO server, routes events |
| `backend/TARS.py` | Main AI loop, tool orchestration |
| `backend/cad_agent.py` | 3D CAD generation |
| `backend/web_agent.py` | Browser automation |
| `backend/printer_agent.py` | 3D printing |
| `backend/kasa_agent.py` | Smart home control |
| `backend/tools.py` | Tool definitions |
| `backend/settings.json` | User preferences |

## ✅ What Works

- ✅ Voice interaction with Gemini 2.5 Native Audio
- ✅ 3D CAD generation (build123d)
- ✅ Web browser automation
- ✅ 3D printer control (Moonraker/OctoPrint)
- ✅ Smart home (Kasa devices)
- ✅ Project management
- ✅ Face authentication (optional)
- ✅ File operations

## ⚠️ Known Issues

1. Duplicate confirmation check in `TARS.py` (line 859-869)
2. Video frames may not be captured if mode is "none"
3. Some error handling could be improved
4. Settings persistence incomplete for some state
5. Windows path handling needs more testing

## 🔑 API Keys Needed

**Required:**
- `GEMINI_API_KEY` in `.env` file (root directory)

**For Email Feature (if adding):**
- `SMTP_SERVER`, `SMTP_PORT`, `EMAIL_ADDRESS`, `EMAIL_PASSWORD`

**For SMS Feature (if adding):**
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`

## 🔧 Adding New Features (5 Steps)

### Example: Email Feature

**1. Create Agent** (`backend/email_agent.py`)
```python
class EmailAgent:
    async def send_email(self, to, subject, body):
        # Implementation
```

**2. Add Tool Definition** (`TARS.py` line ~183)
```python
send_email_tool = {
    "name": "send_email",
    "description": "Sends an email...",
    "parameters": {...}
}
# Add to tools list
```

**3. Initialize Agent** (`TARS.py` `__init__`)
```python
from email_agent import EmailAgent
self.email_agent = EmailAgent()
```

**4. Add Handler** (`TARS.py` `receive_audio()` ~line 1202)
```python
elif fc.name == "send_email":
    success = await self.email_agent.send_email(...)
    # Create FunctionResponse
```

**5. Add Permission** (`server.py` `DEFAULT_SETTINGS`)
```python
"send_email": True  # Require confirmation
```

## 📍 Tool Execution Flow

```
receive_audio() [TARS.py:808]
    ↓
Tool call detected
    ↓
Permission check [TARS.py:816]
    ↓
User confirmation [if required]
    ↓
Handler execution [TARS.py:872-1202]
    ↓
Agent method call
    ↓
FunctionResponse sent to Gemini
```

## 🎯 Tool Handlers Location

All tool handlers are in `TARS.py` `receive_audio()` method:
- `generate_cad` → line 872
- `run_web_agent` → line 880
- `write_file` → line 897
- `control_light` → line 1016
- `print_stl` → line 1112
- Add new handlers here!

## 🔐 Permissions System

- Settings in `backend/settings.json`
- `tool_permissions.{tool_name}` = `true` → requires confirmation
- `false` → auto-executes
- Checked in `TARS.py` line 816

## 📝 Project Structure

```
projects/
  {project_name}/
    cad/          # STL files
    browser/      # Browser screenshots/logs
    chat_history.jsonl  # Conversation log
```

## 🐛 Debugging Tips

1. Check `backend/server.py` logs for Socket.IO events
2. Check `TARS.py` logs for tool calls (look for `[TARS DEBUG]`)
3. Check agent-specific logs (e.g., `[CAD]`, `[WEB]`, `[PRINTER]`)
4. Verify `.env` file has `GEMINI_API_KEY`
5. Check `settings.json` for permission settings

## 📚 Full Documentation

See `SYSTEM_ANALYSIS.md` for complete details.


