import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Helper function to parse markdown and convert to JSX
const parseMarkdown = (text) => {
  if (!text) return null;
  
  // Split by double newlines first to get paragraphs
  const paragraphs = text.split(/\n\n+/);
  const elements = [];
  let elementKey = 0;
  
  paragraphs.forEach((paragraph, paraIdx) => {
    const lines = paragraph.split('\n').map(l => l.trim()).filter(l => l);
    
    if (lines.length === 0) return;
    
    // Check if it's a horizontal rule
    if (lines.length === 1 && (lines[0] === '***' || lines[0] === '---')) {
      elements.push(
        <hr 
          key={`hr-${elementKey++}`} 
          style={{ margin: '2rem 0', border: 'none', borderTop: '1px solid var(--mac-border)' }} 
        />
      );
      return;
    }
    
    // Check if first line is a heading
    const firstLine = lines[0];
    if (firstLine.startsWith('#')) {
      const level = Math.min(firstLine.match(/^#+/)[0].length, 6);
      const headingText = firstLine.replace(/^#+\s*/, '').trim();
      const HeadingTag = `h${level}`;
      const headingStyle = {
        color: 'var(--mac-accent)',
        fontFamily: 'Georgia, serif',
        fontSize: level === 1 ? '1.8rem' : level === 2 ? '1.5rem' : '1.3rem',
        fontWeight: 'bold',
        lineHeight: '1.4',
        marginBottom: '1rem',
        marginTop: '2rem'
      };
      
      elements.push(
        React.createElement(
          HeadingTag,
          {
            key: `heading-${elementKey++}`,
            className: 'mb-3 mt-4',
            style: headingStyle
          },
          parseInlineMarkdown(headingText)
        )
      );
      
      // If there are more lines after the heading, render them as paragraphs
      if (lines.length > 1) {
        const remainingLines = lines.slice(1).join(' ');
        if (remainingLines.trim()) {
          elements.push(
            <p 
              key={`p-after-heading-${elementKey++}`}
              className="mb-3"
              style={{
                textAlign: 'justify',
                hyphens: 'auto',
                fontSize: '1.15rem',
                lineHeight: '1.9'
              }}
            >
              {parseInlineMarkdown(remainingLines)}
            </p>
          );
        }
      }
      return;
    }
    
    // Regular paragraph - join all lines
    const paragraphText = lines.join(' ');
    if (paragraphText.trim()) {
      elements.push(
        <p 
          key={`p-${elementKey++}`}
          className="mb-4"
          style={{
            textAlign: 'justify',
            hyphens: 'auto',
            fontSize: '1.15rem',
            lineHeight: '1.9'
          }}
        >
          {parseInlineMarkdown(paragraphText)}
        </p>
      );
    }
  });
  
  return elements;
};

// Helper function to parse inline markdown (bold, italic, etc.)
const parseInlineMarkdown = (text) => {
  if (!text) return null;
  
  const parts = [];
  let key = 0;
  
  // Pattern to match **bold**, *italic*, or ***bold italic***
  // Order matters: match *** first, then **, then *
  const markdownPattern = /(\*\*\*([^*]+?)\*\*\*|\*\*([^*]+?)\*\*|\*([^*]+?)\*)/g;
  let match;
  let lastIndex = 0;
  
  while ((match = markdownPattern.exec(text)) !== null) {
    // Add text before the match
    if (match.index > lastIndex) {
      const beforeText = text.substring(lastIndex, match.index);
      if (beforeText) {
        parts.push(beforeText);
      }
    }
    
    // Handle the markdown match
    if (match[1].startsWith('***')) {
      // Bold italic
      parts.push(
        <strong key={`markdown-${key++}`}>
          <em>{match[2]}</em>
        </strong>
      );
    } else if (match[1].startsWith('**')) {
      // Bold
      parts.push(
        <strong key={`markdown-${key++}`} style={{ fontWeight: 'bold' }}>
          {match[3]}
        </strong>
      );
    } else if (match[1].startsWith('*')) {
      // Italic (but not if it's part of **)
      parts.push(
        <em key={`markdown-${key++}`} style={{ fontStyle: 'italic' }}>
          {match[4]}
        </em>
      );
    }
    
    lastIndex = match.index + match[0].length;
  }
  
  // Add remaining text
  if (lastIndex < text.length) {
    const remainingText = text.substring(lastIndex);
    if (remainingText) {
      parts.push(remainingText);
    }
  }
  
  // If no markdown was found, return the original text
  // If we found markdown, return the array of parts
  return parts.length > 0 ? parts : text;
};

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
    <div className="container-fluid page-shell" style={{ padding: '20px', overflowY: 'auto' }}>
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
            <div 
              className="study-content"
              style={{
                width: '100%',
                maxWidth: '100%',
                padding: '40px 60px',
                lineHeight: '1.9',
                fontSize: '1.15rem',
                color: 'var(--mac-ink)',
                fontFamily: 'Georgia, "Times New Roman", serif'
              }}
            >
              <div className="mb-5 pb-4" style={{ borderBottom: '2px solid var(--mac-border)' }}>
                <h1 
                  className="mb-3" 
                  style={{ 
                    color: 'var(--mac-accent)', 
                    fontFamily: 'Georgia, serif',
                    fontSize: '2.5rem',
                    fontWeight: 'bold',
                    lineHeight: '1.3'
                  }}
                >
                  {study.title}
                </h1>
                <div className="text-muted" style={{ fontSize: '1rem' }}>
                  {new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                </div>
              </div>
              
              <div
                style={{
                  maxWidth: '900px',
                  margin: '0 auto'
                }}
              >
                {parseMarkdown(study.content)}
              </div>
              
              {study.source_url && (
                <div className="mt-5 pt-4 text-center" style={{ borderTop: '2px solid var(--mac-border)' }}>
                  <a
                    href={study.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn mac-button"
                    style={{ 
                      color: 'var(--mac-accent)', 
                      fontWeight: '600',
                      textDecoration: 'none',
                      padding: '10px 20px'
                    }}
                  >
                    📚 View Source Article
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

