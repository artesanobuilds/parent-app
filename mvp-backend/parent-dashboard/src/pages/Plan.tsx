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

  // Week × kid grid derived from calendar entries.
  const weeks = Array.from(
    new Set(entries.map((e) => e.week_start).filter((w): w is string => !!w)),
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
        <div className="mb-700 overflow-auto">
          <h2 className="font-display text-xl text-ink-primary mb-400">Calendar</h2>
          <table className="border-collapse min-w-full text-sm">
            <thead>
              <tr>
                <th className="text-left text-ink-muted font-medium p-300 border-b border-hairline">
                  Week
                </th>
                {kids.map((k) => (
                  <th
                    key={k}
                    className="text-left text-ink-muted font-medium p-300 border-b border-hairline"
                  >
                    {k}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {weeks.map((w) => (
                <tr key={w}>
                  <td className="p-300 border-b border-hairline font-mono text-ink-secondary align-top">
                    {w}
                  </td>
                  {kids.map((k) => (
                    <td key={k} className="p-300 border-b border-hairline align-top">
                      {entries
                        .filter(
                          (e) =>
                            e.week_start === w &&
                            (e.kid_name === k || e.kid_name == null),
                        )
                        .map((e) => (
                          <div key={e.id} className="mb-200">
                            <span className="text-ink-primary">{e.title}</span>
                          </div>
                        ))}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
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
