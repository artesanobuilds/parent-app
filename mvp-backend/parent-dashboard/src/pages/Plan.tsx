import { useEffect, useState } from 'react';
import { getActivities, getCalendar, getPlanSummary, getTodos, patchTodo } from '../api';
import type { CalendarEntry, PlanSummary, Todo, TrackedActivity } from '../types';

export default function Plan() {
  const [summary, setSummary] = useState<PlanSummary | null>(null);
  const [todos, setTodos] = useState<Todo[]>([]);
  const [entries, setEntries] = useState<CalendarEntry[]>([]);
  const [activities, setActivities] = useState<TrackedActivity[]>([]);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    try {
      const [s, t, c, a] = await Promise.all([
        getPlanSummary(),
        getTodos('open'),
        getCalendar(),
        getActivities(),
      ]);
      setSummary(s);
      setTodos(t);
      setEntries(c);
      setActivities(a);
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
      <h1 className="font-display text-3xl text-ink-primary mb-600">Your family's plan</h1>
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
