"use client";
import { useState, useEffect, useMemo } from 'react';
import { api, useUserState } from '@/context/AuthContext';
import { Typography, Box, List, ListItem, ListItemButton, ListItemText, Paper, CircularProgress, Button, Tooltip, Menu, MenuItem, IconButton, Divider } from '@mui/material';
import Link from 'next/link';
import AddIcon from '@mui/icons-material/Add';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import CreateAgentModal from '@/components/CreateAgentModal';
import EditAgentModal from '@/components/EditAgentModal'; // <-- IMPORT EDIT MODAL

export default function AgentsPage() {
    const { user, loading: userLoading } = useUserState();
    const [agents, setAgents] = useState([]);
    const [listLoading, setListLoading] = useState(true);
    const [plans, setPlans] = useState(null);
    const [createModalOpen, setCreateModalOpen] = useState(false);
    const [editModalOpen, setEditModalOpen] = useState(false);
    const [selectedAgent, setSelectedAgent] = useState(null);
    const [anchorEl, setAnchorEl] = useState(null);

    useEffect(() => {
        if (user) {
            setListLoading(true);
            Promise.all([api.get('/api/v1/agents/'), api.get('/api/v1/plans/')])
                .then(([agentsRes, plansRes]) => {
                    setAgents(agentsRes.data);
                    setPlans(plansRes.data);
                }).catch(console.error).finally(() => setListLoading(false));
        }
    }, [user]);

    const handleAgentCreated = (newAgent) => setAgents(prev => [...prev, newAgent]);
    const handleAgentUpdated = (updatedAgent) => {
        setAgents(prev => prev.map(agent => agent.id === updatedAgent.id ? updatedAgent : agent));
    };

    const handleMenuClick = (event, agent) => {
        event.stopPropagation();
        setAnchorEl(event.currentTarget);
        setSelectedAgent(agent);
    };
    
    const handleMenuClose = () => {
        setAnchorEl(null);
        setSelectedAgent(null);
    };
    
    const handleEdit = () => {
        setEditModalOpen(true);
        setAnchorEl(null);
    };
    
    const handleDelete = () => {
        if (window.confirm(`Are you sure you want to delete the agent "${selectedAgent.name}"? This action cannot be undone.`)) {
            api.delete(`/api/v1/agents/${selectedAgent.id}`)
                .then(() => {
                    setAgents(prev => prev.filter(agent => agent.id !== selectedAgent.id));
                    handleMenuClose();
                })
                .catch(err => {
                    alert("Failed to delete agent. You may not be the owner.");
                    handleMenuClose();
                });
        }
    };

    const isLoading = userLoading || listLoading;
    const agentLimitReached = useMemo(() => {
        if (isLoading || !user || !plans) return true;
        const currentPlan = plans[user.plan];
        if (!currentPlan) return true;
        return agents.length >= currentPlan.limits.max_agents;
    }, [isLoading, user, plans, agents]);
    
    return (
        <Box>
            {/* Header section... */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h4" gutterBottom>My Agents</Typography>
                {user && user.role !== 'viewer' && (
                    <Tooltip title={agentLimitReached ? `Agent limit reached for your plan.` : "Create New Agent"}>
                        <span> 
                            <Button variant="contained" startIcon={<AddIcon />} onClick={() => setCreateModalOpen(true)} disabled={isLoading || agentLimitReached}>Create Agent</Button>
                        </span>
                    </Tooltip>
                )}
            </Box>
            <Divider sx={{ mb: 3 }} />
            
            {/* Agent List */}
            {isLoading ? <CircularProgress /> : (
                agents.length > 0 ? (
                    <Paper><List>
                        {agents.map(agent => (
                            <ListItem key={agent.id} secondaryAction={
                                user && (user.role === 'admin' || user.id === agent.owner_id) && (
                                    <IconButton edge="end" onClick={(e) => handleMenuClick(e, agent)}><MoreVertIcon /></IconButton>
                                )
                            } disablePadding>
                                <ListItemButton component={Link} href={`/dashboard/agents/${agent.id}`}>
                                    <ListItemText primary={agent.name} secondary={<Typography noWrap variant="body2" color="text.secondary">{agent.system_prompt}</Typography>} />
                                </ListItemButton>
                            </ListItem>
                        ))}
                    </List></Paper>
                ) : (
                    <Box sx={{textAlign: 'center', p: 4, border: '2px dashed', borderColor: 'grey.800', borderRadius: 2}}>
                        <Typography variant="h6">No Agents Found</Typography>
                        <Typography color="text.secondary">Click "Create Agent" to build your first AI agent.</Typography>
                    </Box>
                )
            )}

            {/* Menu and Modals */}
            <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleMenuClose}>
                <MenuItem onClick={handleEdit}>Edit</MenuItem>
                <MenuItem onClick={handleDelete} sx={{ color: 'error.main' }}>Delete</MenuItem>
            </Menu>
            <CreateAgentModal open={createModalOpen} handleClose={() => setCreateModalOpen(false)} onAgentCreated={handleAgentCreated} />
            <EditAgentModal open={editModalOpen} handleClose={() => setEditModalOpen(false)} agent={selectedAgent} onAgentUpdated={handleAgentUpdated} />
        </Box>
    );
}