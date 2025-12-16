# Emese v0.4.1 - Life OS

Emese is an AI assistant that helps Máté with daily tasks, programming challenges, thinking, building, and automatic reminders.

## Project Structure

```
emesev4/
├── backend/              # Python FastAPI backend
│   ├── agents/          # AI agents (main, scheduling, study, news)
│   ├── database/        # SQLite database setup
│   ├── services/        # Services (voice, TTS, reminders, notes)
│   └── main.py         # FastAPI server
├── frontend/            # React.js frontend
│   ├── src/
│   │   ├── components/  # React components
│   │   └── pages/      # Page components
│   └── public/
├── Emese.md            # Emese's personality and prompt
├── Máté.md             # User information
├── scheduling_parameters.md
├── studies_parameters.md
├── news_letter_parameters.md
└── project.md          # Project documentation
```

## Setup

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file in root directory with:
```
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
SERPER_API_KEY=your_serper_api_key (used for weather, news, and study searches)
PICOVOICE_ACCESS_KEY=your_picovoice_access_key (for wake word detection - get free key at https://console.picovoice.ai/)
```

5. Run backend:
```bash
python main.py
```

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create `.env` file in frontend directory:
```
REACT_APP_API_URL=http://localhost:8000
```

4. Run frontend:
```bash
npm start
```

## Features

- **Chat Interface**: Real-time chat with Emese via WebSocket
- **Voice Input**: Offline wake word "computer" detection using pvporcupine + pyaudio, speech-to-text via OpenAI Whisper (say "computer" to activate)
- **Text-to-Speech**: ElevenLabs TTS with local fallback
- **Weather Widget**: Shows current weather (uses SERPER_API_KEY to search for weather)
- **Schedule Widget**: Shows current and next event
- **Study Page**: Daily studies on AI, design, and related topics
- **News Page**: Daily newsletter in newspaper style
- **Morning Page**: Meditation and motivation buttons (5-6am)
- **Automatic Tasks**:
  - Schedule creation at 4:00 AM
  - Study creation at 4:30 AM
  - Newsletter creation at midnight
- **Notes**: Create, edit, read, and delete notes
- **Reminders**: Set and manage reminders with notifications

## Deployment

The project is configured for Vercel deployment. The frontend will be deployed as a static site, and the backend should be deployed separately (consider using Railway, Render, or similar services for the Python backend).

## Version

Current version: 0.4.1

