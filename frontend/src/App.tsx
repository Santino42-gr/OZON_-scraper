import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '@/contexts/AuthContext.tsx';
import { Toaster } from '@/components/ui/toaster.tsx';
import { Toaster as Sonner } from '@/components/ui/sonner.tsx';
import { ProtectedRoute } from '@/components/common/ProtectedRoute.tsx';
import { Layout } from '@/components/common/Layout.tsx';
import Login from '@/pages/Login.tsx';
import ResetPassword from '@/pages/ResetPassword.tsx';
import Dashboard from '@/pages/Dashboard.tsx';
import Articles from '@/pages/Articles.tsx';
import Users from '@/pages/Users.tsx';
import Logs from '@/pages/Logs.tsx';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Router>
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/reset-password" element={<ResetPassword />} />

            {/* Protected Routes */}
            <Route
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route path="/" element={<Dashboard />} />
              <Route path="/dashboard" element={<Navigate to="/" replace />} />
              <Route path="/articles" element={<Articles />} />
              <Route path="/users" element={<Users />} />
              <Route path="/logs" element={<Logs />} />
            </Route>

            {/* Catch all - redirect to dashboard */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          <Toaster />
          <Sonner />
        </Router>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;

