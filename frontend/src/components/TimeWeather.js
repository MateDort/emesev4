import React from 'react';

function TimeWeather({ time, weather }) {
  const formatTime = (date) => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const formatDate = (date) => {
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <div style={{ color: '#ffffff' }}>
      <div className="mb-2">
        <div className="h4 mb-0" style={{ color: '#ff6600' }}>
          {formatTime(time)}
        </div>
        <div className="small text-muted">{formatDate(time)}</div>
      </div>
      
      {weather ? (
        <div className="small">
          <div>Weather: {weather.temperature}°F</div>
          <div>{weather.description}</div>
        </div>
      ) : (
        <div className="small text-muted">Weather: Loading...</div>
      )}
    </div>
  );
}

export default TimeWeather;

