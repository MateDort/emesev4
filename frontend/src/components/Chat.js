import React, { useState, useEffect, useRef, useCallback } from 'react';
import Toolbox from './Toolbox';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function Chat({ onPageChange, wsRef }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [muted, setMuted] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [wakeWordDetected, setWakeWordDetected] = useState(false);
  const [isListeningActive, setIsListeningActive] = useState(false);
  const [voiceAvailable, setVoiceAvailable] = useState(true); // Backend handles wake word detection
  const messagesEndRef = useRef(null);
  const audioRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const isRecordingRef = useRef(false);

  useEffect(() => {
    const cachedMessages = localStorage.getItem('chatMessages');
    if (cachedMessages) {
      setMessages(JSON.parse(cachedMessages));
    }

    const fetchHistory = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/chat/history`);
        const history = response.data.history || [];
        const flattened = [];
        history.forEach(entry => {
          if (entry.user) {
            flattened.push({ type: 'user', text: entry.user });
          }
          if (entry.assistant) {
            flattened.push({ type: 'assistant', text: entry.assistant });
          }
        });
        if (flattened.length > 0) {
          setMessages(flattened);
        }
      } catch (error) {
        console.error('Error loading chat history:', error);
      }
    };

    fetchHistory();
  }, []);

  const startRecording = useCallback(async () => {
    if (isRecordingRef.current) {
      console.log('⚠️ Already recording, ignoring start request');
      return;
    }
    
    console.log('🎙️ Starting audio recording...');
    console.log('📋 Checking MediaRecorder support...');
    
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      console.error('❌ getUserMedia not supported in this browser');
      setIsRecording(false);
      isRecordingRef.current = false;
      return;
    }
    
    isRecordingRef.current = true;
    try {
      console.log('🎤 Requesting microphone access...');
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      console.log('✅ Microphone access granted');
      
      // Check MediaRecorder support
      if (!window.MediaRecorder) {
        console.error('❌ MediaRecorder not supported in this browser');
        stream.getTracks().forEach(track => track.stop());
        setWakeWordDetected(false);
        setIsRecording(false);
        isRecordingRef.current = false;
        return;
      }
      
      console.log('📹 Creating MediaRecorder...');
      let mediaRecorder;
      try {
        mediaRecorder = new MediaRecorder(stream, {
          mimeType: 'audio/webm;codecs=opus'
        });
        console.log('✅ MediaRecorder created successfully');
      } catch (mimeError) {
        console.warn('⚠️ WebM codec not supported, trying default...');
        try {
          mediaRecorder = new MediaRecorder(stream);
          console.log('✅ MediaRecorder created with default codec');
        } catch (defaultError) {
          console.error('❌ Failed to create MediaRecorder:', defaultError);
          stream.getTracks().forEach(track => track.stop());
          setWakeWordDetected(false);
          setIsRecording(false);
          isRecordingRef.current = false;
          return;
        }
      }

      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };


      mediaRecorder.start();
      mediaRecorderRef.current = mediaRecorder;
      setIsRecording(true);
      console.log('🔴 Recording started - speak now!');
      
      // Notify backend that recording started
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          type: 'start_recording'
        }));
      }
      
      // Set up stop handler
      mediaRecorder.onstop = async () => {
        console.log('🛑 Recording stopped, processing audio...');
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        console.log(`📦 Audio blob size: ${audioBlob.size} bytes`);
        
        if (audioBlob.size > 0) {
          await sendVoiceMessage(audioBlob);
        } else {
          console.warn('⚠️ No audio data recorded');
        }
        
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
        
        // Reset state - backend will continue listening for wake word
        setWakeWordDetected(false);
        setIsRecording(false);
        isRecordingRef.current = false;
        setIsListeningActive(true); // Backend is always listening
        audioChunksRef.current = [];
      };
      
      // Auto-stop after 8 seconds max (user can also click Stop button)
      setTimeout(() => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
          console.log('⏱️ Auto-stopping recording after 8 seconds');
          mediaRecorderRef.current.stop();
        }
      }, 8000);
    } catch (error) {
      console.error('❌ Error accessing microphone:', error);
      console.error('Error name:', error.name);
      console.error('Error message:', error.message);
      
      if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
        console.error('❌ Microphone permission denied. Please allow microphone access in your browser settings.');
      } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
        console.error('❌ No microphone found. Please connect a microphone.');
      } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
        console.error('❌ Microphone is already in use by another application.');
      }
      
      setWakeWordDetected(false);
      setIsRecording(false);
      isRecordingRef.current = false;
      setIsListeningActive(true); // Backend continues listening
    }
  }, [wsRef, ttsEnabled, muted, onPageChange]);

  // Listen for wake word detection and other messages from backend via WebSocket
  useEffect(() => {
    const ws = wsRef?.current;
    if (!ws) return;

    const handleWebSocketMessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('📨 WebSocket message received:', data.type);
        
        if (data.type === 'connection_established') {
          console.log('✅', data.message);
          setIsListeningActive(true);
        } else if (data.type === 'wake_word_detected') {
          console.log('✅ Wake word detected from backend:', data.message);
          
          // Only start recording if not already recording
          // Use ref instead of state for immediate check
          if (!isRecordingRef.current) {
            setWakeWordDetected(true);
            setIsListeningActive(true);
            
            // Start recording immediately
            console.log('🎙️ Starting recording after wake word detection...');
            try {
              startRecording().catch(error => {
                console.error('❌ Error starting recording:', error);
              });
            } catch (error) {
              console.error('❌ Error calling startRecording:', error);
            }
          } else {
            console.log('⚠️ Already recording, ignoring wake word');
          }
        } else if (data.type === 'automatic_task') {
          setMessages(prev => [
            ...prev,
            { type: 'system', text: data.message }
          ]);
        }
      } catch (e) {
        console.error('Error handling websocket message:', e);
      }
    };

    ws.addEventListener('message', handleWebSocketMessage);
    
    // Set listening as active (backend is always listening)
    setIsListeningActive(true);
    console.log('🎤 Listening for wake word via backend (pvporcupine)...');
    
    return () => {
      ws.removeEventListener('message', handleWebSocketMessage);
    };
  }, [wsRef, startRecording]);

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
  };

  const sendVoiceMessage = async (audioBlob) => {
    try {
      console.log('📤 Sending voice message to backend...');
      // Convert blob to base64
      const reader = new FileReader();
      reader.onloadend = async () => {
        const base64Audio = reader.result.split(',')[1]; // Remove data:audio/webm;base64, prefix
        console.log(`📡 Sending ${base64Audio.length} characters of base64 audio`);
        
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({
            type: 'voice',
            audio: base64Audio
          }));
          console.log('✅ Voice message sent via WebSocket');

          // Listen for response
          const messageHandler = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'voice_response') {
              setIsThinking(false);
              setMessages(prev => [
                ...prev,
                { type: 'user', text: data.transcription },
                { type: 'assistant', text: data.message }
              ]);
              
              // Handle actions
              if (data.action === 'open_page') {
                onPageChange(data.data.page);
              }

              // Play audio response if available
              if (data.audio && ttsEnabled && !muted) {
                playAudio(data.audio);
              }

              wsRef.current.removeEventListener('message', messageHandler);
            }
          };

          wsRef.current.addEventListener('message', messageHandler);
          setIsThinking(true);
        } else {
          // Fallback: convert to text first, then send as chat
          console.warn('WebSocket not available, cannot send voice message');
        }
      };
      reader.readAsDataURL(audioBlob);
    } catch (error) {
      console.error('Error sending voice message:', error);
      setIsThinking(false);
    }
  };



  useEffect(() => {
    scrollToBottom();
    localStorage.setItem('chatMessages', JSON.stringify(messages));
  }, [messages]);

  useEffect(() => {
    // Cleanup on unmount
    return () => {
      // Stop media recorder
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        try {
          mediaRecorderRef.current.stop();
        } catch (error) {
          // Ignore errors on cleanup
        }
      }
    };
  }, []);

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
      // audioData might be base64 string or ArrayBuffer
      let audioBlob;
      if (typeof audioData === 'string') {
        // Base64 string
        const binaryString = atob(audioData);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }
        audioBlob = new Blob([bytes], { type: 'audio/mpeg' });
      } else {
        // ArrayBuffer
        audioBlob = new Blob([audioData], { type: 'audio/mpeg' });
      }
      const audioUrl = URL.createObjectURL(audioBlob);
      audioRef.current.src = audioUrl;
      
      // Play audio with user interaction handling
      const playPromise = audioRef.current.play();
      if (playPromise !== undefined) {
        playPromise
          .then(() => {
            console.log('✅ Audio playback started');
          })
          .catch(error => {
            // Handle autoplay policy - user interaction required
            if (error.name === 'NotAllowedError') {
              console.warn('⚠️ Autoplay blocked - user interaction required. Audio will play on next interaction.');
              // Try to play on next user interaction
              const playOnInteraction = () => {
                audioRef.current.play().catch(e => {
                  console.error('Error playing audio after interaction:', e);
                });
                document.removeEventListener('click', playOnInteraction);
                document.removeEventListener('keydown', playOnInteraction);
              };
              document.addEventListener('click', playOnInteraction, { once: true });
              document.addEventListener('keydown', playOnInteraction, { once: true });
            } else {
              console.error('Error playing audio:', error);
            }
          });
      }
    }
  };

  return (
    <div className="d-flex flex-column h-100 chat-surface-light p-3">
      {/* Chat Messages */}
      <div className="flex-grow-1 overflow-auto p-3 scroll-pane">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`mb-3 ${msg.type === 'user' ? 'text-end' : 'text-start'}`}
          >
            {msg.type === 'user' ? (
              <span
                className="d-inline-block p-3 rounded message-bubble-user"
                style={{ maxWidth: '70%' }}
              >
                {msg.text}
              </span>
            ) : msg.type === 'system' ? (
              <span className="d-inline-block p-3 message-bubble-system" style={{ maxWidth: '70%' }}>
                {msg.text}
              </span>
            ) : (
              <span className="text-dark">{msg.text}</span>
            )}
          </div>
        ))}
        {isThinking && (
          <div className="text-dark">
            <span className="thinking-animation">Thinking...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Voice Status Indicator - Always show when voice is available */}
      {voiceAvailable && (
        <div className="border-top mac-divider p-2">
          <div className="d-flex align-items-center gap-2 small">
            {isRecording ? (
              <>
                <span className="text-danger">
                  <span className="spinner-border spinner-border-sm me-2" role="status" />
                  Recording... (speak now)
                </span>
                <button
                  onClick={stopRecording}
                  className="btn btn-sm btn-outline-danger ms-auto"
                >
                  Stop
                </button>
              </>
            ) : isListeningActive ? (
              <span className="text-info" style={{ fontSize: '0.75rem' }}>
                🎤 Listening... Say "computer"
              </span>
            ) : (
              <span className="text-muted" style={{ fontSize: '0.75rem' }}>
                💬 Voice ready - Say "computer" to activate
              </span>
            )}
          </div>
        </div>
      )}

      {/* Chat Input */}
      <div className="border-top mac-divider p-3 mt-3">
        <form onSubmit={handleSend} className="d-flex align-items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="form-control chat-input-light"
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
            className="btn mac-button fw-semibold"
            style={{ borderColor: '#8aa9d6' }}
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

