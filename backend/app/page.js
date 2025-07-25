"use client";
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Box, CircularProgress } from '@mui/material';

// We are using the separated context hooks, which is the build-safe pattern
import { useUserState } from '@/context/AuthContext'; 

// This is the main entry point of the app: http://localhost:3000/
// Its only job is to check the user's authentication status and redirect them.
export default function HomePage() {
  const { user, loading } = useUserState();
  const router = useRouter();

  useEffect(() => {
    // Wait until the AuthContext has finished checking for a token from localStorage.
    if (!loading) {
      if (user) {
        // If a user object exists, they are logged in. Go to their dashboard.
        if (user.role === 'admin') {
            router.push('/admin/dashboard');
        } else {
            router.push('/dashboard/agents');
        }
      } else {
        // If there's no user, they need to log in.
        router.push('/login');
      }
    }
  }, [user, loading, router]);

  // While the authentication check is happening, display a loading spinner.
  // This prevents a "flash" of the wrong page when the app first loads.
  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
      }}
    >
      <CircularProgress />
    </Box>
  );
}