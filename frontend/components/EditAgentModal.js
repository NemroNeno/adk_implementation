"use client";
import { useState, useEffect } from 'react';
import { Button, Dialog, DialogActions, DialogContent, DialogTitle, TextField, Box, CircularProgress, Alert, FormGroup, FormControlLabel, Checkbox, Typography, Divider } from '@mui/material';
import { api } from '@/context/AuthContext';

export default function EditAgentModal({ open, handleClose, agent, onAgentUpdated }) {
    const [name, setName] = useState('');
    const [systemPrompt, setSystemPrompt] = useState('');
    const [availableTools, setAvailableTools] = useState([]);
    const [selectedTools, setSelectedTools] = useState(new Set());
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        // When the modal opens and we have an agent to edit...
        if (open && agent) {
            // ...pre-fill the form with the agent's current data.
            setName(agent.name);
            setSystemPrompt(agent.system_prompt);
            setSelectedTools(new Set(agent.tools || []));
            
            // Fetch the list of all available tools
            api.get('/api/v1/tools/')
                .then(res => setAvailableTools(res.data))
                .catch(err => setError("Could not load available tools."));
        }
    }, [open, agent]);

    const handleToolToggle = (langchainKey) => {
        const newSelection = new Set(selectedTools);
        if (newSelection.has(langchainKey)) newSelection.delete(langchainKey);
        else newSelection.add(langchainKey);
        setSelectedTools(newSelection);
    };

    const handleSubmit = async () => {
        if (!name || !systemPrompt) return setError("Name and Prompt are required.");
        
        setLoading(true);
        setError('');
        try {
            const payload = {
                name,
                system_prompt: systemPrompt,
                tools: Array.from(selectedTools)
            };
            const response = await api.put(`/api/v1/agents/${agent.id}`, payload);
            onAgentUpdated(response.data); // Notify the parent page of the update
            handleClose();
        } catch (err) {
            setError(err.response?.data?.detail || "Failed to update agent.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onClose={handleClose} fullWidth maxWidth="sm">
            <DialogTitle>Edit Agent: {agent?.name}</DialogTitle>
            <DialogContent>
                <Box component="form" sx={{ mt: 2 }}>
                    <TextField autoFocus margin="dense" label="Agent Name" value={name} onChange={(e) => setName(e.target.value)} fullWidth />
                    <TextField margin="dense" label="System Prompt" multiline rows={6} value={systemPrompt} onChange={(e) => setSystemPrompt(e.target.value)} fullWidth />
                    
                    <Divider sx={{ my: 2 }} />
                    <Typography fontWeight="bold">Assign Tools</Typography>
                    <FormGroup>
                        {availableTools.map((tool) => (
                            <FormControlLabel
                                key={tool.id}
                                control={<Checkbox checked={selectedTools.has(tool.langchain_key)} onChange={() => handleToolToggle(tool.langchain_key)} />}
                                label={<Box><Typography>{tool.name}</Typography><Typography variant="caption">{tool.description}</Typography></Box>}
                            />
                        ))}
                    </FormGroup>
                    {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
                </Box>
            </DialogContent>
            <DialogActions>
                <Button onClick={handleClose}>Cancel</Button>
                <Button onClick={handleSubmit} variant="contained" disabled={loading}>
                    {loading ? <CircularProgress size={24} /> : 'Save Changes'}
                </Button>
            </DialogActions>
        </Dialog>
    );
}