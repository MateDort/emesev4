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
    <div className="container-fluid page-shell" style={{ padding: '20px', overflowY: 'auto' }}>
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
              className="news-content"
              style={{
                fontFamily: 'Georgia, serif',
                width: '100%',
                maxWidth: '100%',
                padding: '40px 60px',
                lineHeight: '1.8',
                fontSize: '1.1rem',
                color: 'var(--mac-ink)'
              }}
            >
              <div className="text-center mb-5 pb-4" style={{ borderBottom: '2px solid var(--mac-border)' }}>
                <h1 className="display-4 mb-2" style={{ color: 'var(--mac-accent)', fontFamily: 'Georgia, serif', fontWeight: 'bold' }}>
                  Daily News
                </h1>
                <div className="text-muted" style={{ fontSize: '1.1rem' }}>{new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</div>
              </div>
              
              {news.format === 'json' && news.articles ? (
                // New format: Display individual articles
                <div
                  style={{
                    maxWidth: '1000px',
                    margin: '0 auto'
                  }}
                >
                  {news.articles.map((article, idx) => (
                    <article
                      key={idx}
                      className="mb-5 pb-5"
                      style={{
                        borderBottom: idx < news.articles.length - 1 ? '1px solid var(--mac-border)' : 'none',
                        paddingBottom: '2rem'
                      }}
                    >
                      <h2
                        className="mb-3"
                        style={{
                          color: 'var(--mac-accent)',
                          fontFamily: 'Georgia, serif',
                          fontSize: '1.8rem',
                          fontWeight: 'bold',
                          lineHeight: '1.3'
                        }}
                      >
                        {article.title}
                      </h2>
                      
                      <div
                        className="mb-4"
                        style={{
                          textAlign: 'justify',
                          fontSize: '1.15rem',
                          lineHeight: '1.9',
                          color: 'var(--mac-ink)'
                        }}
                      >
                        {article.content.split('\n\n').map((paragraph, pIdx) => (
                          <p key={pIdx} className="mb-3">
                            {paragraph.trim()}
                          </p>
                        ))}
                      </div>
                      
                      <div className="mt-4 pt-3 d-flex align-items-center gap-3" style={{ borderTop: '1px solid rgba(179, 195, 216, 0.3)' }}>
                        <a
                          href={article.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="btn mac-button"
                          style={{
                            color: 'var(--mac-accent)',
                            fontWeight: '600',
                            textDecoration: 'none',
                            padding: '10px 20px',
                            fontSize: '0.95rem',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '6px'
                          }}
                        >
                          <span>📰</span>
                          <span>Read Full Article</span>
                        </a>
                        {article.source && article.source !== 'Unknown' && (
                          <span className="text-muted" style={{ fontSize: '0.9rem' }}>
                            Source: <strong>{article.source}</strong>
                          </span>
                        )}
                      </div>
                    </article>
                  ))}
                </div>
              ) : (
                // Old format: Display as formatted text (backward compatibility)
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
                    gap: '3rem',
                    columnGap: '4rem',
                    alignItems: 'start'
                  }}
                >
                  {news.content.split('\n\n').map((section, idx) => (
                    <div key={idx} className="mb-4" style={{ breakInside: 'avoid', pageBreakInside: 'avoid' }}>
                      {section.split('\n').map((line, lineIdx) => {
                        const trimmedLine = line.trim();
                        if (trimmedLine.startsWith('#') || (trimmedLine.toUpperCase() === trimmedLine && trimmedLine.length > 20 && !trimmedLine.includes('.'))) {
                          return (
                            <h2 
                              key={lineIdx} 
                              className="mb-3 mt-4" 
                              style={{ 
                                color: 'var(--mac-accent)', 
                                fontFamily: 'Georgia, serif',
                                fontSize: '1.5rem',
                                fontWeight: 'bold',
                                lineHeight: '1.4'
                              }}
                            >
                              {trimmedLine.replace(/^#+\s*/, '').trim()}
                            </h2>
                          );
                        }
                        if (trimmedLine) {
                          return (
                            <p key={lineIdx} className="mb-3" style={{ textAlign: 'justify', hyphens: 'auto' }}>
                              {trimmedLine}
                            </p>
                          );
                        }
                        return null;
                      })}
                    </div>
                  ))}
                </div>
              )}
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

