"use client";
import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { io } from 'socket.io-client';
import { Box, Typography, Alert, Stack, Divider, Chip, Tooltip, Skeleton, Fab, Avatar } from '@mui/material';
import MicIcon from '@mui/icons-material/Mic';
import MicOffIcon from '@mui/icons-material/MicOff';
import MemoryIcon from '@mui/icons-material/Memory';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import SpeechRecognition, { useSpeechRecognition } from 'react-speech-recognition';
import { api, useUserState } from '@/context/AuthContext';
import ChatMessage from '@/components/ChatMessage';

export default function ChatPage() {
    const { agentId } = useParams();
    const { user } = useUserState();
    const [socket, setSocket] = useState(null);
    const [agent, setAgent] = useState(null);
    const [messages, setMessages] = useState([]);
    const [error, setError] = useState('');
    const [isLoadingHistory, setIsLoadingHistory] = useState(true);
    const [isStreaming, setIsStreaming] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const messagesEndRef = useRef(null);

    const {
        transcript,
        listening,
        resetTranscript,
        browserSupportsSpeechRecognition
    } = useSpeechRecognition();

    const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });

    useEffect(() => {
        if (user) {
            Promise.all([
                api.get(`/api/v1/agents/${agentId}`),
                api.get(`/api/v1/agents/${agentId}/history`)
            ]).then(([agentRes, historyRes]) => {
                setAgent(agentRes.data);
                setMessages(historyRes.data);
            }).catch(() => setError("Failed to load agent data."))
              .finally(() => setIsLoadingHistory(false));
        }
    }, [agentId, user]);

    useEffect(() => {
        if (!isLoadingHistory && user) {
            const newSocket = io(process.env.NEXT_PUBLIC_API_URL, {
                transports: ['websocket'],
                path: '/socket.io',
            });

            setSocket(newSocket);

            newSocket.on('connect', () => {
                console.log('Connected');
                newSocket.emit('start_chat', {
                    agent_id: parseInt(agentId),
                    user_id: user.id,
                });
            });

            newSocket.on('token', ({ token }) => {
                if (!isStreaming) setIsStreaming(true);
                setMessages(prev => {
                    const last = prev[prev.length - 1];
                    if (last?.role === 'ai') {
                        last.content += token;
                        return [...prev];
                    } else {
                        return [...prev, { role: 'ai', content: token }];
                    }
                });
            });

            newSocket.on('stream_end', ({ metrics }) => {
                setMessages(prev => {
                    const last = prev[prev.length - 1];
                    if (last?.role === 'ai') Object.assign(last, metrics);
                    return [...prev];
                });
                setIsStreaming(false);
                setIsProcessing(false);
            });

            newSocket.on('error', (data) => {
                setError(data.message);
                setIsProcessing(false);
            });

            return () => newSocket.disconnect();
        }
    }, [isLoadingHistory, agentId, user, isStreaming]);

    useEffect(scrollToBottom, [messages]);

    const handleMicClick = () => {
        if (listening) {
            SpeechRecognition.stopListening();
            setIsProcessing(true);
            if (transcript.trim()) {
                const newHumanMessage = { role: 'human', content: transcript, timestamp: new Date().toISOString() };
                setMessages(prev => [...prev, newHumanMessage]);
                socket?.emit('chat_message', { message: transcript });
            } else {
                setIsProcessing(false);
            }
            resetTranscript();
        } else {
            resetTranscript();
            SpeechRecognition.startListening({ continuous: true });
        }
    };

    if (!browserSupportsSpeechRecognition && !isLoadingHistory) {
        return <Alert severity="error">This browser does not support speech recognition.</Alert>;
    }

    if (isLoadingHistory || !user || !agent) {
        return (
            <Box sx={{ p: 3 }}>
                <Skeleton variant="text" width={250} height={60} />
                <Skeleton variant="rectangular" width="100%" height={40} sx={{ my: 2 }} />
                <Skeleton variant="rectangular" width="100%" height="60vh" />
            </Box>
        );
    }

    return (
        <Stack sx={{ height: 'calc(100vh - 64px)', p: 2 }}>
            <Box>
                <Typography variant="h5">{agent.name}</Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>{agent.system_prompt}</Typography>
                <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
                    <Chip icon={<MemoryIcon />} label="Tools Enabled" size="small" />
                    {agent.tools?.length > 0 ? agent.tools.map(tool => (
                        <Tooltip key={tool} title={`This agent can use the ${tool} tool.`}>
                            <Chip label={tool.replace(/_/g, ' ')} size="small" variant="outlined" />
                        </Tooltip>
                    )) : <Chip label="None" size="small" variant="outlined" />}
                </Stack>
                <Divider />
            </Box>

            <Box sx={{ flexGrow: 1, overflowY: 'auto', p: 2 }}>
                {messages.map((msg, index) => <ChatMessage key={index} message={msg} />)}
                {listening && <Typography color="text.secondary"><em>{transcript}...</em></Typography>}
                {isStreaming && (
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <Avatar sx={{ bgcolor: 'primary.main', mx: 1 }}><SmartToyIcon /></Avatar>
                        <Typography variant="body1" color="text.secondary">Typing...</Typography>
                    </Box>
                )}
                <div ref={messagesEndRef} />
            </Box>

            {error && <Alert severity="error" onClose={() => setError('')}>{error}</Alert>}

            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', p: 2 }}>
                <Fab color={listening ? "secondary" : "primary"} onClick={handleMicClick} disabled={isProcessing || isStreaming}>
                    {listening ? <MicOffIcon /> : <MicIcon />}
                </Fab>
                <Typography variant="caption" sx={{ mt: 1 }}>
                    {isProcessing ? "Processing..." : listening ? "Listening... Click to stop." : "Click to speak."}
                </Typography>
            </Box>
        </Stack>
    );
}
