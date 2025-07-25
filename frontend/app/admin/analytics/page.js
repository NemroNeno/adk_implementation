"use client";
import { useState, useEffect } from 'react';
import { Typography, Box, Paper, Grid, CircularProgress, Alert } from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import AdminDashboardLayout from '@/components/AdminDashboardLayout';
import { api } from '@/context/AuthContext';
import PeopleIcon from '@mui/icons-material/People';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import MessageIcon from '@mui/icons-material/Message';
import SpeedIcon from '@mui/icons-material/Speed';
import TokenIcon from '@mui/icons-material/Token';

// A reusable Stat Card component
const StatCard = ({ title, value, icon }) => (
    <Paper sx={{ p: 2, display: 'flex', alignItems: 'center', height: '100%' }}>
        {icon && <Box sx={{ mr: 2, color: 'primary.main' }}>{icon}</Box>}
        <Box>
            <Typography color="text.secondary">{title}</Typography>
            <Typography variant="h5" component="p" fontWeight="bold">{value}</Typography>
        </Box>
    </Paper>
);

export default function AnalyticsPage() {
    const [analytics, setAnalytics] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        setLoading(true);
        api.get('/api/v1/admin/analytics')
            .then(res => setAnalytics(res.data))
            .catch(err => setError("Could not fetch analytics data."))
            .finally(() => setLoading(false));
    }, []);

    if (loading) {
        return <AdminDashboardLayout><CircularProgress /></AdminDashboardLayout>;
    }

    if (error) {
        return <AdminDashboardLayout><Alert severity="error">{error}</Alert></AdminDashboardLayout>;
    }

    return (
        <AdminDashboardLayout>
            <Typography variant="h4" gutterBottom>System Analytics</Typography>
            
            {/* Stat Cards */}
            <Grid container spacing={3} sx={{ mb: 4 }}>
                <Grid item xs={12} sm={6} md={4}>
                    <StatCard title="Total Users" value={analytics.total_users} icon={<PeopleIcon />} />
                </Grid>
                <Grid item xs={12} sm={6} md={4}>
                    <StatCard title="Total Agents" value={analytics.total_agents} icon={<SmartToyIcon />} />
                </Grid>
                <Grid item xs={12} sm={6} md={4}>
                    <StatCard title="Total Messages" value={analytics.total_messages} icon={<MessageIcon />} />
                </Grid>
                <Grid item xs={12} sm={6} md={6}>
                    <StatCard title="Avg. Response Time" value={`${analytics.avg_response_time.toFixed(2)}s`} icon={<SpeedIcon />} />
                </Grid>
                <Grid item xs={12} sm={6} md={6}>
                    <StatCard title="Total Tokens Used" value={analytics.total_tokens_used.toLocaleString()} icon={<TokenIcon />} />
                </Grid>
            </Grid>

            {/* Time Series Chart */}
            <Typography variant="h5" gutterBottom>Messages (Last 7 Days)</Typography>
            <Paper sx={{ p: 2, height: 400 }}>
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                        data={analytics.messages_time_series}
                        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                    >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis />
                        <Tooltip contentStyle={{ backgroundColor: '#333' }} />
                        <Legend />
                        <Bar dataKey="messages" fill="#8884d8" />
                    </BarChart>
                </ResponsiveContainer>
            </Paper>
        </AdminDashboardLayout>
    );
}