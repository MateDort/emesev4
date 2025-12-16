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

  const locationLabel = weather?.location || 'Marietta, GA';

  return (
    <div className="aqua-card p-3">
      <div className="mb-2">
        <div className="h4 mb-0" style={{ color: 'var(--mac-accent)' }}>
          {formatTime(time)}
        </div>
        <div className="small text-muted">{formatDate(time)}</div>
      </div>
      
      {weather ? (
        <div className="small">
          <div className="fw-semibold">{locationLabel}</div>
          {weather.temperature === "N/A" || weather.description === "Weather service not configured" ? (
            <div className="text-muted">
              <div>Weather: Not configured</div>
              <div className="text-capitalize" style={{ fontSize: '0.75rem' }}>
                Add WEATHER_API_KEY to .env
              </div>
            </div>
          ) : (
            <>
              <div>Weather: {weather.temperature}°F</div>
              <div className="text-capitalize">{weather.description}</div>
            </>
          )}
        </div>
      ) : (
        <div className="small text-muted">Weather: Loading...</div>
      )}
    </div>
  );
}

export default TimeWeather;

