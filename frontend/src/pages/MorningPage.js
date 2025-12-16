import React from 'react';
import { useNavigate } from 'react-router-dom';

function MorningPage() {
  const navigate = useNavigate();

  const handleMeditation = () => {
    // Navigate to meditation or handle meditation action
    console.log('Meditation clicked');
  };

  const handleMotivation = () => {
    // Navigate to motivation or handle motivation action
    console.log('Motivation clicked');
  };

  return (
    <div className="container-fluid vh-100 d-flex align-items-center justify-content-center" style={{ backgroundColor: '#000000' }}>
      <div className="row w-100">
        <div className="col-12 text-center mb-4">
          <button
            className="btn"
            onClick={() => navigate('/')}
            style={{ backgroundColor: '#ff6600', color: '#000000' }}
          >
            ← Back to Home
          </button>
        </div>
        
        <div className="col-6">
          <button
            className="btn w-100 h-100 p-5"
            onClick={handleMeditation}
            style={{
              backgroundColor: '#ff6600',
              color: '#000000',
              fontSize: '2rem',
              fontWeight: 'bold',
              minHeight: '300px'
            }}
          >
            Meditation
          </button>
        </div>
        
        <div className="col-6">
          <button
            className="btn w-100 h-100 p-5"
            onClick={handleMotivation}
            style={{
              backgroundColor: '#ff6600',
              color: '#000000',
              fontSize: '2rem',
              fontWeight: 'bold',
              minHeight: '300px'
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

