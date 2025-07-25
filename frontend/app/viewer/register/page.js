"use client";
import { useState } from 'react';
import { useAuthActions } from '@/context/AuthContext';
import { Button, TextField, Container, Typography, Box, Link, Alert } from '@mui/material';
import NextLink from 'next/link';

export default function ViewerRegisterPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const { registerAsViewer } = useAuthActions(); // We will create this new function
  const { error, setError } = useAuthActions();

  const handleSubmit = async (e) => {
    e.preventDefault();
    await registerAsViewer(email, password, fullName);
  };

  return (
    <Container component="main" maxWidth="xs">
      <Box sx={{ marginTop: 8, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <Typography component="h1" variant="h5">Register as Viewer</Typography>
        <Alert severity="info" sx={{width: '100%', mt: 2}}>
          Viewer accounts have read-only access and cannot create or modify agents.
        </Alert>
        
        {error && (
            <Alert severity="error" sx={{ width: '100%', mt: 2 }} onClose={() => setError(null)}>
                {error}
            </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit} noValidate sx={{ mt: 1 }}>
          <TextField margin="normal" required fullWidth id="fullName" label="Full Name" name="fullName" value={fullName} onChange={(e) => setFullName(e.target.value)} />
          <TextField margin="normal" required fullWidth id="email" label="Email Address" name="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <TextField margin="normal" required fullWidth name="password" label="Password" type="password" id="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          <Button type="submit" fullWidth variant="contained" sx={{ mt: 3, mb: 2 }}>Sign Up as Viewer</Button>
          <Link component={NextLink} href="/login" variant="body2">
            {"Back to Sign In"}
          </Link>
        </Box>
      </Box>
    </Container>
  );
}