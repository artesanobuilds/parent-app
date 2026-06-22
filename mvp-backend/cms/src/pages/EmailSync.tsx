import { useEffect, useState } from 'react';
import {
  getEmailSyncConfig,
  getEmailSyncRuns,
  putEmailSyncConfig,
  runEmailSyncNow,
  type EmailSyncRun,
  type EmailSyncSchedule,
} from '../api';
import { toast } from '../components/shared/Toast';

const TIMEZONES = [
  'America/Los_Angeles',
  'America/Denver',
  'America/Chicago',
  'America/New_York',
  'UTC',
];

export function EmailSync() {
  const [cfg, setCfg] = useState<EmailSyncSchedule>({
    enabled: false,
    hour: 6,
    tz: 'America/Los_Angeles',
  });
  const [runs, setRuns] = useState<EmailSyncRun[]>([]);
  const [saving, setSaving] = useState(false);
  const [running, setRunning] = useState(false);
  const [loading, setLoading] = useState(true);

  async function loadRuns() {
    try {
      setRuns(await getEmailSyncRuns());
    } catch {
      toast.error('Failed to load runs');
    }
  }

  useEffect(() => {
    Promise.all([
      getEmailSyncConfig().then(setCfg).catch(() => toast.error('Failed to load config')),
      loadRuns(),
    ]).finally(() => setLoading(false));
  }, []);

  async function save() {
    setSaving(true);
    try {
      const next = await putEmailSyncConfig(cfg);
      setCfg(next);
      toast.success('Schedule saved');
    } catch {
      toast.error('Failed to save schedule');
    } finally {
      setSaving(false);
    }
  }

  async function runNow() {
    setRunning(true);
    try {
      const res = await runEmailSyncNow();
      toast.success(`Queued ${res.enqueued} sync run(s)`);
      setTimeout(loadRuns, 1500);
    } catch (e) {
      toast.error(e instanceof Error && e.message.includes('400')
        ? 'No connected Gmail accounts to sync'
        : 'Failed to start sync');
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="p-800 max-w-5xl mx-auto">
      <h1 className="font-display text-display-sm text-ink-primary mb-200">Email Sync</h1>
      <p className="text-ink-muted text-body-sm mb-700">
        The daily agent pulls camp emails from each parent's connected Gmail for their
        registered activities and folds dates, payments, and forms into the plan.
      </p>

      {/* Schedule + manual trigger */}
      <div className="rounded-lg border border-hairline bg-elevated p-600 mb-700">
        <div className="flex flex-wrap items-end gap-600">
          <label className="flex items-center gap-300 text-body-md text-ink-primary">
            <input
              type="checkbox"
              checked={cfg.enabled}
              onChange={(e) => setCfg({ ...cfg, enabled: e.target.checked })}
              className="h-4 w-4 accent-accent"
            />
            Run daily
          </label>

          <label className="flex flex-col gap-100 text-label uppercase tracking-wider text-ink-muted">
            Time of day
            <select
              value={cfg.hour}
              onChange={(e) => setCfg({ ...cfg, hour: Number(e.target.value) })}
              className="rounded-md border border-hairline bg-canvas px-400 py-300 text-body-md text-ink-primary"
            >
              {Array.from({ length: 24 }, (_, h) => (
                <option key={h} value={h}>
                  {String(h).padStart(2, '0')}:00
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-100 text-label uppercase tracking-wider text-ink-muted">
            Timezone
            <select
              value={cfg.tz}
              onChange={(e) => setCfg({ ...cfg, tz: e.target.value })}
              className="rounded-md border border-hairline bg-canvas px-400 py-300 text-body-md text-ink-primary"
            >
              {TIMEZONES.map((tz) => (
                <option key={tz} value={tz}>{tz}</option>
              ))}
            </select>
          </label>

          <div className="flex gap-300 ml-auto">
            <button
              onClick={save}
              disabled={saving}
              className="rounded-md bg-accent px-500 py-300 text-title-md font-medium text-ink-on-photo-light hover:bg-accent-press transition-colors duration-fast disabled:opacity-60"
            >
              {saving ? 'Saving…' : 'Save schedule'}
            </button>
            <button
              onClick={runNow}
              disabled={running}
              className="rounded-md border border-strong px-500 py-300 text-title-md font-medium text-ink-primary hover:bg-canvas transition-colors duration-fast disabled:opacity-60"
            >
              {running ? 'Starting…' : 'Run now'}
            </button>
          </div>
        </div>
      </div>

      {/* Recent runs */}
      <h2 className="font-display text-title-md text-ink-primary mb-400">Recent runs</h2>
      {loading ? (
        <div className="text-center py-1000 text-ink-muted text-body-sm">Loading…</div>
      ) : runs.length === 0 ? (
        <div className="text-center py-1000 text-ink-muted text-body-sm">No runs yet.</div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-hairline bg-elevated">
          <table className="w-full text-body-md">
            <thead>
              <tr className="border-b border-hairline bg-canvas text-left text-label font-semibold uppercase tracking-wider text-ink-muted">
                <th className="px-500 py-400">Status</th>
                <th className="px-500 py-400">Trigger</th>
                <th className="px-500 py-400">User</th>
                <th className="px-500 py-400">Messages</th>
                <th className="px-500 py-400">Activities</th>
                <th className="px-500 py-400">Started</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-hairline">
              {runs.map((r) => (
                <tr key={r.id} className="hover:bg-canvas transition-colors duration-fast">
                  <td className="px-500 py-400 font-medium text-ink-primary">
                    {r.status}
                    {r.error ? <span className="text-error"> — {r.error}</span> : null}
                  </td>
                  <td className="px-500 py-400 text-ink-muted">{r.trigger}</td>
                  <td className="px-500 py-400 text-ink-muted">{r.user_id}</td>
                  <td className="px-500 py-400 text-ink-muted">{r.messages_seen}</td>
                  <td className="px-500 py-400 text-ink-muted">{r.activities_touched}</td>
                  <td className="px-500 py-400 text-ink-muted font-mono text-body-sm">
                    {r.started_at ?? r.created_at ?? '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
