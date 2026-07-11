import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import { initAnalytics, identify } from './analytics';
import { getAnalyticsId } from './auth/store';
import App from './App';
import './index.css';

// PostHog (no-op without VITE_POSTHOG_KEY). Re-identify a returning session on
// its opaque analytics id so events attribute correctly after a refresh.
initAnalytics();
identify(getAnalyticsId());

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter basename="/dashboard">
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
);
