import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function NotesPage() {
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedNote, setSelectedNote] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchNotes();
  }, []);

  const fetchNotes = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/notes`);
      setNotes(response.data.notes || []);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching notes:', error);
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="container-fluid page-shell vh-100">
      <div className="row h-100">
        <div className="col-12">
          <div className="p-4">
            <div className="d-flex justify-content-between align-items-center mb-4">
              <h2 className="mb-0" style={{ color: 'var(--mac-accent)' }}>Notes</h2>
              <button
                className="btn mac-button"
                onClick={() => navigate('/')}
              >
                ← Back to Home
              </button>
            </div>
            
            {loading ? (
              <div className="text-center">Loading notes...</div>
            ) : notes.length === 0 ? (
              <div className="text-center text-muted">
                <p>No notes yet. Create one by saying "create note" in the chat!</p>
              </div>
            ) : (
              <div className="row">
                <div className="col-12 col-md-4">
                  <div className="aqua-card p-3 scroll-pane" style={{ maxHeight: '70vh' }}>
                    <h5 className="mb-3" style={{ color: 'var(--mac-accent)' }}>All Notes</h5>
                    {notes.map((note) => (
                      <div
                        key={note.id}
                        className={`p-3 mb-2 rounded cursor-pointer ${
                          selectedNote?.id === note.id ? 'glass-panel' : ''
                        }`}
                        onClick={() => setSelectedNote(note)}
                        style={{
                          cursor: 'pointer',
                          border: selectedNote?.id === note.id ? '2px solid var(--mac-accent)' : '1px solid var(--mac-border)'
                        }}
                      >
                        <div className="fw-semibold mb-1">{note.title}</div>
                        <div className="small text-muted">
                          {formatDate(note.created_at)}
                        </div>
                        {note.content && (
                          <div className="small mt-2 text-truncate" style={{ maxWidth: '100%' }}>
                            {note.content.substring(0, 100)}
                            {note.content.length > 100 ? '...' : ''}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
                
                <div className="col-12 col-md-8">
                  {selectedNote ? (
                    <div className="aqua-card p-4 scroll-pane" style={{ maxHeight: '70vh' }}>
                      <h3 className="mb-3" style={{ color: 'var(--mac-accent)' }}>
                        {selectedNote.title}
                      </h3>
                      <div className="small text-muted mb-3">
                        Created: {formatDate(selectedNote.created_at)}
                        {selectedNote.updated_at !== selectedNote.created_at && (
                          <span> • Updated: {formatDate(selectedNote.updated_at)}</span>
                        )}
                      </div>
                      <div
                        className="note-content"
                        style={{
                          lineHeight: '1.8',
                          fontSize: '1.1rem',
                          whiteSpace: 'pre-wrap'
                        }}
                      >
                        {selectedNote.content}
                      </div>
                    </div>
                  ) : (
                    <div className="aqua-card p-4 text-center text-muted">
                      <p>Select a note to view its contents</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default NotesPage;

