import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import Chat from '../components/Chat';
import ScheduleWidget from '../components/ScheduleWidget';
import TimeWeather from '../components/TimeWeather';
import MorningPage from './MorningPage';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

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

    // Check if it's morning (5-6am) to show morning page
    const hour = new Date().getHours();
    if (hour >= 5 && hour < 6) {
      setCurrentPage('morning');
    }

    // WebSocket connection
    connectWebSocket();

    return () => {
      clearInterval(timeInterval);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const connectWebSocket = () => {
    const ws = new WebSocket(`ws://localhost:8000/ws`);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'automatic_task') {
        // Show notification for automatic tasks
        console.log('Automatic task:', data.message);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
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
      setWeather(response.data.weather);
    } catch (error) {
      console.error('Error fetching weather:', error);
    }
  };

  const handlePageChange = (page) => {
    if (page === 'study') {
      navigate('/study');
    } else if (page === 'news') {
      navigate('/news');
    } else if (page === 'morning') {
      navigate('/morning');
    }
  };

  if (currentPage === 'morning') {
    return <MorningPage />;
  }

  return (
    <div className="container-fluid vh-100 d-flex" style={{ backgroundColor: '#000000' }}>
      {/* Left Side - Widgets and Time/Weather */}
      <div className="col-3 d-flex flex-column border-end border-secondary">
        {/* Widgets Section - Top Left */}
        <div className="flex-grow-1 border-bottom border-secondary p-3">
          <ScheduleWidget schedule={schedule} onOpenFullSchedule={() => {}} />
        </div>
        
        {/* Time and Weather - Bottom Left */}
        <div className="p-3">
          <TimeWeather time={time} weather={weather} />
        </div>
      </div>

      {/* Right Side - Chat */}
      <div className="col-9 d-flex flex-column">
        <Chat onPageChange={handlePageChange} wsRef={wsRef} />
      </div>
    </div>
  );
}

export default HomePage;

