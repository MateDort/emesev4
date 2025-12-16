# Backend Setup Notes

## Python Version Compatibility

**Important**: This project works best with **Python 3.11 or 3.12**. 

Python 3.14 is very new and some dependencies (like older versions of pydantic) may not be fully compatible yet. If you encounter build errors with `pydantic-core`, please use Python 3.11 or 3.12.

## Installation Issues

### If you see pydantic-core build errors:

1. **Recommended**: Use Python 3.11 or 3.12:
   ```bash
   python3.11 -m venv venv
   # or
   python3.12 -m venv venv
   ```

2. **Alternative**: Update pydantic to latest version (already done in requirements.txt)

### pyttsx3 (Local TTS Fallback)

The `pyttsx3` package is **optional** and commented out in `requirements.txt` because:
- It requires many macOS-specific dependencies (pyobjc frameworks)
- It's only used as a fallback when ElevenLabs TTS is unavailable
- The installation can be slow and pull in hundreds of dependencies

If you want local TTS fallback:
1. Uncomment `pyttsx3==2.90` in `requirements.txt`
2. Run `pip install -r requirements.txt` (this will take longer)

The app will work fine without it - ElevenLabs TTS will be used, and if that fails, TTS will simply be disabled.

## Quick Setup

```bash
# Use Python 3.11 or 3.12 (recommended)
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Initialize database
python3 -c "from database.database import init_db; init_db()"

# Run server
python3 main.py
```

