"use client";
import { useState, useEffect } from 'react';
import { Box, Typography, Button, Paper, CircularProgress, Alert, TextField, List, ListItem, ListItemText, IconButton, Divider } from '@mui/material';
import KeyIcon from '@mui/icons-material/Key';
import DeleteIcon from '@mui/icons-material/Delete';
import { api } from '@/context/AuthContext';

export default function IntegrationsPage() {
    const [integrations, setIntegrations] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    
    // State for the new integration form
    const [serviceName, setServiceName] = useState('');
    const [token, setToken] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    const fetchIntegrations = () => {
        setLoading(true);
        api.get('/api/v1/integrations/')
            .then(res => setIntegrations(res.data))
            .catch(err => setError("Could not fetch integrations."))
            .finally(() => setLoading(false));
    };

    useEffect(() => {
        fetchIntegrations();
    }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!serviceName || !token) {
            setError("Service Name and Token are required.");
            return;
        }
        setIsSubmitting(true);
        setError('');
        try {
            const payload = { service_name: serviceName, token: token };
            await api.post('/api/v1/integrations/', payload);
            // Clear form and refetch the list
            setServiceName('');
            setToken('');
            fetchIntegrations();
        } catch (err) {
            setError(err.response?.data?.detail || "Failed to add integration.");
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleDelete = async (integrationId) => {
        if (window.confirm("Are you sure you want to revoke this token?")) {
            try {
                await api.delete(`/api/v1/integrations/${integrationId}`);
                // Remove from the list for instant UI update
                setIntegrations(prev => prev.filter(i => i.id !== integrationId));
            } catch (err) {
                setError(err.response?.data?.detail || "Failed to delete integration.");
            }
        }
    };

    return (
        <Box>
            <Typography variant="h4" gutterBottom>My Integrations</Typography>
            <Typography color="text.secondary" sx={{ mb: 3 }}>
                Securely store your API keys and tokens for third-party services. Your agents can then be configured to use these integrations.
            </Typography>

            {/* Form to add a new integration */}
            <Paper component="form" onSubmit={handleSubmit} sx={{ p: 2, mb: 4 }}>
                <Typography variant="h6" gutterBottom>Add New Integration</Typography>
                <TextField
                    label="Service Name (e.g., NOTION, GITHUB)"
                    variant="outlined"
                    fullWidth
                    value={serviceName}
                    onChange={(e) => setServiceName(e.target.value)}
                    sx={{ mb: 2 }}
                    helperText="A unique name for your integration."
                />
                <TextField
                    label="API Key or Token"
                    variant="outlined"
                    type="password"
                    fullWidth
                    value={token}
                    onChange={(e) => setToken(e.target.value)}
                    sx={{ mb: 2 }}
                    helperText="Your token will be stored encrypted."
                />
                {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
                <Button type="submit" variant="contained" disabled={isSubmitting}>
                    {isSubmitting ? <CircularProgress size={24} /> : 'Save Integration'}
                </Button>
            </Paper>

            {/* List of existing integrations */}
            <Typography variant="h6" gutterBottom>Saved Integrations</Typography>
            {loading ? <CircularProgress /> : (
                <Paper>
                    <List>
                        {integrations.length > 0 ? integrations.map((integration) => (
                            <ListItem
                                key={integration.id}
                                secondaryAction={
                                    <IconButton edge="end" aria-label="delete" onClick={() => handleDelete(integration.id)}>
                                        <DeleteIcon />
                                    </IconButton>
                                }
                            >
                                <KeyIcon sx={{ mr: 2, color: 'text.secondary' }} />
                                <ListItemText
                                    primary={integration.service_name}
                                    secondary={`Added on: ${new Date(integration.created_at).toLocaleDateString()}`}
                                />
                            </ListItem>
                        )) : (
                            <ListItem>
                                <ListItemText primary="No integrations added yet." />
                            </ListItem>
                        )}
                    </List>
                </Paper>
            )}
        </Box>
    );
}