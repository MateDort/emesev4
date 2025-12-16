# Emese v0.4.1 - Setup Guide

## Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- npm or yarn

## Initial Setup

### 1. Environment Variables

Create a `.env` file in the root directory with your API keys:

```env
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
SERPER_API_KEY=your_serper_api_key_here
WEATHER_API_KEY=your_weather_api_key_here (optional)
```

### 2. Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

The database will be automatically created when you first run the backend.

### 3. Frontend Setup

```bash
cd frontend
npm install
```

Create a `.env` file in the `frontend` directory:

```env
REACT_APP_API_URL=http://localhost:8000
```

## Running the Application

### Option 1: Using Startup Scripts

**Terminal 1 - Backend:**
```bash
./start_backend.sh
```

**Terminal 2 - Frontend:**
```bash
./start_frontend.sh
```

### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

## Accessing the Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Features Overview

### Automatic Tasks
- **4:00 AM**: Daily schedule creation
- **4:30 AM**: Daily study creation
- **Midnight**: Daily newsletter creation

### Pages
- **Home**: Chat interface with schedule widget and time/weather
- **Study**: Daily study page (accessible via "show me today's study")
- **News**: Daily newsletter in newspaper style (accessible via "open news")
- **Morning**: Meditation and motivation buttons (5-6 AM)

### Chat Commands
- "show me today's study" - Opens study page
- "open news" - Opens news page
- "create note [content]" - Creates a new note
- "remind me [time] [message]" - Creates a reminder

## Troubleshooting

### Backend Issues
- Make sure all API keys are set in `.env`
- Check that port 8000 is not in use
- Verify database file permissions

### Frontend Issues
- Ensure backend is running on port 8000
- Check browser console for WebSocket connection errors
- Verify `REACT_APP_API_URL` in frontend `.env`

### Database Issues
- Database file is created automatically at `backend/emese.db`
- If issues occur, delete the database file and restart the backend

## Next Steps

1. Configure your API keys
2. Customize Emese's personality in `Emese.md`
3. Adjust scheduling parameters in `scheduling_parameters.md`
4. Test the automatic tasks (you can manually trigger them for testing)

## Notes

- The wake word "computer" detection requires additional setup for production use
- Weather API is optional - the app will work without it
- Local TTS fallback (pyttsx3) may require system-level TTS libraries

