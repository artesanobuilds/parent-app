import { useState } from 'react';
import {
  deleteTesterFamily,
  getAdminAccounts,
  resetTester,
  type AdminAccount,
  type TesterResetResult,
} from '../api';
import { toast } from '../components/shared/Toast';

export function Users() {
  const [userId, setUserId] = useState('');
  const [confirmText, setConfirmText] = useState('');
  const [accounts, setAccounts] = useState<AdminAccount[] | null>(null);
  const [loadingAccounts, setLoadingAccounts] = useState(false);
  const [busy, setBusy] = useState<'reset' | 'delete' | null>(null);
  const [result, setResult] = useState<
    { action: 'reset' | 'delete'; data: TesterResetResult } | null
  >(null);

  const target = userId.trim();
  const confirmed = target.length > 0 && confirmText.trim() === target;

  async function loadAccounts() {
    setLoadingAccounts(true);
    try {
      setAccounts(await getAdminAccounts());
    } catch {
      toast.error('Failed to load accounts');
    } finally {
      setLoadingAccounts(false);
    }
  }

  async function doReset() {
    if (!confirmed || busy) return;
    setBusy('reset');
    setResult(null);
    try {
      const data = await resetTester(target);
      setResult({ action: 'reset', data });
      setConfirmText('');
      toast.success(`Reset ${target} — sign-in identity kept`);
    } catch (e) {
      toast.error(
        e instanceof Error && e.message.startsWith('404')
          ? 'No account or data found for that user_id'
          : 'Reset failed',
      );
    } finally {
      setBusy(null);
    }
  }

  async function doDelete() {
    if (!confirmed || busy) return;
    if (
      !window.confirm(
        `FULL DELETE of ${target} — this deletes the sign-in identity too. ` +
          'The tester will get a brand-new account next sign-in. Continue?',
      )
    ) {
      return;
    }
    setBusy('delete');
    setResult(null);
    try {
      const data = await deleteTesterFamily(target);
      setResult({ action: 'delete', data });
      setConfirmText('');
      toast.success(`Deleted ${target} — identity removed`);
    } catch (e) {
      toast.error(
        e instanceof Error && e.message.startsWith('404')
          ? 'No account or data found for that user_id'
          : 'Delete failed',
      );
    } finally {
      setBusy(null);
    }
  }

  const counts = result ? (result.data.counts ?? result.data.deleted ?? {}) : {};
  const nonZero = Object.entries(counts).filter(([, n]) => n > 0);

  return (
    <div className="p-800 max-w-5xl mx-auto">
      <h1 className="font-display text-display-sm text-ink-primary mb-200">Testers</h1>
      <p className="text-ink-muted text-body-sm mb-700">
        Reset a tester's family data so they can re-run the redesigned onboarding on
        their real account. After reset: sign out in the app, relaunch, and run
        onboarding again — your sign-in stays attached.
      </p>

      {/* Find a user_id */}
      <div className="rounded-lg border border-hairline bg-elevated p-600 mb-700">
        <div className="flex items-end justify-between gap-600 flex-wrap">
          <div>
            <h2 className="font-display text-title-md text-ink-primary mb-100">
              Find a user_id
            </h2>
            <p className="text-body-sm text-ink-muted">
              Look up the account by email below, or check the row counts on the
              Dashboard (/cms/stats).
            </p>
          </div>
          <button
            onClick={loadAccounts}
            disabled={loadingAccounts}
            className="rounded-md border border-strong px-500 py-300 text-title-md font-medium text-ink-primary hover:bg-canvas transition-colors duration-fast disabled:opacity-60"
          >
            {loadingAccounts ? 'Loading…' : accounts ? 'Reload accounts' : 'Load accounts'}
          </button>
        </div>
        {accounts && (
          <div className="mt-500 overflow-hidden rounded-md border border-hairline">
            <table className="w-full text-body-sm">
              <thead>
                <tr className="border-b border-hairline bg-canvas text-left text-label uppercase tracking-wider text-ink-muted">
                  <th className="px-400 py-300">User ID</th>
                  <th className="px-400 py-300">Email</th>
                  <th className="px-400 py-300">Sign-in claimed</th>
                  <th className="px-400 py-300">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-hairline">
                {accounts.map((a) => (
                  <tr
                    key={a.user_id}
                    onClick={() => {
                      setUserId(a.user_id);
                      setConfirmText('');
                    }}
                    className="hover:bg-canvas transition-colors duration-fast cursor-pointer"
                  >
                    <td className="px-400 py-300 font-mono text-ink-primary">{a.user_id}</td>
                    <td className="px-400 py-300 text-ink-muted">{a.primary_email ?? '—'}</td>
                    <td className="px-400 py-300 text-ink-muted">{a.claimed ? 'yes' : 'no'}</td>
                    <td className="px-400 py-300 text-ink-muted font-mono">
                      {a.created_at ?? '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Target + typed confirmation */}
      <div className="rounded-lg border border-hairline bg-elevated p-600 mb-700">
        <div className="flex flex-wrap items-end gap-600">
          <label className="flex flex-col gap-100 text-label uppercase tracking-wider text-ink-muted grow">
            User ID
            <input
              type="text"
              value={userId}
              onChange={(e) => {
                setUserId(e.target.value);
                setConfirmText('');
              }}
              placeholder="e.g. miguel"
              className="rounded-md border border-hairline bg-canvas px-400 py-300 font-mono text-body-md text-ink-primary"
            />
          </label>
          <label className="flex flex-col gap-100 text-label uppercase tracking-wider text-ink-muted grow">
            Type the user ID again to confirm
            <input
              type="text"
              value={confirmText}
              onChange={(e) => setConfirmText(e.target.value)}
              placeholder={target || 'confirm user_id'}
              className="rounded-md border border-hairline bg-canvas px-400 py-300 font-mono text-body-md text-ink-primary"
            />
          </label>
        </div>

        {/* Reset */}
        <div className="mt-600 rounded-md border border-hairline bg-canvas p-500">
          <h3 className="font-display text-title-md text-ink-primary mb-100">
            Reset family data
          </h3>
          <p className="text-body-sm text-ink-muted mb-400">
            Wipes profile, chats, kids, planner, and Circle data. KEEPS the Apple/Google
            sign-in identity and the accepted terms. The tester loop: reset here →
            sign out in the app → relaunch → run onboarding → sign in at step 8 —
            same account, fresh family.
          </p>
          <button
            onClick={doReset}
            disabled={!confirmed || busy !== null}
            className="rounded-md bg-accent px-500 py-300 text-title-md font-medium text-ink-on-photo-light hover:bg-accent-press transition-colors duration-fast disabled:opacity-60"
          >
            {busy === 'reset' ? 'Resetting…' : 'Reset (keeps sign-in)'}
          </button>
        </div>

        {/* Danger: full delete */}
        <div className="mt-500 rounded-md border border-error bg-canvas p-500">
          <h3 className="font-display text-title-md text-error mb-100">
            Danger: full delete
          </h3>
          <p className="text-body-sm text-ink-muted mb-400">
            The complete account delete (DELETE /family). Everything above PLUS the
            sign-in identity — this deletes the sign-in identity too. Next sign-in
            with the same Apple/Google account creates a brand-new, empty user_id.
          </p>
          <button
            onClick={doDelete}
            disabled={!confirmed || busy !== null}
            className="rounded-md bg-error px-500 py-300 text-title-md font-medium text-ink-on-photo-light hover:opacity-90 transition-opacity duration-fast disabled:opacity-60"
          >
            {busy === 'delete' ? 'Deleting…' : 'Delete account + identity'}
          </button>
        </div>
      </div>

      {/* Result readout */}
      {result && (
        <div className="rounded-lg border border-hairline bg-elevated p-600">
          <h2 className="font-display text-title-md text-ink-primary mb-200">
            {result.action === 'reset' ? 'Reset complete' : 'Delete complete'} —{' '}
            <span className="font-mono">{result.data.user_id}</span>
          </h2>
          <p className="text-body-sm text-ink-muted mb-400">
            {result.action === 'reset'
              ? 'Sign-in identity kept. Tell the tester: sign out in the app, relaunch, and run onboarding again — your sign-in stays attached.'
              : 'Sign-in identity deleted. The next sign-in creates a new account.'}
          </p>
          {nonZero.length === 0 ? (
            <p className="text-body-sm text-ink-muted italic">No rows removed.</p>
          ) : (
            <div className="overflow-hidden rounded-md border border-hairline">
              <table className="w-full text-body-sm">
                <thead>
                  <tr className="border-b border-hairline bg-canvas text-left text-label uppercase tracking-wider text-ink-muted">
                    <th className="px-400 py-300">Table</th>
                    <th className="px-400 py-300">Rows removed</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-hairline">
                  {nonZero.map(([table, n]) => (
                    <tr key={table}>
                      <td className="px-400 py-300 font-mono text-ink-primary">{table}</td>
                      <td className="px-400 py-300 text-ink-muted">{n}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
