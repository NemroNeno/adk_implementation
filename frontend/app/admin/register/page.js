"use client";
import { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { Button, TextField, Container, Typography, Box, Link, Alert } from '@mui/material';
import NextLink from 'next/link';

export default function AdminRegisterPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const { register } = useAuth();

  const handleSubmit = (e) => {
    e.preventDefault();
    register(email, password, fullName, true); // The `true` flag indicates admin registration
  };

  return (
    <Container component="main" maxWidth="xs">
      <Box sx={{ marginTop: 8, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <Typography component="h1" variant="h5">Register as Admin</Typography>
        <Alert severity="warning" sx={{width: '100%', mt: 2}}>This creates an account with administrative privileges.</Alert>
        <Box component="form" onSubmit={handleSubmit} noValidate sx={{ mt: 1 }}>
          <TextField margin="normal" required fullWidth id="fullName" label="Full Name" name="fullName" value={fullName} onChange={(e) => setFullName(e.target.value)} />
          <TextField margin="normal" required fullWidth id="email" label="Email Address" name="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <TextField margin="normal" required fullWidth name="password" label="Password" type="password" id="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          <Button type="submit" fullWidth variant="contained" sx={{ mt: 3, mb: 2 }}>Sign Up as Admin</Button>
          <Link component={NextLink} href="/login" variant="body2">
            {"Back to Sign In"}
          </Link>
        </Box>
      </Box>
    </Container>
  );
}