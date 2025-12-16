import React, { useState } from 'react';

function Toolbox({ ttsEnabled, setTtsEnabled, muted, setMuted }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="position-relative me-2">
      <button
        type="button"
        className="btn btn-outline-secondary"
        onClick={() => setIsOpen(!isOpen)}
        style={{ borderColor: '#ff6600', color: '#ff6600' }}
      >
        ⚙️
      </button>
      
      {isOpen && (
        <div
          className="position-absolute bottom-100 mb-2 p-3 rounded"
          style={{ backgroundColor: '#1a1a1a', border: '1px solid #ff6600', zIndex: 1000 }}
        >
          <div className="form-check form-switch mb-2">
            <input
              className="form-check-input"
              type="checkbox"
              id="ttsToggle"
              checked={ttsEnabled}
              onChange={(e) => setTtsEnabled(e.target.checked)}
            />
            <label className="form-check-label text-white" htmlFor="ttsToggle">
              Text to Speech
            </label>
          </div>
          
          <div className="form-check form-switch">
            <input
              className="form-check-input"
              type="checkbox"
              id="muteToggle"
              checked={muted}
              onChange={(e) => setMuted(e.target.checked)}
            />
            <label className="form-check-label text-white" htmlFor="muteToggle">
              Mute
            </label>
          </div>
        </div>
      )}
    </div>
  );
}

export default Toolbox;

