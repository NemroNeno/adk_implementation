"use client";
import { useState, useEffect } from 'react';
import { useUserState, useAuthActions } from '@/context/AuthContext';
import { api } from '@/context/AuthContext';
import { Box, Typography, TextField, Button, Paper, CircularProgress, Alert } from '@mui/material';

export default function ProfilePage() {
    const { user } = useUserState();
    const { loginWithToken } = useAuthActions(); // To refresh user state after update
    const [fullName, setFullName] = useState('');
    const [email, setEmail] = useState('');
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState('');
    const [error, setError] = useState('');

    useEffect(() => {
        if (user) {
            setFullName(user.full_name || '');
            setEmail(user.email || '');
        }
    }, [user]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setSuccess('');
        setError('');
        try {
            const payload = { full_name: fullName };
            await api.put('/api/v1/users/me', payload);
            setSuccess('Profile updated successfully!');
            // Refresh the user state in the context
            const token = localStorage.getItem('token');
            if (token) {
                await loginWithToken(token);
            }
        } catch (err) {
            setError(err.response?.data?.detail || "Failed to update profile.");
        } finally {
            setLoading(false);
        }
    };

    if (!user) {
        return <CircularProgress />;
    }

    return (
        <Box>
            <Typography variant="h4" gutterBottom>My Profile</Typography>
            <Paper component="form" onSubmit={handleSubmit} sx={{ p: 3, maxWidth: 600 }}>
                <Typography variant="h6" gutterBottom>User Details</Typography>
                <TextField
                    label="Full Name"
                    variant="outlined"
                    fullWidth
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    sx={{ mb: 2 }}
                />
                <TextField
                    label="Email Address"
                    variant="outlined"
                    fullWidth
                    value={email}
                    disabled // Don't allow email changes for now
                    sx={{ mb: 2 }}
                />
                
                {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
                {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

                <Button type="submit" variant="contained" disabled={loading}>
                    {loading ? <CircularProgress size={24} /> : 'Save Changes'}
                </Button>
            </Paper>
        </Box>
    );
}