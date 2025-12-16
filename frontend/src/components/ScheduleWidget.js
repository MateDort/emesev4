import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function ScheduleWidget({ schedule, onOpenFullSchedule }) {
  const [showFullSchedule, setShowFullSchedule] = useState(false);
  const [currentAndNext, setCurrentAndNext] = useState({ current: null, next: null });
  const [reminders, setReminders] = useState([]);
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    fetchCurrentAndNext();
    fetchReminders();
    const interval = setInterval(() => {
      fetchCurrentAndNext();
      fetchReminders();
    }, 60000); // Update every minute
    return () => clearInterval(interval);
  }, []);

  // Update current time every second for live countdown
  useEffect(() => {
    const timeInterval = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timeInterval);
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

  const fetchReminders = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/reminders`);
      if (response.data.reminders) {
        // Get up to 3 upcoming reminders
        setReminders(response.data.reminders.slice(0, 3));
      }
    } catch (error) {
      console.error('Error fetching reminders:', error);
    }
  };

  const formatCountdown = (reminderTime) => {
    const now = currentTime;
    const target = new Date(reminderTime);
    const diff = target - now;
    
    if (diff <= 0) {
      return "Overdue";
    }
    
    const totalSeconds = Math.floor(diff / 1000);
    const days = Math.floor(totalSeconds / 86400);
    const hours = Math.floor((totalSeconds % 86400) / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    
    const parts = [];
    if (days > 0) parts.push(`${days}d`);
    if (hours > 0) parts.push(`${hours}h`);
    if (minutes > 0) parts.push(`${minutes}m`);
    parts.push(`${seconds}s`); // Always show seconds
    
    return parts.join(' ');
  };

  const handleCompleteReminder = async (reminderId, e) => {
    e.stopPropagation();
    try {
      await axios.post(`${API_URL}/api/reminders/${reminderId}/complete`);
      fetchReminders(); // Refresh the list
    } catch (error) {
      console.error('Error completing reminder:', error);
    }
  };

  const handleDeleteReminder = async (reminderId, e) => {
    e.stopPropagation();
    try {
      await axios.delete(`${API_URL}/api/reminders/${reminderId}`);
      fetchReminders(); // Refresh the list
    } catch (error) {
      console.error('Error deleting reminder:', error);
    }
  };

  const handleClick = () => {
    setShowFullSchedule(true);
    onOpenFullSchedule();
  };

  const closeModal = () => setShowFullSchedule(false);

  return (
    <>
      {showFullSchedule && (
        <div
          className="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center"
          style={{ background: 'rgba(0, 0, 0, 0.35)', zIndex: 1050 }}
        >
          <div className="aqua-card p-4 scroll-pane" style={{ maxWidth: '640px', width: '90%', maxHeight: '80vh' }}>
            <div className="d-flex justify-content-between align-items-center mb-3">
              <h5 className="mb-0" style={{ color: 'var(--mac-accent)' }}>Full Schedule</h5>
              <button className="btn mac-button btn-sm" onClick={closeModal}>
                Close
              </button>
            </div>
            {schedule && schedule.length > 0 ? (
              <div className="scroll-pane pe-1" style={{ maxHeight: '65vh' }}>
                {schedule.map((event, idx) => (
                  <div key={idx} className="mb-3 pb-2" style={{ borderBottom: '1px solid var(--mac-border)' }}>
                    <div className="fw-semibold">{event.event_title}</div>
                    <div className="text-muted">
                      {event.start_time} - {event.end_time}
                    </div>
                    {event.description && (
                      <div className="text-muted small mt-1">{event.description}</div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-muted">No schedule available</div>
            )}
          </div>
        </div>
      )}

      <div className="d-flex flex-column gap-3">
        {/* Schedule Card */}
        <div
          className="p-3 rounded cursor-pointer aqua-card"
          onClick={handleClick}
          style={{
            cursor: 'pointer'
          }}
        >
          <h6 className="mb-3" style={{ color: 'var(--mac-accent)', letterSpacing: '0.5px' }}>Schedule</h6>
          
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

        {/* Reminders Card - Separate Bubble */}
        <div className="p-3 rounded aqua-card">
          <h6 className="mb-3" style={{ color: 'var(--mac-accent)', letterSpacing: '0.5px' }}>Reminders</h6>
          
          {reminders.length > 0 ? (
            <div>
              {reminders.map((reminder) => (
                <div key={reminder.id} className="mb-2">
                  <div className="d-flex justify-content-between align-items-start">
                    <div className="flex-grow-1">
                      <div className="small fw-semibold">{reminder.title}</div>
                      {reminder.description && (
                        <div className="small text-muted">{reminder.description}</div>
                      )}
                    </div>
                    <div className="d-flex align-items-center gap-2">
                      <div className="small text-muted" style={{ whiteSpace: 'nowrap' }}>
                        {formatCountdown(reminder.reminder_time)}
                      </div>
                      <button
                        onClick={(e) => handleCompleteReminder(reminder.id, e)}
                        className="btn btn-sm p-0"
                        style={{
                          background: 'none',
                          border: 'none',
                          color: 'var(--mac-accent)',
                          fontSize: '18px',
                          cursor: 'pointer',
                          padding: '2px 6px',
                          lineHeight: '1',
                          fontWeight: 'bold',
                          transition: 'opacity 0.2s'
                        }}
                        onMouseEnter={(e) => e.target.style.opacity = '0.7'}
                        onMouseLeave={(e) => e.target.style.opacity = '1'}
                        title="Mark as done"
                      >
                        ✓
                      </button>
                      <button
                        onClick={(e) => handleDeleteReminder(reminder.id, e)}
                        className="btn btn-sm p-0"
                        style={{
                          background: 'none',
                          border: 'none',
                          color: '#dc3545',
                          fontSize: '18px',
                          cursor: 'pointer',
                          padding: '2px 6px',
                          lineHeight: '1',
                          fontWeight: 'bold',
                          transition: 'opacity 0.2s'
                        }}
                        onMouseEnter={(e) => e.target.style.opacity = '0.7'}
                        onMouseLeave={(e) => e.target.style.opacity = '1'}
                        title="Delete"
                      >
                        ✕
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-muted small">None</div>
          )}
        </div>
      </div>
    </>
  );
}

export default ScheduleWidget;

