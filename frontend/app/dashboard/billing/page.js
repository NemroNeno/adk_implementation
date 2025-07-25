"use client";
import { useState, useEffect } from 'react';
import { useUserState } from '@/context/AuthContext';
import { api } from '@/context/AuthContext';
import { Box, Typography, Button, Paper, CircularProgress, Alert, Grid, List, ListItem, ListItemIcon, ListItemText } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

const plans = { // This should ideally be fetched from an API
    free: { name: 'Free', price: '$0/mo', features: ['2 Agents', '50,000 Tokens/mo'] },
    pro: { name: 'Pro', price: '$20/mo', features: ['20 Agents', '1,000,000 Tokens/mo', 'Priority Support'] }
};

export default function BillingPage() {
    const { user, loading: userLoading } = useUserState();
    const [loading, setLoading] = useState(false);
    
    const handleSubscribe = async () => {
        setLoading(true);
        try {
            const res = await api.post('/api/v1/subscriptions/create-checkout-session');
            window.location.href = res.data.url;
        } catch (err) {
            alert("Could not initiate subscription. Please try again.");
            setLoading(false);
        }
    };

    const handleManageBilling = async () => {
        setLoading(true);
        try {
            const res = await api.post('/api/v1/subscriptions/create-portal-session');
            window.location.href = res.data.url;
        } catch (err) {
            alert("Could not open billing portal. Please try again.");
            setLoading(false);
        }
    };

    if (userLoading) return <CircularProgress />;

    const currentPlan = user?.plan || 'free';
    const planDetails = plans[currentPlan];

    return (
        <Box>
            <Typography variant="h4" gutterBottom>Billing & Plan</Typography>
            <Grid container spacing={4}>
                <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 3, height: '100%' }}>
                        <Typography variant="h6">Current Plan</Typography>
                        <Typography variant="h4" color="primary" sx={{ my: 1 }}>{planDetails.name}</Typography>
                        <List>
                            {planDetails.features.map(feature => (
                                <ListItem key={feature} disableGutters>
                                    <ListItemIcon sx={{minWidth: 32}}><CheckCircleIcon color="success" fontSize="small"/></ListItemIcon>
                                    <ListItemText primary={feature} />
                                </ListItem>
                            ))}
                        </List>
                         {currentPlan === 'pro' ? (
                            <Button variant="contained" onClick={handleManageBilling} disabled={loading} sx={{mt: 2}}>Manage Billing & Invoices</Button>
                         ) : (
                            <Typography color="text.secondary">Upgrade to Pro for more features.</Typography>
                         )}
                    </Paper>
                </Grid>
                <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 3, height: '100%', border: currentPlan === 'pro' ? '' : '1px solid', borderColor: 'primary.main' }}>
                         <Typography variant="h6">Pro Plan</Typography>
                         <Typography variant="h4" sx={{ my: 1 }}>{plans.pro.price}</Typography>
                         <List>
                            {plans.pro.features.map(feature => (
                                <ListItem key={feature} disableGutters>
                                    <ListItemIcon sx={{minWidth: 32}}><CheckCircleIcon color="success" fontSize="small"/></ListItemIcon>
                                    <ListItemText primary={feature} />
                                </ListItem>
                            ))}
                        </List>
                        {currentPlan === 'free' && (
                            <Button variant="contained" color="primary" onClick={handleSubscribe} disabled={loading} sx={{mt: 2}}>
                                {loading ? 'Redirecting...' : 'Upgrade to Pro'}
                            </Button>
                        )}
                    </Paper>
                </Grid>
            </Grid>
        </Box>
    );
}