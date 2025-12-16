import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function NewsPage() {
  const [news, setNews] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchNews();
  }, []);

  const fetchNews = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/news`);
      setNews(response.data.news);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching news:', error);
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
              <div className="text-center">Loading news...</div>
            ) : news ? (
              <div
                className="news-content"
                style={{
                  fontFamily: 'Georgia, serif',
                  maxWidth: '900px',
                  margin: '0 auto',
                  padding: '2rem',
                  backgroundColor: '#1a1a1a',
                  border: '2px solid #ff6600'
                }}
              >
                <div className="text-center mb-4 border-bottom border-secondary pb-3">
                  <h1 className="display-4" style={{ color: '#ff6600', fontFamily: 'serif' }}>
                    Daily News
                  </h1>
                  <div className="text-muted">{new Date().toLocaleDateString()}</div>
                </div>
                
                <div
                  style={{
                    columnCount: 2,
                    columnGap: '2rem',
                    lineHeight: '1.6'
                  }}
                >
                  {news.content.split('\n\n').map((section, idx) => (
                    <div key={idx} className="mb-3">
                      {section.split('\n').map((line, lineIdx) => {
                        if (line.trim().startsWith('#') || (line.trim().toUpperCase() === line.trim() && line.length > 20)) {
                          return (
                            <h3 key={lineIdx} className="mb-2" style={{ color: '#ff6600' }}>
                              {line.replace('#', '').trim()}
                            </h3>
                          );
                        }
                        return (
                          <p key={lineIdx} className="mb-2">
                            {line}
                          </p>
                        );
                      })}
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center">No news available for today.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default NewsPage;

