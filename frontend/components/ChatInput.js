"use client";
import { useState } from 'react';
import { useSpeechRecognition, SpeechRecognition } from 'react-speech-recognition';
import { Box, TextField, IconButton, Tooltip } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import MicIcon from '@mui/icons-material/Mic';
import MicOffIcon from '@mui/icons-material/MicOff';

export default function ChatInput({ onSendMessage, disabled }) {
  const [inputValue, setInputValue] = useState('');
  const { transcript, listening, resetTranscript, browserSupportsSpeechRecognition } = useSpeechRecognition();

  useState(() => {
    setInputValue(transcript);
  }, [transcript]);

  const handleSend = () => {
    if (inputValue.trim()) {
      onSendMessage(inputValue);
      setInputValue('');
      resetTranscript();
    }
  };

  const handleMicClick = () => {
    if (listening) {
      SpeechRecognition.stopListening();
      handleSend(); // Send whatever was transcribed
    } else {
      resetTranscript();
      SpeechRecognition.startListening({ continuous: true });
    }
  };

  if (!browserSupportsSpeechRecognition) {
      return <Typography color="error">Speech recognition not supported.</Typography>;
  }

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', p: 1, borderTop: 1, borderColor: 'divider' }}>
      <TextField
        fullWidth
        variant="outlined"
        size="small"
        placeholder="Type or use the mic to talk to your agent..."
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey ? (e.preventDefault(), handleSend()) : null}
        disabled={disabled}
        multiline
        maxRows={5}
      />
      <Tooltip title={listening ? 'Stop Listening' : 'Use Microphone'}>
        <IconButton color={listening ? 'secondary' : 'primary'} onClick={handleMicClick} disabled={disabled && !listening}>
          {listening ? <MicOffIcon /> : <MicIcon />}
        </IconButton>
      </Tooltip>
      <Tooltip title="Send Message">
        <span>
          <IconButton color="primary" onClick={handleSend} disabled={disabled || !inputValue.trim()}>
            <SendIcon />
          </IconButton>
        </span>
      </Tooltip>
    </Box>
  );
}