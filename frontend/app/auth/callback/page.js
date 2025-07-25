"use client";
import { useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { Box, CircularProgress, Typography } from '@mui/material';

function AuthCallback() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const { loginWithToken } = useAuth(); 

    useEffect(() => {
        const token = searchParams.get('token');
        if (token) {
            loginWithToken(token);
        } else {
            router.push('/login?error=auth_failed');
        }
    }, []); // Removed dependencies to run only once

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
            <CircularProgress />
            <Typography sx={{mt: 2}}>Finalizing authentication...</Typography>
        </Box>
    );
}

// Wrap with Suspense because useSearchParams requires it
export default function AuthCallbackPage() {
    return (
        <Suspense fallback={<div>Loading...</div>}>
            <AuthCallback />
        </Suspense>
    );
}