"use client";
import { Box, Drawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText, Toolbar, Typography, Divider, Button } from '@mui/material';
import AuthGuard from './AuthGuard';
import { useAuthActions, useUserState } from '@/context/AuthContext';
import GroupIcon from '@mui/icons-material/Group';
import BarChartIcon from '@mui/icons-material/BarChart';
import LogoutIcon from '@mui/icons-material/Logout';
import { useRouter } from 'next/navigation';

const drawerWidth = 240;

export default function AdminDashboardLayout({ children }) {
  const { user } = useUserState();
  const { logout } = useAuthActions();
  const router = useRouter();

  const menuItems = [
    { text: 'User Management', icon: <GroupIcon />, path: '/admin/dashboard' },
    { text: 'System Analytics', icon: <BarChartIcon />, path: '/admin/analytics' }, // Placeholder
  ];

  return (
    <AuthGuard>
      <Box sx={{ display: 'flex' }}>
        <Drawer variant="permanent" sx={{ width: drawerWidth, flexShrink: 0, [`& .MuiDrawer-paper`]: { width: drawerWidth, boxSizing: 'border-box' } }}>
          <Toolbar><Typography variant="h6" noWrap>Admin Panel</Typography></Toolbar>
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
          <Box sx={{ p: 2, mt: 'auto' }}>
            <Typography variant="body2">Welcome, {user?.full_name}</Typography>
            <Button variant="text" startIcon={<LogoutIcon />} onClick={logout} fullWidth sx={{ justifyContent: 'flex-start', mt: 1 }}>
              Logout
            </Button>
          </Box>
        </Drawer>
        <Box component="main" sx={{ flexGrow: 1, bgcolor: 'background.default', p: 3, height: '100vh', overflow: 'auto' }}>
          <Toolbar />
          {children}
        </Box>
      </Box>
    </AuthGuard>
  );
}