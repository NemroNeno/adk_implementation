'use client';

import { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';
import { useRouter } from 'next/navigation';

// Create contexts
const UserStateContext = createContext({ user: null, token: null, loading: true, error: null });
const AuthDispatchContext = createContext(null);

// Export the configured api instance
export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
});

// Export custom hooks
export const useUserState = () => useContext(UserStateContext);
export const useAuthActions = () => useContext(AuthDispatchContext);
export const useAuth = () => ({ ...useUserState(), ...useAuthActions() });

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null); // <-- ADD ERROR STATE
  const router = useRouter();

  // Redirect based on user role
  const redirectToDashboard = (role) => {
    if (role === 'admin') {
      router.push('/admin/dashboard');
    } else if (role === 'viewer') {
      router.push('/viewer/dashboard'); // <-- VIEWER REDIRECT
    } else {
      router.push('/dashboard/agents');
    }
  };

  const loginWithToken = async (token) => {
    localStorage.setItem('token', token);
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    try {
      const res = await api.get('/api/v1/users/me');
      setUser(res.data);
      setToken(token);
      redirectToDashboard(res.data.role);
    } catch (error) {
      localStorage.removeItem('token');
      api.defaults.headers.common['Authorization'] = '';
      setUser(null);
      setToken(null);
    }
  };

  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    if (storedToken) {
      loginWithToken(storedToken).finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email, password) => {
    setError(null);
    try {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const res = await api.post('/api/v1/login/access-token', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });

      await loginWithToken(res.data.access_token);
    } catch (err) {
      console.error("Login failed:", err);
      const errorMessage = err.response?.data?.detail || "Login failed. Please check your credentials.";
      setError(errorMessage);
    }
  };

  const register = async (email, password, fullName, isAdmin = false) => {
    setError(null);
    try {
      const endpoint = isAdmin ? '/api/v1/users/admin' : '/api/v1/users/';
      const payload = { email, password, full_name: fullName };

      await api.post(endpoint, payload, {
        headers: { 'Content-Type': 'application/json' }
      });

      alert("Registration successful! Logging you in...");
      await login(email, password);
    } catch (err) {
      console.error("Registration failed:", err);
      const errorMessage = err.response?.data?.detail || "An unknown error occurred during registration.";
      setError(errorMessage);
    }
  };

  // --- ✅ ADD THIS NEW FUNCTION ---
  const registerAsViewer = async (email, password, fullName) => {
    setError(null);
    try {
      const endpoint = '/api/v1/users/viewer'; // viewer-specific endpoint
      const payload = { email, password, full_name: fullName };

      await api.post(endpoint, payload, {
        headers: { 'Content-Type': 'application/json' }
      });

      alert("Viewer registration successful! Logging you in...");
      await login(email, password);
    } catch (err) {
      console.error("Viewer registration failed:", err);
      const errorMessage = err.response?.data?.detail || "An error occurred during viewer registration.";
      setError(errorMessage);
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    api.defaults.headers.common['Authorization'] = '';
    setUser(null);
    setToken(null);
    setError(null);
    router.push('/login');
  };

  const authActions = {
    login,
    logout,
    register,
    registerAsViewer, // ✅ Add it to exported actions
    loginWithToken,
    error,
    setError,
  };

  return (
    <UserStateContext.Provider value={{ user, token, loading, error }}>
      <AuthDispatchContext.Provider value={authActions}>
        {children}
      </AuthDispatchContext.Provider>
    </UserStateContext.Provider>
  );
};
