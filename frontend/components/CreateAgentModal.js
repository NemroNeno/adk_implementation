"use client";
import { useState, useEffect } from 'react';
import { Button, Dialog, DialogActions, DialogContent, DialogTitle, TextField, Box, CircularProgress, Alert, FormGroup, FormControlLabel, Checkbox, Typography, Divider } from '@mui/material';
import { api } from '@/context/AuthContext';

export default function CreateAgentModal({ open, handleClose, onAgentCreated }) {
    const [name, setName] = useState('');
    const [systemPrompt, setSystemPrompt] = useState('');
    const [availableTools, setAvailableTools] = useState([]);
    // FIX: Use an object for checkbox state, not a Set
    const [selectedTools, setSelectedTools] = useState({});
    const [loading, setLoading] = useState(false);
    const [loadingTools, setLoadingTools] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        if (open) {
            // Reset form state
            setName('');
            setSystemPrompt('');
            setError('');
            setLoadingTools(true);
            api.get('/api/v1/tools/')
                .then(res => {
                    setAvailableTools(res.data);
                    // Initialize selectedTools state as an object of booleans
                    const initialSelection = {};
                    res.data.forEach(tool => {
                        initialSelection[tool.function_name] = false; // Use function_name as the key
                    });
                    setSelectedTools(initialSelection);
                })
                .catch(err => setError("Could not load available tools."))
                .finally(() => setLoadingTools(false));
        }
    }, [open]);

    // FIX: Correct handler for checkbox changes
    const handleToolToggle = (event) => {
        setSelectedTools(prev => ({
            ...prev,
            [event.target.name]: event.target.checked,
        }));
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        setLoading(true);
        setError('');
        try {
            // Filter for tools where the value is true
            const enabledToolKeys = Object.keys(selectedTools).filter(key => selectedTools[key]);
            const payload = { name, system_prompt: systemPrompt, tools: enabledToolKeys };
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
                    {/* ... TextFields are fine ... */}
                    <TextField autoFocus margin="dense" id="name" label="Agent Name" required fullWidth value={name} onChange={(e) => setName(e.target.value)} sx={{mt:1}}/>
                    <TextField margin="dense" id="system-prompt" label="System Prompt" multiline rows={6} required fullWidth value={systemPrompt} onChange={(e) => setSystemPrompt(e.target.value)} />
                    <Divider sx={{ my: 2 }} />
                    <Typography fontWeight="bold">Assign Tools</Typography>
                    
                    {loadingTools ? <CircularProgress sx={{ my: 1 }} /> : (
                        <FormGroup>
                            {availableTools.map((tool) => (
                                <FormControlLabel
                                    key={tool.id}
                                    control={
                                        <Checkbox
                                            // FIX: Correctly reference the state object
                                            checked={selectedTools[tool.function_name] || false}
                                            onChange={handleToolToggle}
                                            name={tool.function_name} // Name should be the key
                                        />
                                    }
                                    label={<Box><Typography>{tool.name}</Typography><Typography variant="caption" color="text.secondary">{tool.description}</Typography></Box>}
                                />
                            ))}
                        </FormGroup>
                    )}
                    {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleClose}>Cancel</Button>
                    <Button type="submit" variant="contained" disabled={loading}>{loading ? <CircularProgress size={24} /> : 'Create Agent'}</Button>
                </DialogActions>
            </Box>
        </Dialog>
    );
}