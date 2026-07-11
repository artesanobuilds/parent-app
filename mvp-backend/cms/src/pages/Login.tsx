import { useState } from 'react';
import type { FormEvent } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { createSession } from '../api';

export function Login() {
  const [token, setToken] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();
  const [params] = useSearchParams();

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!token.trim() || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      await createSession(token.trim());
      // `from` is an absolute path incl. the /cms basename; navigate wants a
      // basename-relative one.
      const from = params.get('from');
      navigate(from && from.startsWith('/cms') ? from.slice('/cms'.length) || '/' : '/', { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-canvas p-800">
      <form
        onSubmit={onSubmit}
        className="w-full max-w-sm rounded-lg border border-hairline bg-elevated p-700"
      >
        <h1 className="font-display text-display-sm text-ink-primary mb-300">MVP CMS</h1>
        <p className="text-body-sm text-ink-muted mb-600">
          Enter the operator token to start an admin session.
        </p>
        <input
          type="password"
          autoFocus
          autoComplete="current-password"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          placeholder="Admin token"
          className="w-full rounded-md border border-hairline bg-canvas px-500 py-300 text-body-md text-ink-primary mb-400 focus:outline-none focus:ring-2 focus:ring-accent"
        />
        {error && <p className="text-body-sm text-red-600 mb-400">{error}</p>}
        <button
          type="submit"
          disabled={!token.trim() || submitting}
          className="w-full rounded-md bg-accent px-500 py-300 text-title-md font-medium text-ink-on-photo-light hover:bg-accent-press transition-colors duration-fast disabled:opacity-50"
        >
          {submitting ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
    </div>
  );
}
