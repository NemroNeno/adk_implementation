"use client";
import { useState, useEffect } from 'react';
import { Typography, Box, Paper, List, ListItem, ListItemText, CircularProgress, IconButton, Alert, Divider, Button } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import PersonIcon from '@mui/icons-material/Person';
import VisibilityIcon from '@mui/icons-material/Visibility';
import DownloadIcon from '@mui/icons-material/Download'; // <-- Import the download icon
import { api, useUserState } from '@/context/AuthContext';
import AdminDashboardLayout from '@/components/AdminDashboardLayout';

export default function AdminDashboard() {
    const { user, loading: authLoading } = useUserState(); 
    const [users, setUsers] = useState([]);
    const [listLoading, setListLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        if (user && user.role === 'admin') {
            setListLoading(true);
            api.get('/api/v1/users/')
                .then(res => setUsers(res.data))
                .catch(err => setError("Could not fetch users."))
                .finally(() => setListLoading(false));
        }
    }, [user]);

    const handleDeleteUser = (userId) => {
        if (window.confirm("Are you sure you want to delete this user? This is irreversible.")) {
            api.delete(`/api/v1/users/${userId}`)
                .then(() => {
                    alert("User deleted successfully.");
                    setUsers(prevUsers => prevUsers.filter(u => u.id !== userId));
                })
                .catch(err => alert(`Failed to delete user: ${err.response?.data?.detail || err.message}`));
        }
    };

    // --- THIS IS THE NEW FUNCTION FOR EXPORTING ---
    const handleExport = () => {
        api.get('/api/v1/admin/reports/audit-log', {
            responseType: 'blob', // We expect a file
        }).then(response => {
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', 'audit_log_export.csv');
            document.body.appendChild(link);
            link.click();
            link.parentNode.removeChild(link);
        }).catch(err => {
            alert("Failed to export report.");
            console.error(err);
        });
    };

    const roleIcons = {
        admin: <AdminPanelSettingsIcon color="primary" />,
        user: <PersonIcon />,
        viewer: <VisibilityIcon color="disabled" />,
    };

    if (authLoading || listLoading) {
        return (
            <AdminDashboardLayout>
                <CircularProgress />
            </AdminDashboardLayout>
        );
    }
    
    return (
        <AdminDashboardLayout>
            {error && <Alert severity="error">{error}</Alert>}
            
            {/* --- User Management Section --- */}
            <Typography variant="h4" gutterBottom>User Management</Typography>
            <Paper>
                <List>
                    {users.map((u) => (
                        <ListItem
                            key={u.id}
                            secondaryAction={
                                user && u.id !== user.id && (
                                    <IconButton edge="end" aria-label="delete" onClick={() => handleDeleteUser(u.id)}>
                                        <DeleteIcon />
                                    </IconButton>
                                )
                            }
                        >
                            <ListItemText
                                primary={u.full_name || u.email}
                                secondary={`Role: ${u.role}`}
                            />
                            {roleIcons[u.role]}
                        </ListItem>
                    ))}
                </List>
            </Paper>

            <Divider sx={{ my: 4 }} />

            {/* --- Reporting Section --- */}
            <Typography variant="h4" gutterBottom>Reporting</Typography>
            <Paper sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Typography>
                    Export a complete CSV file of all user and system actions recorded in the audit log.
                </Typography>
                <Button
                    variant="contained"
                    startIcon={<DownloadIcon />}
                    onClick={handleExport}
                >
                    Export Audit Log
                </Button>
            </Paper>
        </AdminDashboardLayout>
    );
}