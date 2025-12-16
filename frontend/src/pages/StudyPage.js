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
    <div className="container-fluid page-shell">
      <div className="row">
        <div className="col-12 mb-4 d-flex justify-content-between align-items-center">
          <button
            className="btn mac-button"
            onClick={() => navigate('/')}
          >
            ← Back to Home
          </button>
          <div className="text-muted small">Latest study</div>
        </div>
        
        <div className="col-12">
          {loading ? (
            <div className="text-center">Loading study...</div>
          ) : study ? (
            <div className="aqua-card p-4 scroll-pane" style={{ maxHeight: '75vh' }}>
              <h1 className="mb-3" style={{ color: 'var(--mac-accent)' }}>{study.title}</h1>
              <div
                className="study-content"
                style={{
                  lineHeight: '1.8',
                  fontSize: '1.05rem',
                  maxWidth: '900px',
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
                <div className="mt-4 text-center">
                  <a
                    href={study.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ color: 'var(--mac-accent)', fontWeight: '600' }}
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
  );
}

export default StudyPage;

