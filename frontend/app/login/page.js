'use client';

import { useState } from 'react';
import { useAuthActions } from '@/context/AuthContext'; // Correct hook
import { Button, TextField, Container, Typography, Box, Link, Divider, Grid } from '@mui/material';
import NextLink from 'next/link';
import GoogleIcon from '@mui/icons-material/Google';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { login } = useAuthActions();

  const handleSubmit = (e) => {
    e.preventDefault();
    login(email, password);
  };

  const handleOAuthLogin = (provider) => {
    window.location.href = `${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/login/${provider}`;
  };

  return (
    <Container component="main" maxWidth="xs">
      <Box
        sx={{
          marginTop: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Typography component="h1" variant="h5">
          Sign in
        </Typography>

        <Box component="form" onSubmit={handleSubmit} sx={{ mt: 3 }}>
          <TextField
            margin="normal"
            required
            fullWidth
            id="email"
            label="Email Address"
            name="email"
            autoComplete="email"
            autoFocus
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />

          <TextField
            margin="normal"
            required
            fullWidth
            name="password"
            label="Password"
            type="password"
            id="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          <Button type="submit" fullWidth variant="contained" sx={{ mt: 3, mb: 2 }}>
            Sign In
          </Button>

          <Divider sx={{ my: 2 }}>OR</Divider>

          <Button
            onClick={() => handleOAuthLogin('google')}
            fullWidth
            variant="outlined"
            sx={{ mb: 1 }}
            startIcon={<GoogleIcon />}
          >
            Sign In with Google
          </Button>

          {/* Additional Registration Links */}
          <Grid container sx={{ mt: 2 }} justifyContent="space-between">
            <Grid item>
              <Link component={NextLink} href="/viewer/register" variant="body2">
                Register as Viewer
              </Link>
            </Grid>
            <Grid item>
              <Link component={NextLink} href="/admin/register" variant="body2">
                Register as Admin
              </Link>
            </Grid>
            <Grid item>
              <Link component={NextLink} href="/register" variant="body2">
                Sign Up
              </Link>
            </Grid>
          </Grid>
        </Box>
      </Box>
    </Container>
  );
}
