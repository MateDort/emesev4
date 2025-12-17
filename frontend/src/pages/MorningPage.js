import React from 'react';
import { useNavigate } from 'react-router-dom';

function MorningPage() {
  const navigate = useNavigate();

  const handleMeditation = () => {
    // Navigate to meditation or handle meditation action
    console.log('Meditation clicked');
  };

  const handleMotivation = () => {
    // Open motivation YouTube video
    const motivationLink = "https://www.youtube.com/watch?v=UAZJC-yirR0&t=913s";
    window.open(motivationLink, '_blank');
  };

  return (
    <div className="container-fluid page-shell d-flex align-items-center justify-content-center">
      <div className="row w-100 g-3">
        <div className="col-12 text-center">
          <button
            className="btn mac-button px-4 py-2"
            onClick={() => navigate('/')}
          >
            ← Back to Home
          </button>
        </div>
        
        <div className="col-12 col-md-6">
          <button
            className="btn w-100 p-5 mac-button"
            onClick={handleMeditation}
            style={{
              fontSize: '2rem',
              fontWeight: 'bold',
              minHeight: '260px'
            }}
          >
            Meditation
          </button>
        </div>
        
        <div className="col-12 col-md-6">
          <button
            className="btn w-100 p-5 mac-button"
            onClick={handleMotivation}
            style={{
              fontSize: '2rem',
              fontWeight: 'bold',
              minHeight: '260px'
            }}
          >
            Motivation
          </button>
        </div>
      </div>
    </div>
  );
}

export default MorningPage;

