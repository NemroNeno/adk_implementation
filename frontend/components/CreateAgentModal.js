"use client";
import { useState, useEffect } from 'react';
import { Button, Dialog, DialogActions, DialogContent, DialogTitle, TextField, Box, CircularProgress, Alert, FormGroup, FormControlLabel, Checkbox, Typography, Divider } from '@mui/material';
import { api } from '@/context/AuthContext';

export default function CreateAgentModal({ open, handleClose, onAgentCreated }) {
    const [name, setName] = useState('');
    const [systemPrompt, setSystemPrompt] = useState('');
    const [availableTools, setAvailableTools] = useState([]);
    const [selectedTools, setSelectedTools] = useState({}); // Use an object for easier state management
    const [loading, setLoading] = useState(false);
    const [loadingTools, setLoadingTools] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        if (open) {
            // Reset state every time the modal opens
            setName('');
            setSystemPrompt('');
            setSelectedTools({});
            setError('');
            
            setLoadingTools(true);
            api.get('/api/v1/tools/')
                .then(res => {
                    setAvailableTools(res.data);
                    // Initialize selectedTools state based on fetched tools
                    const initialSelection = {};
                    res.data.forEach(tool => {
                        initialSelection[tool.langchain_key] = false;
                    });
                    setSelectedTools(initialSelection);
                })
                .catch(err => setError("Could not load available tools."))
                .finally(() => setLoadingTools(false));
        }
    }, [open]);

    // --- THE FIX IS HERE: A more standard React onChange handler ---
    const handleToolToggle = (event) => {
        setSelectedTools({
            ...selectedTools,
            [event.target.name]: event.target.checked,
        });
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        if (!name || !systemPrompt) {
            setError("Name and System Prompt are required.");
            return;
        }
        setLoading(true);
        setError('');
        try {
            // Filter out the tools that are actually selected
            const enabledToolKeys = Object.keys(selectedTools).filter(key => selectedTools[key]);
            
            const payload = {
                name: name,
                system_prompt: systemPrompt,
                tools: enabledToolKeys
            };
            const response = await api.post('/api/v1/agents/', payload);
            onAgentCreated(response.data);
            handleClose();
        } catch (err) {
            setError(err.response?.data?.detail || "Failed to create agent.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onClose={handleClose} fullWidth maxWidth="sm">
            <Box component="form" onSubmit={handleSubmit}>
                <DialogTitle>Create New AI Agent</DialogTitle>
                <DialogContent>
                    <TextField autoFocus margin="dense" id="name" label="Agent Name" required fullWidth value={name} onChange={(e) => setName(e.target.value)} sx={{mt:1}}/>
                    <TextField margin="dense" id="system-prompt" label="System Prompt" multiline rows={6} required fullWidth value={systemPrompt} onChange={(e) => setSystemPrompt(e.target.value)} />
                    <Divider sx={{ my: 2 }} />
                    <Typography fontWeight="bold">Assign Tools</Typography>
                    
                    {loadingTools ? <CircularProgress sx={{ my: 1 }} /> : availableTools.length > 0 ? (
                        <FormGroup>
                            {availableTools.map((tool) => (
                                <FormControlLabel
                                    key={tool.id}
                                    control={
                                        <Checkbox
                                            // --- THE FIX IS HERE ---
                                            checked={selectedTools[tool.langchain_key] || false}
                                            onChange={handleToolToggle}
                                            name={tool.langchain_key}
                                        />
                                    }
                                    label={<Box><Typography>{tool.name}</Typography><Typography variant="caption" color="text.secondary">{tool.description}</Typography></Box>}
                                />
                            ))}
                        </FormGroup>
                    ) : ( <Typography variant="body2" color="text.secondary" sx={{ my: 1 }}>No tools available.</Typography> )}
                    
                    {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleClose}>Cancel</Button>
                    <Button type="submit" variant="contained" disabled={loading}>
                        {loading ? <CircularProgress size={24} /> : 'Create Agent'}
                    </Button>
                </DialogActions>
            </Box>
        </Dialog>
    );
}