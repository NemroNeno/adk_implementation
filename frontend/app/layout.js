"use client"; // This is important for MUI compatibility
import { AuthProvider } from '@/context/AuthContext';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
  },
});

export default function RootLayout({ children }) {
  // We can remove the <head> and <body> tags as Next.js handles them.
  // Also, metadata should be exported separately, not returned.
  return (
    <html lang="en">
      <body>
        <ThemeProvider theme={darkTheme}>
          <CssBaseline />
          <AuthProvider>
            {children}
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}