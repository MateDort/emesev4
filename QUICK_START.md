# Quick Start Guide

## Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Create `.env` file in the root directory** (not in backend/):
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
   SERPER_API_KEY=your_serper_api_key_here
   WEATHER_API_KEY=your_weather_api_key_here (optional)
   ```

   **Note:** The backend will start even without API keys, but certain features will be disabled:
   - Without `GEMINI_API_KEY`: LLM chat features disabled
   - Without `OPENAI_API_KEY`: Voice transcription disabled
   - Without `ELEVENLABS_API_KEY`: TTS will use local fallback (if available)
   - Without `SERPER_API_KEY`: Study and news agents won't be able to search the web

5. **Start the backend:**
   ```bash
   python3 main.py
   ```
   
   Or use the startup script from project root:
   ```bash
   ./start_backend.sh
   ```

   The server will be available at `http://localhost:8000`
   API docs at `http://localhost:8000/docs`

## Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Create `.env` file in frontend directory:**
   ```env
   REACT_APP_API_URL=http://localhost:8000
   ```

4. **Start the frontend:**
   ```bash
   npm start
   ```
   
   Or use the startup script from project root:
   ```bash
   ./start_frontend.sh
   ```

   The app will open at `http://localhost:3000`

## Running Both

You need to run both backend and frontend in separate terminals:

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python3 main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

## Troubleshooting

### Backend won't start
- Make sure you're in the virtual environment: `source venv/bin/activate`
- Check that all dependencies are installed: `pip install -r requirements.txt`
- The backend will start even without API keys (with warnings)

### Frontend won't connect to backend
- Make sure backend is running on port 8000
- Check `REACT_APP_API_URL` in `frontend/.env`
- Check browser console for errors

### Python 3.14 compatibility warnings
- These are warnings, not errors - the app should still work
- For best compatibility, use Python 3.11 or 3.12
- See `backend/PYTHON314_NOTES.md` for details

