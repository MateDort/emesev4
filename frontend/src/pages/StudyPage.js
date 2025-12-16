import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function StudyPage() {
  const [study, setStudy] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchStudy();
  }, []);

  const fetchStudy = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/study`);
      setStudy(response.data.study);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching study:', error);
      setLoading(false);
    }
  };

  return (
    <div className="container-fluid vh-100" style={{ backgroundColor: '#000000', color: '#ffffff' }}>
      <div className="row h-100">
        <div className="col-12">
          <div className="p-4">
            <button
              className="btn mb-4"
              onClick={() => navigate('/')}
              style={{ backgroundColor: '#ff6600', color: '#000000' }}
            >
              ← Back to Home
            </button>
            
            {loading ? (
              <div className="text-center">Loading study...</div>
            ) : study ? (
              <div>
                <h1 className="mb-4" style={{ color: '#ff6600' }}>{study.title}</h1>
                <div
                  className="study-content"
                  style={{
                    lineHeight: '1.8',
                    fontSize: '1.1rem',
                    maxWidth: '800px',
                    margin: '0 auto'
                  }}
                >
                  {study.content.split('\n').map((paragraph, idx) => (
                    <p key={idx} className="mb-3">
                      {paragraph}
                    </p>
                  ))}
                </div>
                {study.source_url && (
                  <div className="mt-4">
                    <a
                      href={study.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ color: '#ff6600' }}
                    >
                      View Source
                    </a>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center">No study available for today.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default StudyPage;

