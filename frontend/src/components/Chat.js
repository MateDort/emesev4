import React, { useState, useEffect, useRef } from 'react';
import Toolbox from './Toolbox';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function Chat({ onPageChange, wsRef }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [muted, setMuted] = useState(false);
  const messagesEndRef = useRef(null);
  const audioRef = useRef(null);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { type: 'user', text: userMessage }]);
    setIsThinking(true);

    // Send via WebSocket if available
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'chat',
        message: userMessage
      }));

      // Listen for response
      const messageHandler = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'chat_response') {
          setIsThinking(false);
          setMessages(prev => [...prev, { type: 'assistant', text: data.message }]);
          
          // Handle actions
          if (data.action === 'open_page') {
            onPageChange(data.data.page);
          }

          // TTS if enabled
          if (data.tts && ttsEnabled && !muted && data.audio) {
            playAudio(data.audio);
          }

          wsRef.current.removeEventListener('message', messageHandler);
        }
      };

      wsRef.current.addEventListener('message', messageHandler);
      } else {
        // Fallback to HTTP
        try {
          const response = await axios.post(`${API_URL}/api/chat`, {
            message: userMessage
          });
          setIsThinking(false);
          setMessages(prev => [...prev, { type: 'assistant', text: response.data.message }]);
          
          if (response.data.action === 'open_page') {
            onPageChange(response.data.data.page);
          }
          
          // TTS if enabled
          if (response.data.tts && ttsEnabled && !muted) {
            // For HTTP, we'd need to call TTS endpoint separately
            // For now, skip TTS on HTTP fallback
          }
        } catch (error) {
          setIsThinking(false);
          setMessages(prev => [...prev, { type: 'assistant', text: 'Error: Could not connect to Emese.' }]);
        }
      }
  };

  const playAudio = (audioData) => {
    if (audioRef.current) {
      const audioBlob = new Blob([audioData], { type: 'audio/mpeg' });
      const audioUrl = URL.createObjectURL(audioBlob);
      audioRef.current.src = audioUrl;
      audioRef.current.play();
    }
  };

  return (
    <div className="d-flex flex-column h-100" style={{ backgroundColor: '#000000' }}>
      {/* Chat Messages */}
      <div className="flex-grow-1 overflow-auto p-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`mb-3 ${msg.type === 'user' ? 'text-end' : 'text-start'}`}
          >
            {msg.type === 'user' ? (
              <span
                className="d-inline-block p-3 rounded"
                style={{ backgroundColor: '#ff6600', color: '#000000', maxWidth: '70%' }}
              >
                {msg.text}
              </span>
            ) : (
              <span className="text-white">{msg.text}</span>
            )}
          </div>
        ))}
        {isThinking && (
          <div className="text-white">
            <span className="thinking-animation">Thinking...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Chat Input */}
      <div className="border-top border-secondary p-3">
        <form onSubmit={handleSend} className="d-flex align-items-center">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="form-control me-2"
            style={{ backgroundColor: '#000000', color: '#ffffff', borderColor: '#ff6600' }}
            placeholder="Type your message..."
          />
          <Toolbox
            ttsEnabled={ttsEnabled}
            setTtsEnabled={setTtsEnabled}
            muted={muted}
            setMuted={setMuted}
          />
          <button
            type="submit"
            className="btn"
            style={{ backgroundColor: '#ff6600', color: '#000000' }}
          >
            Send
          </button>
        </form>
      </div>

      <audio ref={audioRef} />
    </div>
  );
}

export default Chat;

