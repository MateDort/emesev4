import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function ScheduleWidget({ schedule, onOpenFullSchedule }) {
  const [showFullSchedule, setShowFullSchedule] = useState(false);
  const [currentAndNext, setCurrentAndNext] = useState({ current: null, next: null });

  useEffect(() => {
    fetchCurrentAndNext();
    const interval = setInterval(fetchCurrentAndNext, 60000); // Update every minute
    return () => clearInterval(interval);
  }, []);

  const fetchCurrentAndNext = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/schedule`);
      if (response.data.schedule && response.data.schedule.length > 0) {
        const now = new Date();
        const currentTime = now.toTimeString().slice(0, 5);
        
        let current = null;
        let next = null;

        for (const event of response.data.schedule) {
          if (event.start_time <= currentTime && currentTime <= event.end_time) {
            current = event;
          } else if (event.start_time > currentTime && !next) {
            next = event;
          }
        }

        setCurrentAndNext({ current, next });
      }
    } catch (error) {
      console.error('Error fetching schedule:', error);
    }
  };

  const handleClick = () => {
    setShowFullSchedule(true);
    onOpenFullSchedule();
  };

  if (showFullSchedule) {
    return (
      <div className="p-3" style={{ backgroundColor: '#000000', color: '#ffffff' }}>
        <div className="d-flex justify-content-between align-items-center mb-3">
          <h5>Full Schedule</h5>
          <button
            className="btn btn-sm"
            onClick={() => setShowFullSchedule(false)}
            style={{ backgroundColor: '#ff6600', color: '#000000' }}
          >
            Close
          </button>
        </div>
        {schedule && schedule.length > 0 ? (
          <div>
            {schedule.map((event, idx) => (
              <div key={idx} className="mb-2 p-2 border-bottom border-secondary">
                <div className="fw-bold">{event.event_title}</div>
                <div className="text-muted">
                  {event.start_time} - {event.end_time}
                </div>
                {event.description && (
                  <div className="text-muted small">{event.description}</div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-muted">No schedule available</div>
        )}
      </div>
    );
  }

  return (
    <div
      className="p-3 rounded cursor-pointer"
      onClick={handleClick}
      style={{
        backgroundColor: '#1a1a1a',
        border: '1px solid #ff6600',
        cursor: 'pointer'
      }}
    >
      <h6 className="mb-3" style={{ color: '#ff6600' }}>Schedule</h6>
      
      {currentAndNext.current && (
        <div className="mb-3">
          <div className="small text-muted">Current</div>
          <div className="fw-bold">{currentAndNext.current.event_title}</div>
          <div className="small text-muted">
            {currentAndNext.current.start_time} - {currentAndNext.current.end_time}
          </div>
        </div>
      )}
      
      {currentAndNext.next && (
        <div>
          <div className="small text-muted">Next</div>
          <div className="fw-bold">{currentAndNext.next.event_title}</div>
          <div className="small text-muted">
            {currentAndNext.next.start_time} - {currentAndNext.next.end_time}
          </div>
        </div>
      )}
      
      {!currentAndNext.current && !currentAndNext.next && (
        <div className="text-muted small">No events scheduled</div>
      )}
    </div>
  );
}

export default ScheduleWidget;

