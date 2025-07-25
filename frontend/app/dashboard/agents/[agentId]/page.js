"use client";
import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { io } from 'socket.io-client';
import { Box, TextField, IconButton, Paper, Typography, CircularProgress, Alert, Stack, Divider, Chip, Tooltip, Skeleton } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import MemoryIcon from '@mui/icons-material/Memory';
import { api, useUserState } from '@/context/AuthContext';
import ChatMessage from '@/components/ChatMessage';

export default function ChatPage() {
    const { agentId } = useParams();
    const { user } = useUserState();
    const [socket, setSocket] = useState(null);
    const [agent, setAgent] = useState(null);
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [error, setError] = useState('');
    const [isLoadingHistory, setIsLoadingHistory] = useState(true);
    const [isStreaming, setIsStreaming] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        if (user) {
            Promise.all([
                api.get(`/api/v1/agents/${agentId}`),
                api.get(`/api/v1/agents/${agentId}/history`)
            ]).then(([agentRes, historyRes]) => {
                setAgent(agentRes.data);
                setMessages(historyRes.data);
            }).catch(err => setError("Failed to load agent data."))
              .finally(() => setIsLoadingHistory(false));
        }
    }, [agentId, user]);

    // ... (rest of the file is the same) ...

    // ... (rest of the file is the same) ...

    // ... (rest of the file is the same) ...

    useEffect(() => {
        if (!isLoadingHistory && user) {
            // --- WebSocket-only fix applied here ---
            const newSocket = io(process.env.NEXT_PUBLIC_API_URL, {
                transports: ['websocket'], // Enforce WebSocket only
            });
            // --- End WebSocket fix ---

            setSocket(newSocket);

            newSocket.on('connect', () => {
                console.log('Socket.IO successfully connected via WebSocket!');
                newSocket.emit('start_chat', {
                    agent_id: parseInt(agentId),
                    user_id: user.id,
                });
            });

            newSocket.on('connect_error', (err) => {
                console.error('Socket.IO connection error:', err);
                setError(`Failed to connect to chat server: ${err.message}`);
            });

            newSocket.on('disconnect', () => {
                console.log('Socket.IO disconnected.');
            });

            newSocket.on('token', (data) => {
                if (!isStreaming) setIsStreaming(true);
                setMessages(prev => {
                    const last = prev[prev.length - 1];
                    if (last?.role === 'ai' && !last.response_time_seconds) {
                        last.content += data.token;
                        return [...prev];
                    } else {
                        return [...prev, { role: 'ai', content: data.token }];
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
            });

            newSocket.on('error', (data) => setError(data.message));

            return () => {
                newSocket.disconnect();
            };
        }
    }, [isLoadingHistory, agentId, user, isStreaming]);


// ... (rest of the file is the same) ...

// ... (rest of the file is the same) ...

// ... (rest of the file is the same) ...
    useEffect(scrollToBottom, [messages]);

    const handleSendMessage = useCallback((e) => {
        e.preventDefault();
        if (input.trim() && socket && !isStreaming) {
            const newHumanMessage = { role: 'human', content: input, timestamp: new Date().toISOString() };
            setMessages(prev => [...prev, newHumanMessage]);
            socket.emit('chat_message', { message: input });
            setInput('');
        }
    }, [input, socket, isStreaming]);

    if (isLoadingHistory || !user || !agent) {
        // ... Skeleton loading UI is unchanged ...
        return <Box sx={{ p: 3 }}><Skeleton variant="text" width={250} height={60} /><Skeleton variant="rectangular" width="100%" height={40} sx={{my:2}} /><Skeleton variant="rectangular" width="100%" height="60vh" /></Box>;
    }

    return (
        // ... The rest of the JSX is unchanged ...
        <Stack sx={{ height: 'calc(100vh - 64px)', p: 2 }}>
            <Box>
                <Typography variant="h5">{agent.name}</Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>{agent.system_prompt}</Typography>
                <Stack direction="row" spacing={1} sx={{mb: 2}}>
                    <Chip icon={<MemoryIcon />} label="Tools Enabled" size="small" />
                    {agent.tools?.length > 0 ? agent.tools.map(tool => (<Tooltip key={tool} title={`This agent can use the ${tool} tool.`}><Chip label={tool.replace(/_/g, ' ')} size="small" variant="outlined" /></Tooltip>)) : <Chip label="None" size="small" variant="outlined" />}
                </Stack>
                <Divider />
            </Box>
            <Box sx={{ flexGrow: 1, overflowY: 'auto', p: 2 }}>
                {messages.map((msg, index) => <ChatMessage key={index} message={msg} />)}
                {isStreaming && (<Box sx={{display: 'flex', alignItems: 'center', justifyContent: 'flex-start', mb: 2}}><Avatar sx={{ bgcolor: 'primary.main', mx: 1 }}><SmartToyIcon /></Avatar><Typography variant="body1" color="text.secondary">Typing...</Typography></Box>)}
                <div ref={messagesEndRef} />
            </Box>
            {error && <Alert severity="error" onClose={() => setError('')}>{error}</Alert>}
            <Paper component="form" onSubmit={handleSendMessage} sx={{ p: '2px 4px', display: 'flex', alignItems: 'center', mt: 1 }}>
                <TextField sx={{ ml: 1, flex: 1 }} placeholder="Ask your agent a question..." value={input} onChange={(e) => setInput(e.target.value)} multiline maxRows={5} variant="standard" InputProps={{ disableUnderline: true }} disabled={isStreaming} />
                <IconButton type="submit" color="primary" sx={{ p: '10px' }} disabled={isStreaming || !input.trim()}><SendIcon /></IconButton>
            </Paper>
        </Stack>
    );
}