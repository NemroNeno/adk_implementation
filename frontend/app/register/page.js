"use client";
import { useState } from 'react';
// Import both hooks now
import { useAuthActions, useUserState } from '@/context/AuthContext';
import { Button, TextField, Container, Typography, Box, Link, Alert } from '@mui/material'; // Import Alert
import NextLink from 'next/link';

export default function RegisterPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const { register } = useAuthActions();
  // Get the error state from the context
  const { error, setError } = useAuthActions();

  const handleSubmit = async (e) => {
    e.preventDefault();
    await register(email, password, fullName, false);
  };

  return (
    
    <Container component="main" maxWidth="xs">
      <Box sx={{ marginTop: 8, /* ... */ }}>
        <Typography component="h1" variant="h5">Sign up</Typography>

        {/* --- DISPLAY ERROR ALERT --- */}
        {error && (
            <Alert severity="error" sx={{ width: '100%', mt: 2 }} onClose={() => setError(null)}>
                {error}
            </Alert>
        )}
        
        <Box component="form" onSubmit={handleSubmit} noValidate sx={{ mt: 1 }}>
            {/* ... TextFields and Button ... */}
          <TextField margin="normal" required fullWidth id="fullName" label="Full Name" name="fullName" value={fullName} onChange={(e) => setFullName(e.target.value)} />
          <TextField margin="normal" required fullWidth id="email" label="Email Address" name="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <TextField margin="normal" required fullWidth name="password" label="Password" type="password" id="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          <Button type="submit" fullWidth variant="contained" sx={{ mt: 3, mb: 2 }}>Sign Up</Button>

        
          <Link component={NextLink} href="/login" variant="body2">
            {"Back to Sign In"}
          </Link>

        </Box>
      </Box>
    </Container>
  );
}