"use client";
import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { io } from 'socket.io-client';
import { Box, Typography, Alert, Stack, Divider, Chip, Tooltip, Skeleton, Fab, Avatar, LinearProgress } from '@mui/material';
import MicIcon from '@mui/icons-material/Mic';
import MicOffIcon from '@mui/icons-material/MicOff';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import ConstructionIcon from '@mui/icons-material/Construction';
import SpeechRecognition, { useSpeechRecognition } from 'react-speech-recognition';
import { api, useUserState } from '@/context/AuthContext';
import DashboardLayout from '@/components/DashboardLayout';
import ChatMessage from '@/components/ChatMessage';
import ChatInput from '@/components/ChatInput'; // We'll use a dedicated input component

export default function ChatPage() {
    const { agentId } = useParams();
    const { user } = useUserState();
    const [socket, setSocket] = useState(null);
    const [agent, setAgent] = useState(null);
    const [messages, setMessages] = useState([]);
    const [error, setError] = useState('');
    const [isLoadingHistory, setIsLoadingHistory] = useState(true);
    
    // NEW state for better UI feedback
    const [isStreaming, setIsStreaming] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const [toolStatus, setToolStatus] = useState(null); // e.g., "Using Tavily Search..."

    const messagesEndRef = useRef(null);
    const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });

    // Fetch initial agent and history data
    useEffect(() => {
        if (user && agentId) {
            setIsLoadingHistory(true);
            Promise.all([
                api.get(`/api/v1/agents/${agentId}`),
                api.get(`/api/v1/agents/${agentId}/history`)
            ]).then(([agentRes, historyRes]) => {
                setAgent(agentRes.data);
                setMessages(historyRes.data.map(msg => ({...msg, id: msg.id}))); // Ensure unique keys
            }).catch(() => setError("Failed to load agent data or history."))
              .finally(() => setIsLoadingHistory(false));
        }
    }, [agentId, user]);

    // Setup WebSocket connection and listeners
    useEffect(() => {
        if (!isLoadingHistory && user && agent) {
            // Connect to the correct namespace
            const newSocket = io(process.env.NEXT_PUBLIC_API_URL, {
                path: '/socket.io/',
                transports: ['websocket'],
                namespace: '/text'
            });

            setSocket(newSocket);

            newSocket.on('connect', () => {
                console.log('Socket.IO connected to /text namespace');
                newSocket.emit('start_chat', {
                    agent_id: parseInt(agentId, 10),
                    user_id: user.id,
                });
            });

            // --- CORRECTED EVENT HANDLERS ---
            newSocket.on('token', ({ token }) => {
                setIsProcessing(true); // We are now receiving a response
                setToolStatus(null);   // A tool is done, now we get text
                if (!isStreaming) setIsStreaming(true);

                setMessages(prev => {
                    const lastMsg = prev[prev.length - 1];
                    // If last message was from AI, append token. Otherwise, create new AI message.
                    if (lastMsg && lastMsg.role === 'ai') {
                        return [
                            ...prev.slice(0, -1),
                            { ...lastMsg, content: lastMsg.content + token }
                        ];
                    } else {
                        return [
                            ...prev,
                            { id: `ai-${Date.now()}`, role: 'ai', content: token }
                        ];
                    }
                });
            });

            newSocket.on('tool_start', ({ name }) => {
                // The backend says it's using a tool. Show this to the user.
                setToolStatus(`Using tool: ${name.replace(/_/g, ' ')}...`);
            });

            newSocket.on('stream_end', ({ metrics }) => {
                setIsStreaming(false);
                setIsProcessing(false);
                setToolStatus(null);
                // Optionally update the last message with final metrics
            });

            newSocket.on('error', (data) => {
                setError(data.message || 'An unknown error occurred.');
                setIsProcessing(false);
                setIsStreaming(false);
                setToolStatus(null);
            });
            
            newSocket.on('disconnect', () => {
                console.log('Socket.IO disconnected.');
            });

            return () => newSocket.disconnect();
        }
    }, [isLoadingHistory, agentId, user, agent]);

    useEffect(scrollToBottom, [messages]);

    const handleSendMessage = (messageText) => {
        if (!messageText.trim() || !socket || isProcessing) return;

        setError('');
        setIsProcessing(true);
        const newHumanMessage = { id: `human-${Date.now()}`, role: 'human', content: messageText, timestamp: new Date().toISOString() };
        setMessages(prev => [...prev, newHumanMessage]);
        
        socket.emit('chat_message', { message: messageText });
    };

    if (isLoadingHistory || !user || !agent) {
        return (
            <DashboardLayout>
                <Box sx={{ p: 3 }}>
                    <Skeleton variant="text" width={250} height={60} />
                    <Skeleton variant="rectangular" width="100%" height={40} sx={{ my: 2 }} />
                    <Skeleton variant="rectangular" width="100%" height="60vh" />
                </Box>
            </DashboardLayout>
        );
    }

    return (
        <DashboardLayout>
            <Stack sx={{ height: 'calc(100vh - 64px - 48px)', p: 2, position: 'relative' }}>
                {/* Header */}
                <Box>
                    <Typography variant="h5">{agent.name}</Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>{agent.system_prompt}</Typography>
                    <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
                        {agent.tools?.length > 0 ? agent.tools.map(tool => (
                            <Tooltip key={tool} title={`This agent can use the ${tool} tool.`}>
                                <Chip icon={<ConstructionIcon />} label={tool.replace(/_/g, ' ')} size="small" variant="outlined" />
                            </Tooltip>
                        )) : <Chip label="No tools assigned" size="small" />}
                    </Stack>
                    <Divider />
                </Box>

                {/* Chat History */}
                <Box sx={{ flexGrow: 1, overflowY: 'auto', p: 2 }}>
                    {messages.map((msg) => <ChatMessage key={msg.id} message={msg} />)}
                    <div ref={messagesEndRef} />
                </Box>
                
                {/* Status Bar */}
                <Box sx={{ height: '24px', display: 'flex', alignItems: 'center', justifyContent: 'center', mb:1 }}>
                    {isProcessing && !toolStatus && !isStreaming && <LinearProgress sx={{width: '100%'}} />}
                    {toolStatus && <Chip icon={<SmartToyIcon/>} label={toolStatus} size="small" color="secondary"/>}
                </Box>
                
                {error && <Alert severity="error" onClose={() => setError('')} sx={{ mb: 2 }}>{error}</Alert>}

                {/* Input Area */}
                <ChatInput onSendMessage={handleSendMessage} disabled={isProcessing} />
            </Stack>
        </DashboardLayout>
    );
}