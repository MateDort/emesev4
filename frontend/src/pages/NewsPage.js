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
    <div className="container-fluid page-shell">
      <div className="row">
        <div className="col-12">
          <div className="mb-4 d-flex justify-content-between align-items-center">
            <button
              className="btn mac-button"
              onClick={() => navigate('/')}
            >
              ← Back to Home
            </button>
            <div className="text-muted small">Updated: {new Date().toLocaleTimeString()}</div>
          </div>
          
          {loading ? (
            <div className="text-center">Loading news...</div>
          ) : news ? (
            <div
              className="news-content aqua-card p-4 scroll-pane"
              style={{
                fontFamily: 'Georgia, serif',
                maxWidth: '1000px',
                margin: '0 auto',
                maxHeight: '75vh'
              }}
            >
              <div className="text-center mb-4 pb-3" style={{ borderBottom: '1px solid var(--mac-border)' }}>
                <h1 className="display-5 mb-1" style={{ color: 'var(--mac-accent)', fontFamily: 'serif' }}>
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
                          <h3 key={lineIdx} className="mb-2" style={{ color: 'var(--mac-accent)' }}>
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
  );
}

export default NewsPage;

