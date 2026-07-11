import { useEffect, type ReactNode } from 'react';
import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { useAuth } from './auth/AuthContext';
import { pageview } from './analytics';
import Layout from './components/Layout';
import Login from './pages/Login';
import Docs from './pages/Docs';
import Discovery from './pages/Discovery';
import Plan from './pages/Plan';
import Chat from './pages/Chat';
import Profile from './pages/Profile';

function ProtectedRoute({ children }: { children: ReactNode }) {
  const { isAuthed } = useAuth();
  return isAuthed ? <>{children}</> : <Navigate to="/login" replace />;
}

// Explicit, path-only pageviews (autocapture is off). The route name carries no
// PII, so this is safe on a kid/family surface.
function usePageviews() {
  const location = useLocation();
  useEffect(() => {
    pageview(location.pathname);
  }, [location.pathname]);
}

export default function App() {
  usePageviews();
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      {/* PUBLIC product docs — deliberately OUTSIDE ProtectedRoute (the GTM
          funnel links straight here). tests/test_public_docs.py asserts the
          guard keeps excluding these. */}
      <Route path="/docs" element={<Docs />} />
      <Route path="/docs/:slug" element={<Docs />} />
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
        <Route path="profile" element={<Profile />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
