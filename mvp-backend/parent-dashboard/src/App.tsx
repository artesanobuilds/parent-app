import { useEffect, type ReactNode } from 'react';
import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { useAuth } from './auth/AuthContext';
import { pageview } from './analytics';
import Layout from './components/Layout';
import Login from './pages/Login';
import Docs from './pages/Docs';
import Invite from './pages/Invite';
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
      {/* PUBLIC invite landing — also OUTSIDE ProtectedRoute, and for a
          stronger reason than the docs: the person opening an invite has no
          account yet (a nanny, a grandparent), so the auth guard would strand
          exactly the visitor the link exists for. This is the path
          CIRCLE_INVITE_BASE_URL points at. */}
      <Route path="/invite/:token" element={<Invite />} />
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
