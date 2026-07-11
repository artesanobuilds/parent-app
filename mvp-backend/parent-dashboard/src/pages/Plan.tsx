import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Check,
  Copy,
  Download,
  Plus,
  RotateCcw,
  Share2,
  X,
} from 'lucide-react';
import {
  createShareLink,
  downloadPlanXlsx,
  getActivities,
  getBoard,
  getCalendar,
  getPlanSummary,
  getTodos,
  patchTodo,
  resetPlan,
} from '../api';
import type { ShareScope } from '../api';
import type {
  CalendarEntry,
  PlanBoard,
  PlanSummary,
  Todo,
  TrackedActivity,
  VerticalDoor,
} from '../types';
import { BoardCard, CHIP_LABELS } from '../components/Card';
import { cachedDoors, fetchDoors } from '../lib/doors';
import { capture } from '../analytics';

export default function Plan() {
  const [summary, setSummary] = useState<PlanSummary | null>(null);
  const [todos, setTodos] = useState<Todo[]>([]);
  const [entries, setEntries] = useState<CalendarEntry[]>([]);
  const [activities, setActivities] = useState<TrackedActivity[]>([]);
  const [board, setBoard] = useState<PlanBoard | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  // Doors render from last-good cache immediately; the fetch refreshes them.
  // Never blocks board render (fail-open rule).
  const [doors, setDoors] = useState<VerticalDoor[]>(cachedDoors());

  useEffect(() => {
    void fetchDoors().then(setDoors);
  }, []);

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
        <PlanToolbar onError={setErr} onReload={load} />
      </div>
      {err && <div className="text-error mb-500">{err}</div>}

      {/* Cost */}
      {cost && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-400 mb-700">
          <Stat label="Confirmed" value={`$${Math.round(cost.confirmed_total)}`} accent />
          <Stat label="Cost TBD" value={String(cost.tbd_count)} />
          <Stat label="Tracked" value={String(cost.item_count)} />
          {/* Family-level items (a trip has no kid) serialize under a "null"
              bucket — they're not a kid. */}
          <Stat
            label="Kids"
            value={String(
              Object.keys(cost.by_kid ?? {}).filter((k) => k && k !== 'null').length,
            )}
          />
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
      {board && (
        <ActivityBoard board={board} busyId={busyId} onMutate={mutate} doors={doors} />
      )}

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
  doors,
}: {
  board: PlanBoard;
  busyId: string | null;
  onMutate: (activityId: string, fn: () => Promise<unknown>) => void;
  doors: VerticalDoor[];
}) {
  const navigate = useNavigate();
  // Vertical is an ATTRIBUTE + chip filter, never navigation (plan rule).
  const [typeFilter, setTypeFilter] = useState<string | null>(null);
  const [doorsOpen, setDoorsOpen] = useState(false);

  const total = board.stages.reduce((n, s) => n + s.activities.length, 0);
  const typeCounts = new Map<string, number>();
  for (const s of board.stages)
    for (const a of s.activities) {
      const t = a.activity_type ?? 'camp';
      typeCounts.set(t, (typeCounts.get(t) ?? 0) + 1);
    }
  // The chip row appears only when the board actually spans verticals.
  const multiVertical = typeCounts.size > 1;
  const filtered = board.stages.map((s) => ({
    ...s,
    activities: typeFilter
      ? s.activities.filter((a) => (a.activity_type ?? 'camp') === typeFilter)
      : s.activities,
  }));
  const stages = filtered.filter((s) => s.activities.length > 0);

  function openDoor(d: VerticalDoor) {
    capture('door_opened', { door: d.key });
    navigate('/chat', { state: { starter: d.starter_prompt, door: d.key } });
  }

  const chipBtn = (active: boolean) =>
    `rounded-full border px-400 py-100 text-sm ${
      active
        ? 'border-accent text-ink-primary bg-accent-tint'
        : 'border-hairline text-ink-secondary hover:text-ink-primary'
    }`;

  return (
    <div className="mb-700">
      <div className="flex items-center justify-between gap-400 mb-400">
        <h2 className="font-display text-xl text-ink-primary">Activities</h2>
        {/* The five doors, behind ONE disclosure — no new tabs/segments. */}
        {doors.length > 0 && (
          <div className="relative">
            <button
              onClick={() => setDoorsOpen((v) => !v)}
              className="flex items-center gap-200 bg-accent text-ink-on-photo-light rounded-lg px-400 py-200 text-sm font-medium"
            >
              <Plus className="w-4 h-4" />
              Plan something
            </button>
            {doorsOpen && (
              <div className="absolute right-0 mt-200 w-72 bg-elevated border border-hairline rounded-xl shadow-lg z-10 p-300 flex flex-col">
                {doors.map((d) => (
                  <button
                    key={d.key}
                    onClick={() => openDoor(d)}
                    className="text-left rounded-lg px-300 py-300 hover:bg-accent-tint"
                  >
                    <div className="text-ink-primary font-medium text-sm">{d.title}</div>
                    <div className="text-ink-muted text-xs">{d.subtitle}</div>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
      {multiVertical && (
        <div className="flex flex-wrap gap-300 mb-400">
          <button onClick={() => setTypeFilter(null)} className={chipBtn(typeFilter === null)}>
            All {total}
          </button>
          {[...typeCounts.entries()].map(([t, n]) => (
            <button key={t} onClick={() => setTypeFilter(t)} className={chipBtn(typeFilter === t)}>
              {CHIP_LABELS[t] ?? t} {n}
            </button>
          ))}
        </div>
      )}
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
                    showVerticalChip={multiVertical}
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

// ── Export / share toolbar ──────────────────────────────────────────
const SHARE_SCOPES: { scope: ShareScope; label: string; hint: string }[] = [
  { scope: 'full', label: 'Full plan', hint: 'Everything below' },
  { scope: 'logistics', label: 'Nanny', hint: 'Schedule & coverage' },
  { scope: 'therapy', label: 'Therapist', hint: 'Therapy schedule' },
];

function PlanToolbar({
  onError,
  onReload,
}: {
  onError: (msg: string | null) => void;
  onReload: () => Promise<void>;
}) {
  const [exporting, setExporting] = useState(false);
  const [shareOpen, setShareOpen] = useState(false);
  const [resetOpen, setResetOpen] = useState(false);

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
      <div className="relative">
        <button
          onClick={() => setResetOpen((v) => !v)}
          className="flex items-center gap-200 bg-elevated border border-hairline rounded-xl px-400 py-200 text-sm text-ink-primary hover:bg-accent-tint"
        >
          <RotateCcw className="w-4 h-4" />
          Start over
        </button>
        {resetOpen && (
          <ResetPanel
            onClose={() => setResetOpen(false)}
            onError={onError}
            onReload={onReload}
          />
        )}
      </div>
    </div>
  );
}

// Confirm panel for "Start over" (same popover idiom as SharePanel).
function ResetPanel({
  onClose,
  onError,
  onReload,
}: {
  onClose: () => void;
  onError: (msg: string | null) => void;
  onReload: () => Promise<void>;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [busy, setBusy] = useState(false);

  // Close on outside click.
  useEffect(() => {
    function onDown(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    }
    document.addEventListener('mousedown', onDown);
    return () => document.removeEventListener('mousedown', onDown);
  }, [onClose]);

  async function run() {
    setBusy(true);
    onError(null);
    try {
      await resetPlan();
      await onReload();
      onClose();
    } catch (e) {
      onError(e instanceof Error ? e.message : 'Could not start over');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      ref={ref}
      className="absolute right-0 mt-200 w-80 bg-elevated border border-hairline rounded-xl shadow-lg p-500 z-10"
    >
      <div className="flex items-center justify-between mb-300">
        <div className="text-ink-primary font-medium text-sm">Start over?</div>
        <button onClick={onClose} className="text-ink-muted hover:text-ink-primary" aria-label="Close">
          <X className="w-4 h-4" />
        </button>
      </div>
      <div className="text-ink-muted text-xs mb-400">
        Clears your plan — activities, to-dos, calendar, coverage, and discovery results.
        Your family profile and chats stay. Google-synced calendar events aren&apos;t removed.
      </div>
      <div className="flex items-center gap-300">
        <button
          onClick={run}
          disabled={busy}
          className="flex items-center gap-200 bg-error text-ink-on-photo-light rounded-lg px-400 py-200 text-sm font-medium disabled:opacity-60"
        >
          <RotateCcw className="w-4 h-4" />
          {busy ? 'Starting over…' : 'Yes, start over'}
        </button>
        <button
          onClick={onClose}
          disabled={busy}
          className="border border-hairline rounded-lg px-400 py-200 text-sm text-ink-primary hover:bg-accent-tint disabled:opacity-50"
        >
          Cancel
        </button>
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
