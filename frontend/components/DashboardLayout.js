"use client";
import { Box, Drawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText, Toolbar, Typography, Divider, Button, Avatar } from '@mui/material';
import AuthGuard from './AuthGuard';
import { useAuthActions, useUserState } from '@/context/AuthContext';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import LogoutIcon from '@mui/icons-material/Logout';
import CreditCardIcon from '@mui/icons-material/CreditCard';
import PowerIcon from '@mui/icons-material/Power';
import { useRouter } from 'next/navigation';
import UsageMeter from './UsageMeter';
import { api } from '@/context/AuthContext';
import { useState, useEffect } from 'react';

const drawerWidth = 240;

export default function DashboardLayout({ children }) {
  const { user } = useUserState();
  const { logout } = useAuthActions();
  const router = useRouter();
  const [plans, setPlans] = useState(null);
  useEffect(() => { api.get('/api/v1/plans/').then(res => setPlans(res.data)); }, []);

  const menuItems = [
    { text: 'My Agents', icon: <SmartToyIcon />, path: '/dashboard/agents' },
    { text: 'Profile', icon: <AccountCircleIcon />, path: '/dashboard/profile' },
    { text: 'Billing & Plan', icon: <CreditCardIcon />, path: '/dashboard/billing' },
    { text: 'Integrations', icon: <PowerIcon />, path: '/dashboard/integrations' },
  ];
  
  const currentPlanDetails = user && plans ? plans[user.plan] : null;

  return (
    <AuthGuard>
      <Box sx={{ display: 'flex' }}>
        <Drawer
          variant="permanent"
          sx={{
            width: drawerWidth,
            flexShrink: 0,
            [`& .MuiDrawer-paper`]: { width: drawerWidth, boxSizing: 'border-box' },
          }}
        >
          <Toolbar>
            <Typography variant="h6" noWrap>ADK Platform</Typography>
          </Toolbar>
          <Divider />
          <List>
            {menuItems.map((item) => (
              <ListItem key={item.text} disablePadding>
                <ListItemButton onClick={() => router.push(item.path)}>
                  <ListItemIcon>{item.icon}</ListItemIcon>
                  <ListItemText primary={item.text} />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
          <Divider />
          {user && currentPlanDetails && (
            <Box sx={{ p: 2 }}>
              <Typography variant="overline" color="text.secondary">Monthly Usage</Typography>
              <UsageMeter
                  title="Token Usage"
                  used={user.token_usage_this_month || 0}
                  limit={currentPlanDetails.limits.max_tokens_per_month}
              />
            </Box>
          )}
          <Box sx={{ p: 2, mt: 'auto', display: 'flex', alignItems: 'center' }}>
            <Avatar sx={{ mr: 1, bgcolor: 'secondary.main' }}>
              {user?.full_name ? user.full_name.charAt(0) : <AccountCircleIcon />}
            </Avatar>
            <Box>
              <Typography variant="body2">Welcome, {user?.full_name}</Typography>
              <Button
                variant="text"
                size="small"
                startIcon={<LogoutIcon />}
                onClick={logout}
                sx={{ p: 0, justifyContent: 'flex-start', color: 'text.secondary' }}
              >
                Logout
              </Button>
            </Box>
          </Box>
        </Drawer>
        <Box component="main" sx={{ flexGrow: 1, p: 3, height: '100vh', overflow: 'auto' }}>
          <Toolbar />
          {children}
        </Box>
      </Box>
    </AuthGuard>
  );
}