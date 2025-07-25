"use client";
import { useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { useAuthActions } from '@/context/AuthContext'; // Must use this hook
import { Box, CircularProgress, Typography } from '@mui/material';

function AuthCallback() {
    const searchParams = useSearchParams();
    const { loginWithToken } = useAuthActions(); // Get the function here

    useEffect(() => {
        const token = searchParams.get('token');
        if (token && loginWithToken) {
            loginWithToken(token); 
        }
    }, [searchParams, loginWithToken]);

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
            <CircularProgress />
            <Typography sx={{mt: 2}}>Finalizing authentication...</Typography>
        </Box>
    );
}

export default function AuthCallbackPage() {
    return (
        <Suspense>
            <AuthCallback />
        </Suspense>
    );
}