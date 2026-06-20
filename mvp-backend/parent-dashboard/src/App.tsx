import type { ReactNode } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { useAuth } from './auth/AuthContext';
import Layout from './components/Layout';
import Login from './pages/Login';
import Discovery from './pages/Discovery';
import Plan from './pages/Plan';
import Chat from './pages/Chat';

function ProtectedRoute({ children }: { children: ReactNode }) {
  const { isAuthed } = useAuth();
  return isAuthed ? <>{children}</> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Plan />} />
        <Route path="plan" element={<Plan />} />
        <Route path="discovery" element={<Discovery />} />
        <Route path="chat" element={<Chat />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
