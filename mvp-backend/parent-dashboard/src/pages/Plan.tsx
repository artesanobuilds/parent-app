import { useEffect, useRef, useState } from 'react';
import { Check, Copy, Download, ExternalLink, Eye, Share2, Undo2, X } from 'lucide-react';
import {
  createShareLink,
  downloadPlanXlsx,
  getActivities,
  getBoard,
  getCalendar,
  getPlanSummary,
  getTodos,
  patchTodo,
  updateActivity,
} from '../api';
import type { ShareScope } from '../api';
import type {
  BoardActivity,
  CalendarEntry,
  PlanBoard,
  PlanSummary,
  Todo,
  TrackedActivity,
} from '../types';

export default function Plan() {
  const [summary, setSummary] = useState<PlanSummary | null>(null);
  const [todos, setTodos] = useState<Todo[]>([]);
  const [entries, setEntries] = useState<CalendarEntry[]>([]);
  const [activities, setActivities] = useState<TrackedActivity[]>([]);
  const [board, setBoard] = useState<PlanBoard | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    try {
      const [s, t, c, a, b] = await Promise.all([
        getPlanSummary(),
        getTodos('open'),
        getCalendar(),
        getActivities(),
        getBoard(),
      ]);
      setSummary(s);
      setTodos(t);
      setEntries(c);
      setActivities(a);
      setBoard(b);
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Failed to load plan');
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function complete(id: string) {
    await patchTodo(id, 'done');
    setTodos((prev) => prev.filter((t) => t.id !== id));
  }

  // Run one board mutation with a per-card busy state, then re-fetch
  // everything (board + summary + todos + calendar) so the page stays fresh.
  async function mutate(activityId: string, fn: () => Promise<unknown>) {
    setBusyId(activityId);
    setErr(null);
    try {
      await fn();
      await load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Update failed');
    } finally {
      setBusyId(null);
    }
  }

  // Week × kid grid derived from calendar entries. Week is taken from
  // week_start, falling back to the Monday of start_ts for day-specific entries.
  const weeks = Array.from(
    new Set(entries.map(weekKey).filter((w): w is string => !!w)),
  ).sort();
  const kids = Array.from(
    new Set(
      [
        ...entries.map((e) => e.kid_name),
        ...activities.map((a) => a.kid_name),
      ].filter((k): k is string => !!k),
    ),
  ).sort();

  const cost = summary?.cost;

  return (
    <div className="p-700 max-w-6xl">
      <div className="text-ink-muted text-xs uppercase tracking-wide">Plan</div>
      <div className="flex items-start justify-between gap-500 mb-600">
        <h1 className="font-display text-3xl text-ink-primary">Your family's plan</h1>
        <PlanToolbar onError={setErr} />
      </div>
      {err && <div className="text-error mb-500">{err}</div>}

      {/* Cost */}
      {cost && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-400 mb-700">
          <Stat label="Confirmed" value={`$${Math.round(cost.confirmed_total)}`} accent />
          <Stat label="Cost TBD" value={String(cost.tbd_count)} />
          <Stat label="Tracked" value={String(cost.item_count)} />
          <Stat label="Kids" value={String(Object.keys(cost.by_kid ?? {}).length)} />
        </div>
      )}

      {/* Callouts */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-500 mb-700">
        <Callout
          title="Pending eligibility"
          tone="warning"
          items={(summary?.pending_eligibility ?? []).map((p) => p.name)}
        />
        <Callout
          title="Coverage gaps"
          tone="error"
          items={(summary?.coverage_gaps ?? []).map((g) =>
            [g.kid_name, g.task].filter(Boolean).join(' · ') +
            (g.reason ? ` — ${g.reason}` : ''),
          )}
        />
        <Callout
          title="Schedule conflicts"
          tone="warning"
          items={(summary?.conflicts ?? []).map((c) => c.detail)}
        />
      </div>

      {/* Activity lifecycle board */}
      {board && <ActivityBoard board={board} busyId={busyId} onMutate={mutate} />}

      {/* Week × kid calendar */}
      {weeks.length > 0 && (
        <div className="mb-700">
          <div className="flex items-baseline justify-between mb-400">
            <h2 className="font-display text-xl text-ink-primary">Calendar</h2>
            <div className="flex items-center gap-400 text-xs text-ink-muted">
              <LegendDot className="bg-accent-tint" label="Confirmed" />
              <LegendDot className="bg-canvas border border-warning" label="Pending" />
              <LegendDot className="bg-canvas border border-hairline" label="Blackout" />
            </div>
          </div>
          <div className="overflow-auto border border-hairline rounded-xl">
            <table className="border-collapse min-w-full text-sm">
              <thead>
                <tr className="bg-canvas">
                  <th className="text-left text-ink-muted font-medium p-400 border-b border-hairline w-40">
                    Week
                  </th>
                  {kids.map((k) => (
                    <th
                      key={k}
                      className="text-left text-ink-primary font-medium p-400 border-b border-hairline"
                    >
                      {k}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {weeks.map((w, i) => (
                  <tr key={w} className={i % 2 ? 'bg-canvas/40' : ''}>
                    <td className="p-400 border-b border-hairline align-top whitespace-nowrap">
                      <div className="text-ink-primary font-medium">{fmtWeekRange(w)}</div>
                      <div className="text-ink-muted text-xs font-mono">{w}</div>
                    </td>
                    {kids.map((k) => {
                      const cell = entries.filter(
                        (e) => weekKey(e) === w && (e.kid_name === k || e.kid_name == null),
                      );
                      return (
                        <td key={k} className="p-400 border-b border-hairline align-top">
                          {cell.length === 0 ? (
                            <span className="text-ink-muted">—</span>
                          ) : (
                            <div className="flex flex-col gap-200">
                              {cell.map((e) => (
                                <span
                                  key={e.id}
                                  className={`inline-block rounded px-300 py-100 text-xs leading-tight ${chipClasses(e)}`}
                                  title={`${e.kind}${e.status ? ` · ${e.status}` : ''}`}
                                >
                                  {e.title}
                                </span>
                              ))}
                            </div>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* To-dos */}
      <h2 className="font-display text-xl text-ink-primary mb-400">Follow-ups</h2>
      {todos.length === 0 ? (
        <p className="text-ink-muted">Nothing open.</p>
      ) : (
        <div className="flex flex-col gap-300 max-w-2xl">
          {todos.map((t) => (
            <div
              key={t.id}
              className="flex items-center gap-400 bg-elevated border border-hairline rounded-lg p-400"
            >
              <button
                onClick={() => complete(t.id)}
                className="w-5 h-5 rounded-full border border-strong hover:bg-accent-tint shrink-0"
                aria-label="Complete"
              />
              <div className="flex-1">
                <div className="text-ink-primary">{t.title}</div>
                {t.due_date && (
                  <div className="text-ink-muted text-xs font-mono">Due {t.due_date}</div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Activity lifecycle board ────────────────────────────────────────
// Stage groups (Considering → To register → Registered → All set) teach the
// flow: each non-empty stage renders its title, count, and blurb; each card
// gets ONE primary action (the backend-computed next_step).
function ActivityBoard({
  board,
  busyId,
  onMutate,
}: {
  board: PlanBoard;
  busyId: string | null;
  onMutate: (activityId: string, fn: () => Promise<unknown>) => void;
}) {
  const stages = board.stages.filter((s) => s.activities.length > 0);
  const total = board.stages.reduce((n, s) => n + s.activities.length, 0);

  return (
    <div className="mb-700">
      <h2 className="font-display text-xl text-ink-primary mb-400">Activities</h2>
      {total === 0 ? (
        <p className="text-ink-muted">
          Nothing tracked yet. Save ideas from Discover → decide → register → we track the rest.
        </p>
      ) : (
        <div className="flex flex-col gap-600">
          {stages.map((s) => (
            <div key={s.key}>
              <div className="flex items-baseline gap-300">
                <h3 className="text-ink-primary font-medium">{s.title}</h3>
                <span className="text-ink-muted text-sm font-mono">{s.activities.length}</span>
              </div>
              <div className="text-ink-muted text-xs mb-300">{s.blurb}</div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-500">
                {s.activities.map((a) => (
                  <BoardCard
                    key={a.id}
                    a={a}
                    gmailConnected={board.gmail_connected}
                    busy={busyId === a.id}
                    onMutate={onMutate}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function BoardCard({
  a,
  gmailConnected,
  busy,
  onMutate,
}: {
  a: BoardActivity;
  gmailConnected: boolean;
  busy: boolean;
  onMutate: (activityId: string, fn: () => Promise<unknown>) => void;
}) {
  const step = a.next_step;
  // Register opens the signup page in a new tab; once opened, offer the
  // follow-through button so the parent can confirm they signed up.
  const [openedSignup, setOpenedSignup] = useState(false);
  const registeredStage = step.stage === 'registered' || step.stage === 'all_set';
  // The top to-do is the primary button for complete_todo cards; the rest
  // render as a small list with their own checkmarks.
  const restTodos = step.action === 'complete_todo' ? a.open_todos.slice(1) : a.open_todos;

  const primaryBtn =
    'flex items-center gap-200 bg-accent text-ink-on-photo-light rounded-lg px-400 py-200 text-sm font-medium disabled:opacity-60';
  const secondaryBtn =
    'border border-hairline rounded-lg px-400 py-200 text-sm text-ink-primary hover:bg-accent-tint disabled:opacity-50';

  const patchStatus = (fields: Record<string, unknown>) =>
    onMutate(a.id, () => updateActivity(a.id, fields));

  function onPrimary() {
    switch (step.action) {
      case 'plan':
        patchStatus({ status: 'planned' });
        break;
      case 'register':
        window.open(step.url ?? undefined, '_blank', 'noopener');
        setOpenedSignup(true);
        break;
      case 'mark_registered':
        patchStatus({ status: 'signed_up' });
        break;
      case 'complete_todo':
        if (step.todo_id) onMutate(a.id, () => patchTodo(step.todo_id!, 'done'));
        break;
      case 'restore':
        patchStatus({ status: 'exploring' });
        break;
    }
  }

  return (
    <div className={`bg-elevated border border-hairline rounded-xl p-600 ${busy ? 'opacity-60' : ''}`}>
      <div className="flex items-start justify-between gap-400">
        <h4 className="font-medium text-ink-primary">{a.name}</h4>
        {step.action === 'plan' && (
          <button
            onClick={() =>
              patchStatus({ status: 'declined', decision_rationale: 'Passed from the board' })
            }
            disabled={busy}
            className="text-ink-muted text-sm hover:text-ink-primary disabled:opacity-50 shrink-0"
          >
            Pass
          </button>
        )}
      </div>
      <div className="flex flex-wrap gap-200 mt-300 text-sm text-ink-secondary">
        {a.kid_name && <span className="bg-accent-tint rounded px-300 py-100">{a.kid_name}</span>}
        {a.provider && <span className="bg-canvas rounded px-300 py-100">{a.provider}</span>}
        {a.price_amount != null && (
          <span className="bg-canvas rounded px-300 py-100 font-mono">${a.price_amount}</span>
        )}
      </div>

      {/* The ONE primary action, hint (its consequence) directly underneath */}
      {step.action !== 'none' && (
        <div className="mt-400">
          {step.action === 'resolve' ? (
            <div className="text-warning text-sm">{step.label}</div>
          ) : step.action === 'register' ? (
            <div className="flex flex-wrap items-center gap-300">
              <button onClick={onPrimary} disabled={busy} className={primaryBtn}>
                <ExternalLink className="w-4 h-4" />
                {step.label}
              </button>
              {openedSignup && (
                <button
                  onClick={() => patchStatus({ status: 'signed_up' })}
                  disabled={busy}
                  className={secondaryBtn}
                >
                  Mark registered
                </button>
              )}
            </div>
          ) : (
            <button onClick={onPrimary} disabled={busy} className={primaryBtn}>
              {step.action === 'complete_todo' && <Check className="w-4 h-4" />}
              {step.action === 'restore' && <Undo2 className="w-4 h-4" />}
              {step.label}
            </button>
          )}
          {step.hint && <div className="text-ink-muted text-xs mt-200">{step.hint}</div>}
        </div>
      )}

      {/* Remaining open to-dos, each completable in place */}
      {restTodos.length > 0 && (
        <div className="mt-300 flex flex-col gap-200">
          {restTodos.map((t) => (
            <div key={t.id} className="flex items-center gap-300 text-sm">
              <button
                onClick={() => onMutate(a.id, () => patchTodo(t.id, 'done'))}
                disabled={busy}
                className="w-4 h-4 rounded-full border border-strong hover:bg-accent-tint shrink-0 disabled:opacity-50"
                aria-label={`Complete ${t.title}`}
              />
              <span className="text-ink-secondary">{t.title}</span>
              {t.due_date && (
                <span className="text-ink-muted text-xs font-mono">Due {t.due_date}</span>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Tracking line: is the system watching this camp's emails? */}
      {registeredStage &&
        (a.watching ? (
          <div className="flex items-center gap-200 text-ink-muted text-xs mt-300">
            <Eye className="w-4 h-4 shrink-0" />
            <span>
              Watching {a.provider ?? a.name}&apos;s emails for confirmations &amp; payment
              reminders
            </span>
          </div>
        ) : !a.watchable ? (
          <div className="text-warning text-xs mt-300">
            Add the camp&apos;s contact email so I can watch for confirmations
          </div>
        ) : !gmailConnected ? (
          <div className="text-ink-muted text-xs mt-300">
            Connect Gmail to auto-track camp emails
          </div>
        ) : null)}
    </div>
  );
}

// ── Export / share toolbar ──────────────────────────────────────────
const SHARE_SCOPES: { scope: ShareScope; label: string; hint: string }[] = [
  { scope: 'full', label: 'Full plan', hint: 'Everything below' },
  { scope: 'logistics', label: 'Nanny', hint: 'Schedule & coverage' },
  { scope: 'therapy', label: 'Therapist', hint: 'Therapy schedule' },
];

function PlanToolbar({ onError }: { onError: (msg: string | null) => void }) {
  const [exporting, setExporting] = useState(false);
  const [shareOpen, setShareOpen] = useState(false);

  async function onExport() {
    setExporting(true);
    onError(null);
    try {
      await downloadPlanXlsx();
    } catch (e) {
      onError(e instanceof Error ? e.message : 'Export failed');
    } finally {
      setExporting(false);
    }
  }

  return (
    <div className="flex items-center gap-300 shrink-0">
      <button
        onClick={onExport}
        disabled={exporting}
        className="flex items-center gap-200 bg-elevated border border-hairline rounded-xl px-400 py-200 text-sm text-ink-primary hover:bg-accent-tint disabled:opacity-50"
      >
        <Download className="w-4 h-4" />
        {exporting ? 'Exporting…' : 'Export'}
      </button>
      <div className="relative">
        <button
          onClick={() => setShareOpen((v) => !v)}
          className="flex items-center gap-200 bg-elevated border border-hairline rounded-xl px-400 py-200 text-sm text-ink-primary hover:bg-accent-tint"
        >
          <Share2 className="w-4 h-4" />
          Share
        </button>
        {shareOpen && <SharePanel onClose={() => setShareOpen(false)} onError={onError} />}
      </div>
    </div>
  );
}

function SharePanel({
  onClose,
  onError,
}: {
  onClose: () => void;
  onError: (msg: string | null) => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [busy, setBusy] = useState<ShareScope | null>(null);
  const [link, setLink] = useState<{ scope: ShareScope; url: string } | null>(null);
  const [copied, setCopied] = useState(false);

  // Close on outside click.
  useEffect(() => {
    function onDown(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    }
    document.addEventListener('mousedown', onDown);
    return () => document.removeEventListener('mousedown', onDown);
  }, [onClose]);

  async function pick(scope: ShareScope) {
    setBusy(scope);
    setCopied(false);
    onError(null);
    try {
      const res = await createShareLink(scope);
      setLink({ scope, url: res.url });
    } catch (e) {
      onError(e instanceof Error ? e.message : 'Could not create share link');
    } finally {
      setBusy(null);
    }
  }

  async function copy() {
    if (!link) return;
    try {
      await navigator.clipboard.writeText(link.url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      onError('Could not copy to clipboard');
    }
  }

  return (
    <div
      ref={ref}
      className="absolute right-0 mt-200 w-80 bg-elevated border border-hairline rounded-xl shadow-lg p-500 z-10"
    >
      <div className="flex items-center justify-between mb-300">
        <div className="text-ink-primary font-medium text-sm">Share plan</div>
        <button onClick={onClose} className="text-ink-muted hover:text-ink-primary" aria-label="Close">
          <X className="w-4 h-4" />
        </button>
      </div>
      <div className="text-ink-muted text-xs mb-400">
        Creates a read-only public link. Choose what it shows:
      </div>
      <div className="flex flex-col gap-200">
        {SHARE_SCOPES.map((s) => (
          <button
            key={s.scope}
            onClick={() => pick(s.scope)}
            disabled={busy !== null}
            className={`flex items-center justify-between text-left border rounded-lg px-400 py-300 hover:bg-accent-tint disabled:opacity-50 ${
              link?.scope === s.scope ? 'border-accent' : 'border-hairline'
            }`}
          >
            <div>
              <div className="text-ink-primary text-sm">{s.label}</div>
              <div className="text-ink-muted text-xs">{s.hint}</div>
            </div>
            {busy === s.scope && <span className="text-ink-muted text-xs">…</span>}
          </button>
        ))}
      </div>
      {link && (
        <div className="mt-400">
          <div className="flex items-center gap-200 bg-canvas border border-hairline rounded-lg px-300 py-200">
            <span className="flex-1 text-ink-secondary text-xs font-mono truncate" title={link.url}>
              {link.url}
            </span>
            <button
              onClick={copy}
              className="flex items-center gap-100 text-ink-primary hover:text-accent shrink-0"
              aria-label="Copy link"
            >
              {copied ? <Check className="w-4 h-4 text-accent" /> : <Copy className="w-4 h-4" />}
            </button>
          </div>
          <div className="text-ink-muted text-xs mt-200">Anyone with this link can view (read-only).</div>
        </div>
      )}
    </div>
  );
}

// ── Calendar helpers ────────────────────────────────────────────────
/** Monday (ISO yyyy-mm-dd) of a date. */
function isoMonday(d: Date): string {
  const day = (d.getUTCDay() + 6) % 7; // 0 = Monday
  const mon = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate() - day));
  return mon.toISOString().slice(0, 10);
}

/** Bucket an entry into a week: week_start if present, else Monday of start_ts. */
function weekKey(e: CalendarEntry): string | null {
  if (e.week_start) return e.week_start;
  if (e.start_ts) {
    const d = new Date(e.start_ts);
    if (!Number.isNaN(d.getTime())) return isoMonday(d);
  }
  return null;
}

/** "Jul 6–10" (Mon–Fri) for a Monday ISO date. */
function fmtWeekRange(iso: string): string {
  const mon = new Date(`${iso}T00:00:00Z`);
  if (Number.isNaN(mon.getTime())) return iso;
  const fri = new Date(mon.getTime());
  fri.setUTCDate(mon.getUTCDate() + 4);
  const m = (d: Date) => d.toLocaleDateString('en-US', { month: 'short', timeZone: 'UTC' });
  const mMon = m(mon);
  const mFri = m(fri);
  return mMon === mFri
    ? `${mMon} ${mon.getUTCDate()}–${fri.getUTCDate()}`
    : `${mMon} ${mon.getUTCDate()} – ${mFri} ${fri.getUTCDate()}`;
}

/** Chip styling by kind/status (uses only defined Hearth Tailwind tokens). */
function chipClasses(e: CalendarEntry): string {
  const kind = (e.kind || '').toLowerCase();
  const status = (e.status || '').toLowerCase();
  if (kind === 'blackout' || kind === 'holiday')
    return 'bg-canvas text-ink-muted line-through';
  if (status === 'confirmed') return 'bg-accent-tint text-ink-primary';
  if (status === 'pending' || status === 'tentative' || status === 'tbd')
    return 'bg-canvas text-warning border border-warning';
  return 'bg-canvas text-ink-secondary border border-hairline';
}

function LegendDot({ className, label }: { className: string; label: string }) {
  return (
    <span className="flex items-center gap-100">
      <span className={`inline-block w-3 h-3 rounded ${className}`} />
      {label}
    </span>
  );
}

function Stat({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className="bg-elevated border border-hairline rounded-xl p-500">
      <div className={`font-display text-2xl ${accent ? 'text-accent' : 'text-ink-primary'}`}>
        {value}
      </div>
      <div className="text-ink-muted text-xs uppercase tracking-wide mt-100">{label}</div>
    </div>
  );
}

function Callout({
  title,
  items,
  tone,
}: {
  title: string;
  items: string[];
  tone: 'warning' | 'error';
}) {
  if (items.length === 0) return null;
  const color = tone === 'error' ? 'text-error' : 'text-warning';
  return (
    <div className="bg-elevated border border-hairline rounded-xl p-500">
      <div className={`text-xs uppercase tracking-wide font-medium ${color} mb-300`}>{title}</div>
      <ul className="flex flex-col gap-200">
        {items.map((item, i) => (
          <li key={i} className="text-ink-primary text-sm">
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
