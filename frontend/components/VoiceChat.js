import { useState, useEffect, useRef } from 'react';
import { io } from 'socket.io-client';

const VoiceChat = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [status, setStatus] = useState('Idle');

  const socketRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioPlayerRef = useRef(new Audio());
  const audioQueueRef = useRef([]);
  const isPlayingRef = useRef(false);

  useEffect(() => {
    // This connection logic is now perfect for the namespaced backend.
    const socket = io('http://localhost:8000/voice', {
      path: '/socket.io/',
      transports: ['websocket'],
    });
    socketRef.current = socket;

    socket.on('connect', () => {
      console.log('Connected to Voice WebSocket Namespace!');
      setIsConnected(true);
      setStatus('Connected. Ready to talk.');
    });

    socket.on('disconnect', () => {
      console.log('Disconnected from WebSocket server.');
      setIsConnected(false);
      setStatus('Disconnected.');
    });

    socket.on('response_audio', (audioChunk) => {
      const blob = new Blob([audioChunk], { type: 'audio/webm' });
      audioQueueRef.current.push(blob);
      // Kick off the playback chain if it's not already running.
      playNextInQueue();
    });

    socket.on('error', (error) => {
      console.error('Received error from server:', error.message);
      setStatus(`Error: ${error.message}`);
      if (isRecording) {
        stopRecording();
      }
    });

    // Cleanup function is perfect.
    return () => {
      socket.disconnect();
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        stopRecording();
      }
    };
  }, []); // Empty dependency array is correct.

  const playNextInQueue = () => {
    if (isPlayingRef.current || audioQueueRef.current.length === 0) {
      return;
    }
    isPlayingRef.current = true;
    setStatus('Agent is speaking...');
    
    const audioBlob = audioQueueRef.current.shift();
    const audioUrl = URL.createObjectURL(audioBlob);
    const audioPlayer = audioPlayerRef.current;
    
    audioPlayer.src = audioUrl;
    audioPlayer.play();

    // The robust, corrected onended handler
    audioPlayer.onended = () => {
      isPlayingRef.current = false;
      if (audioQueueRef.current.length > 0) {
        playNextInQueue();
      } else {
        setStatus('Connected. Ready to talk.');
      }
    };
  };

  const startRecording = async () => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      alert('Your browser does not support audio recording.');
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream, { mimeType: 'audio/webm' });

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0 && socketRef.current?.connected) {
          socketRef.current.emit('audio_stream', event.data);
        }
      };

      mediaRecorderRef.current.start(500); // Send data every 500ms
      setIsRecording(true);
      setStatus('Listening...');
    } catch (err) {
      console.error("Error accessing microphone:", err);
      setStatus("Microphone access denied.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
      // This is crucial for turning off the mic light. Correct.
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
    setIsRecording(false);
    setStatus('Processing...');
  };

  return (
    <div>
      <h2>ADK Voice Agent</h2>
      <p>Status: {status}</p>
      <button
        onClick={isRecording ? stopRecording : startRecording}
        disabled={!isConnected}
        style={{
          padding: '1rem',
          fontSize: '1.2rem',
          backgroundColor: isRecording ? '#d32f2f' : '#388e3c', // Using theme-like colors
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          cursor: isConnected ? 'pointer' : 'not-allowed',
          opacity: isConnected ? 1 : 0.6,
        }}
      >
        {isRecording ? 'Stop Talking' : 'Start Talking'}
      </button>
    </div>
  );
};

export default VoiceChat;