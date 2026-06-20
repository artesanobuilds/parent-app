import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';

// Closed-beta sign-in: the parent enters the same user_id the mobile app uses.
// Real email/password (or Apple Sign-In) is a later step.
export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [userId, setUserId] = useState('');
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!userId.trim()) return;
    setBusy(true);
    setErr(null);
    try {
      await login(userId);
      navigate('/plan');
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Sign-in failed');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-canvas">
      <form
        onSubmit={submit}
        className="w-[380px] flex flex-col gap-500 bg-elevated border border-hairline rounded-xl p-800"
      >
        <h1 className="font-display text-3xl text-ink-primary">Parent Dashboard</h1>
        <p className="text-ink-secondary text-sm">
          Enter the same user ID you use in the app. (Closed-beta sign-in — password
          auth comes later.)
        </p>
        <input
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
          placeholder="user id"
          autoFocus
          className="border border-strong rounded-lg px-400 py-300 bg-canvas text-ink-primary outline-none focus:border-accent"
        />
        {err && <div className="text-error text-sm">{err}</div>}
        <button
          type="submit"
          disabled={busy || !userId.trim()}
          className="bg-accent text-ink-on-photo-light rounded-lg px-500 py-300 font-medium disabled:opacity-60"
        >
          {busy ? 'Signing in…' : 'Continue'}
        </button>
      </form>
    </div>
  );
}
