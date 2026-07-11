import { useEffect, useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';

// Phase 2 sign-in: Sign in with Google (web redirect) or a pairing code minted
// in the mobile app. The legacy "type your user id" path is kept collapsed for
// existing beta accounts until every family has signed in.
export default function Login() {
  const { login, loginWithCode, loginWithPairing } = useAuth();
  const navigate = useNavigate();
  const [pairing, setPairing] = useState('');
  const [legacyId, setLegacyId] = useState('');
  const [showLegacy, setShowLegacy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  // Returning from the Google redirect: the backend appends
  // #status=success&login_code=... to /dashboard/. Redeem it, then clean the URL.
  useEffect(() => {
    const hash = window.location.hash.replace(/^#/, '');
    if (!hash) return;
    const params = new URLSearchParams(hash);
    const code = params.get('login_code');
    if (params.get('status') === 'success' && code) {
      setBusy(true);
      loginWithCode(code)
        .then(() => {
          window.history.replaceState(null, '', window.location.pathname);
          navigate('/plan');
        })
        .catch((e) => setErr(e instanceof Error ? e.message : 'Sign-in failed'))
        .finally(() => setBusy(false));
    } else if (params.get('status') === 'error') {
      setErr('Google sign-in was cancelled or failed.');
    }
  }, [loginWithCode, navigate]);

  function signInWithGoogle() {
    // Full-page redirect to the backend, which 302s to Google consent.
    window.location.href = '/auth/google/start?surface=dashboard';
  }

  async function submitPairing(e: FormEvent) {
    e.preventDefault();
    if (!pairing.trim() || busy) return;
    setBusy(true);
    setErr(null);
    try {
      await loginWithPairing(pairing.trim());
      navigate('/plan');
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Invalid pairing code');
    } finally {
      setBusy(false);
    }
  }

  async function submitLegacy(e: FormEvent) {
    e.preventDefault();
    if (!legacyId.trim() || busy) return;
    setBusy(true);
    setErr(null);
    try {
      await login(legacyId);
      navigate('/plan');
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Sign-in failed');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-canvas">
      <div className="w-[380px] flex flex-col gap-500 bg-elevated border border-hairline rounded-xl p-800">
        <h1 className="font-display text-3xl text-ink-primary">Parent Dashboard</h1>
        <p className="text-ink-secondary text-sm">Sign in to see your family's plan.</p>

        <button
          type="button"
          onClick={signInWithGoogle}
          disabled={busy}
          className="flex items-center justify-center gap-300 bg-accent text-ink-on-photo-light rounded-lg px-500 py-300 font-medium disabled:opacity-60"
        >
          Continue with Google
        </button>

        <form onSubmit={submitPairing} className="flex flex-col gap-300">
          <label className="text-ink-secondary text-xs">
            Or enter a pairing code from the app (Settings → Pair a device)
          </label>
          <div className="flex gap-300">
            <input
              value={pairing}
              onChange={(e) => setPairing(e.target.value)}
              placeholder="ABCD-1234"
              className="flex-1 border border-strong rounded-lg px-400 py-300 bg-canvas text-ink-primary outline-none focus:border-accent"
            />
            <button
              type="submit"
              disabled={busy || !pairing.trim()}
              className="bg-canvas border border-strong rounded-lg px-400 py-300 text-ink-primary disabled:opacity-60"
            >
              Pair
            </button>
          </div>
        </form>

        {err && <div className="text-error text-sm">{err}</div>}

        <button
          type="button"
          onClick={() => setShowLegacy((v) => !v)}
          className="text-ink-secondary text-xs underline self-start"
        >
          {showLegacy ? 'Hide' : 'Existing beta account?'}
        </button>
        {showLegacy && (
          <form onSubmit={submitLegacy} className="flex flex-col gap-300">
            <input
              value={legacyId}
              onChange={(e) => setLegacyId(e.target.value)}
              placeholder="user id"
              className="border border-strong rounded-lg px-400 py-300 bg-canvas text-ink-primary outline-none focus:border-accent"
            />
            <button
              type="submit"
              disabled={busy || !legacyId.trim()}
              className="bg-canvas border border-strong rounded-lg px-500 py-300 text-ink-primary disabled:opacity-60"
            >
              Continue
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
