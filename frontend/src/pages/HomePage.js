import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import Chat from '../components/Chat';
import ScheduleWidget from '../components/ScheduleWidget';
import TimeWeather from '../components/TimeWeather';
import MorningPage from './MorningPage';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Helper function to get WebSocket URL
const getWebSocketURL = () => {
  if (process.env.REACT_APP_API_URL) {
    // Convert http/https to ws/wss
    const apiUrl = process.env.REACT_APP_API_URL.trim();
    // Remove trailing slash if present
    const cleanUrl = apiUrl.replace(/\/$/, '');
    
    if (cleanUrl.startsWith('https://')) {
      return cleanUrl.replace('https://', 'wss://') + '/ws';
    } else if (cleanUrl.startsWith('http://')) {
      return cleanUrl.replace('http://', 'ws://') + '/ws';
    } else if (cleanUrl.startsWith('wss://') || cleanUrl.startsWith('ws://')) {
      // Already a WebSocket URL, just append /ws if not present
      return cleanUrl.endsWith('/ws') ? cleanUrl : cleanUrl + '/ws';
    } else {
      // Assume https if no protocol specified
      console.warn('⚠️ REACT_APP_API_URL missing protocol, assuming https://');
      return 'wss://' + cleanUrl + '/ws';
    }
  }
  // Default to localhost for development
  console.warn('⚠️ REACT_APP_API_URL not set, using localhost');
  return 'ws://localhost:8000/ws';
};

function HomePage() {
  const [currentPage, setCurrentPage] = useState('home');
  const [schedule, setSchedule] = useState(null);
  const [time, setTime] = useState(new Date());
  const [weather, setWeather] = useState(null);
  const navigate = useNavigate();
  const wsRef = useRef(null);

  useEffect(() => {
    // Update time every second
    const timeInterval = setInterval(() => {
      setTime(new Date());
    }, 1000);

    // Fetch schedule
    fetchSchedule();
    
    // Fetch weather
    fetchWeather();
    
    // Refresh weather every 10 minutes
    const weatherInterval = setInterval(() => {
      fetchWeather();
    }, 600000);

    // Check if it's morning (5-6am) to show morning page
    const hour = new Date().getHours();
    if (hour >= 5 && hour < 6) {
      setCurrentPage('morning');
    }

    // WebSocket connection
    connectWebSocket();

    return () => {
      clearInterval(timeInterval);
      clearInterval(weatherInterval);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const connectWebSocket = () => {
    const wsUrl = getWebSocketURL();
    console.log('🔌 Connecting to WebSocket:', wsUrl);
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('✅ WebSocket connected successfully');
    };

    ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
      console.error('WebSocket URL was:', wsUrl);
      console.error('API_URL env:', process.env.REACT_APP_API_URL);
    };

    ws.onclose = (event) => {
      console.log('🔌 WebSocket disconnected', event.code, event.reason);
      // Attempt to reconnect after 3 seconds
      setTimeout(() => {
        console.log('🔄 Attempting to reconnect WebSocket...');
        connectWebSocket();
      }, 3000);
    };
  };

  const fetchSchedule = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/schedule`);
      setSchedule(response.data.schedule);
    } catch (error) {
      console.error('Error fetching schedule:', error);
    }
  };

  const fetchWeather = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/weather`);
      if (response.data && response.data.weather) {
        setWeather(response.data.weather);
      }
    } catch (error) {
      console.error('Error fetching weather:', error);
      // Set a fallback weather object on error
      setWeather({
        temperature: "N/A",
        description: "Unable to fetch weather",
        location: "Marietta, GA"
      });
    }
  };

  const handlePageChange = (page) => {
    if (page === 'study') {
      navigate('/study');
    } else if (page === 'news') {
      navigate('/news');
    } else if (page === 'morning') {
      navigate('/morning');
    } else if (page === 'notes') {
      navigate('/notes');
    }
  };

  if (currentPage === 'morning') {
    return <MorningPage />;
  }

  return (
    <div className="container-fluid page-shell vh-100">
      <div className="row g-3 h-100">
        {/* Left Side - Widgets and Time/Weather (2/3) */}
        <div className="col-12 col-lg-8 d-flex flex-column gap-3 h-100">
          <div className="glass-panel p-3 h-100 d-flex flex-column">
            <div className="mb-3">
              <ScheduleWidget schedule={schedule} onOpenFullSchedule={() => {}} />
            </div>
            <div className="mt-auto">
              <TimeWeather time={time} weather={weather} />
            </div>
          </div>
        </div>

        {/* Right Side - Chat (1/3) */}
        <div className="col-12 col-lg-4 h-100">
          <div className="h-100">
            <Chat onPageChange={handlePageChange} wsRef={wsRef} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default HomePage;

