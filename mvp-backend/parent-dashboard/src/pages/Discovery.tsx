import { useEffect, useState, type Dispatch, type SetStateAction } from 'react';
import { Bookmark, BookmarkCheck, Loader2, X } from 'lucide-react';
import {
  createResearchRun,
  deleteActivity,
  getActivities,
  getCandidates,
  getProfile,
  getResearchRun,
  streamResearchRun,
  trackActivity,
} from '../api';
import type { Candidate, ResearchProgress, TrackedActivity } from '../types';

// localStorage key: lets us reconnect to an in-flight run after a reload/nav.
const RUN_KEY = 'discovery_active_run';

const clearStoredRun = () => {
  try {
    localStorage.removeItem(RUN_KEY);
  } catch {
    /* ignore storage errors (private mode, etc.) */
  }
};

const fmtElapsed = (s: number) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;

export default function Discovery() {
  const [progress, setProgress] = useState<ResearchProgress | null>(null);
  const [runStatus, setRunStatus] = useState<string | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [zip, setZip] = useState('');
  const [radius, setRadius] = useState(15);
  const [count, setCount] = useState(25);
  const [focus, setFocus] = useState('');
  const [showFocus, setShowFocus] = useState(false);
  const radiusOptions = [5, 10, 25, 50];
  const countOptions = [5, 15, 25, 50];
  const [busy, setBusy] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [err, setErr] = useState<string | null>(null);

  // Phase B — client-side facet filters over the loaded candidates.
  const [cityFilter, setCityFilter] = useState<Set<string>>(new Set());
  const [categoryFilter, setCategoryFilter] = useState<Set<string>>(new Set());
  const [kidFilter, setKidFilter] = useState<Set<string>>(new Set());

  // R1 — "Exploring" shortlist.
  const [exploring, setExploring] = useState<TrackedActivity[]>([]);
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());
  const [savingIds, setSavingIds] = useState<Set<string>>(new Set());

  async function refreshShortlist() {
    try {
      const acts = await getActivities();
      setExploring(acts.filter((a) => a.status === 'exploring'));
      setSavedIds(
        new Set(acts.map((a) => a.candidate_id).filter((x): x is string => !!x)),
      );
    } catch {
      /* shortlist is best-effort */
    }
  }

  useEffect(() => {
    refreshShortlist();
  }, []);

  // Live elapsed timer — starts when a run goes busy, clears when it finishes.
  useEffect(() => {
    if (!busy) return;
    setElapsed(0);
    const t = setInterval(() => setElapsed((s) => s + 1), 1000);
    return () => clearInterval(t);
  }, [busy]);

  async function saveCandidate(c: Candidate) {
    if (savedIds.has(c.id) || savingIds.has(c.id)) return;
    setSavingIds((s) => new Set(s).add(c.id));
    try {
      const kid = c.fit_kids?.[0] ?? c.kid_name ?? undefined;
      await trackActivity({
        name: c.name,
        candidate_id: c.id,
        kid_name: kid,
        provider: c.provider,
        price_amount: c.price_amount,
        signup_url: c.signup_url,
      });
      setSavedIds((s) => new Set(s).add(c.id));
      await refreshShortlist();
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Could not save to shortlist');
    } finally {
      setSavingIds((s) => {
        const n = new Set(s);
        n.delete(c.id);
        return n;
      });
    }
  }

  // Un-track an activity (un-pin from Exploring). refreshShortlist recomputes
  // savedIds, so a saved candidate's button flips back to "Save".
  async function removeActivity(activityId: string) {
    try {
      await deleteActivity(activityId);
      await refreshShortlist();
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Could not remove from shortlist');
    }
  }

  // Save if not saved; un-save (remove the linked tracked activity) if it is.
  async function toggleSave(c: Candidate) {
    if (savingIds.has(c.id)) return;
    if (savedIds.has(c.id)) {
      const act = exploring.find((a) => a.candidate_id === c.id);
      if (act) await removeActivity(act.id);
    } else {
      await saveCandidate(c);
    }
  }

  // Prefill the ZIP from the saved profile (don't override anything typed).
  useEffect(() => {
    getProfile()
      .then((p) => {
        const z = p.parent?.postal_code;
        if (z) setZip((prev) => prev || z);
      })
      .catch(() => {
        /* no profile yet — leave the field empty */
      });
  }, []);

  // Stream + reconcile-poll an existing run to completion. Callable both for a
  // freshly-created run and when re-attaching to an in-flight one after a reload.
  async function attachToRun(run_id: string) {
    // Live updates over SSE — one held connection, no polling. If the stream
    // errors/ends early we reconcile (and briefly poll) below.
    try {
      await streamResearchRun(run_id, (frame) => {
        setProgress(frame.progress ?? null);
        setRunStatus(frame.status);
      });
    } catch {
      /* fall through to reconcile/poll */
    }
    let s = await getResearchRun(run_id);
    setRunStatus(s.status);
    const deadline = Date.now() + 300_000;
    while (
      s.status !== 'done' &&
      s.status !== 'failed' &&
      s.status !== 'error' &&
      Date.now() < deadline
    ) {
      await new Promise((r) => setTimeout(r, 3000));
      s = await getResearchRun(run_id);
      setProgress(s.progress ?? null);
      setRunStatus(s.status);
    }
    if (s.status === 'done') {
      setCandidates(await getCandidates(run_id));
      clearStoredRun();
    } else if (s.status === 'failed' || s.status === 'error') {
      setErr(s.error ?? 'The discovery run failed.');
      clearStoredRun();
    }
  }

  async function run() {
    setBusy(true);
    setErr(null);
    setCandidates([]);
    setProgress(null);
    setRunStatus(null);
    clearFilters();
    try {
      const trimmedZip = zip.trim();
      const params: Record<string, unknown> = {
        season: 'summer 2026',
        radius_miles: radius,
        max_candidates: count,
      };
      const f = focus.trim();
      if (f) params.focus = f;
      const { run_id } = await createResearchRun(
        params,
        trimmedZip ? { postal_code: trimmedZip, country: 'US' } : undefined,
      );
      try {
        localStorage.setItem(RUN_KEY, run_id);
      } catch {
        /* ignore storage errors */
      }
      await attachToRun(run_id);
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Could not start a run');
    } finally {
      setBusy(false);
    }
  }

  // Reconnect to an in-flight run after a reload/navigation. Never auto-starts
  // a new run — only resumes/loads one we previously persisted.
  useEffect(() => {
    let stored: string | null = null;
    try {
      stored = localStorage.getItem(RUN_KEY);
    } catch {
      /* ignore storage errors */
    }
    if (!stored) return;
    const run_id = stored;
    let cancelled = false;
    (async () => {
      try {
        const s = await getResearchRun(run_id);
        if (cancelled) return;
        if (s.status === 'done') {
          setProgress(s.progress ?? null);
          setRunStatus(s.status);
          setCandidates(await getCandidates(run_id));
          clearStoredRun();
        } else if (s.status === 'failed' || s.status === 'error') {
          clearStoredRun();
        } else {
          // Still running or queued — resume streaming/polling.
          setBusy(true);
          setProgress(s.progress ?? null);
          setRunStatus(s.status);
          try {
            await attachToRun(run_id);
          } finally {
            if (!cancelled) setBusy(false);
          }
        }
      } catch {
        // Run is gone / errored — drop it and show the normal form.
        clearStoredRun();
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Phase B: client-side facet filtering ────────────────────────────
  function clearFilters() {
    setCityFilter(new Set());
    setCategoryFilter(new Set());
    setKidFilter(new Set());
  }

  const toggleFacet = (setter: Dispatch<SetStateAction<Set<string>>>, v: string) =>
    setter((prev) => {
      const n = new Set(prev);
      if (n.has(v)) n.delete(v);
      else n.add(v);
      return n;
    });

  const kidsOf = (c: Candidate): string[] =>
    c.fit_kids && c.fit_kids.length > 0 ? c.fit_kids : c.kid_name ? [c.kid_name] : [];

  const distinct = (vals: (string | null | undefined)[]): string[] =>
    Array.from(new Set(vals.filter((v): v is string => !!v))).sort();

  const cityFacets = distinct(candidates.map((c) => c.city));
  const categoryFacets = distinct(candidates.map((c) => c.category));
  const kidFacets = distinct(candidates.flatMap(kidsOf));

  // AND across groups, OR within a group.
  const filtered = candidates.filter((c) => {
    if (cityFilter.size && !(c.city && cityFilter.has(c.city))) return false;
    if (categoryFilter.size && !(c.category && categoryFilter.has(c.category))) return false;
    if (kidFilter.size && !kidsOf(c).some((k) => kidFilter.has(k))) return false;
    return true;
  });
  const activeFilterCount = cityFilter.size + categoryFilter.size + kidFilter.size;
  const hasFacetBar =
    candidates.length > 0 &&
    (cityFacets.length >= 2 || categoryFacets.length >= 2 || kidFacets.length >= 2);

  const facetGroup = (
    label: string,
    values: string[],
    active: Set<string>,
    setter: Dispatch<SetStateAction<Set<string>>>,
  ) => {
    if (values.length < 2) return null;
    return (
      <div className="flex items-center gap-200 flex-wrap">
        <span className="text-ink-muted text-xs uppercase tracking-wide w-16 shrink-0">
          {label}
        </span>
        {values.map((v) => (
          <button
            key={v}
            onClick={() => toggleFacet(setter, v)}
            className={`rounded px-300 py-100 text-sm border ${
              active.has(v)
                ? 'bg-accent-tint border-accent text-ink-primary'
                : 'border-hairline text-ink-secondary hover:border-accent'
            }`}
          >
            {v}
          </button>
        ))}
      </div>
    );
  };

  // ── Phase C: waiting-UX derived state ───────────────────────────────
  const previewList = progress?.candidates_preview ?? [];
  const hasPreview = previewList.length > 0;
  const isQueued = (runStatus === 'queued' || progress?.phase === 'queued') && !hasPreview;

  return (
    <div className="p-700 max-w-5xl">
      <div className="flex items-center justify-between mb-700">
        <div>
          <div className="text-ink-muted text-xs uppercase tracking-wide">Discover</div>
          <h1 className="font-display text-3xl text-ink-primary">Find activities</h1>
        </div>
        <div className="flex items-center gap-300">
          <input
            value={zip}
            onChange={(e) => setZip(e.target.value)}
            placeholder="ZIP (e.g. 95448)"
            className="w-36 border border-strong rounded-lg px-400 py-300 bg-elevated outline-none focus:border-accent"
          />
          <select
            value={radius}
            onChange={(e) => setRadius(Number(e.target.value))}
            className="border border-strong rounded-lg px-400 py-300 bg-elevated outline-none focus:border-accent"
            aria-label="Search radius"
          >
            {radiusOptions.map((mi) => (
              <option key={mi} value={mi}>
                {mi} mi
              </option>
            ))}
          </select>
          <select
            value={count}
            onChange={(e) => setCount(Number(e.target.value))}
            className="border border-strong rounded-lg px-400 py-300 bg-elevated outline-none focus:border-accent"
            aria-label="How many to find"
          >
            {countOptions.map((n) => (
              <option key={n} value={n}>
                Find {n}
              </option>
            ))}
          </select>
          <button
            onClick={run}
            disabled={busy}
            className="bg-accent text-ink-on-photo-light rounded-lg px-500 py-300 font-medium disabled:opacity-60"
          >
            {busy ? 'Searching…' : 'Find activities'}
          </button>
        </div>
      </div>

      {/* Optional free-form focus — hidden until asked for, so the default is just ZIP + radius. */}
      <div className="mb-700">
        {showFocus ? (
          <div className="flex flex-col gap-200">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-ink-secondary">Focus (optional)</label>
              <button
                onClick={() => {
                  setShowFocus(false);
                  setFocus('');
                }}
                className="text-ink-muted text-sm hover:text-ink-secondary"
              >
                Remove
              </button>
            </div>
            <textarea
              value={focus}
              onChange={(e) => setFocus(e.target.value)}
              rows={2}
              placeholder="e.g. art camps only · physical activity · just for Ceiba"
              className="w-full border border-strong rounded-lg px-400 py-300 bg-elevated outline-none focus:border-accent resize-y"
            />
          </div>
        ) : (
          <button
            onClick={() => setShowFocus(true)}
            className="text-accent text-sm font-medium"
          >
            + Add focus (optional)
          </button>
        )}
      </div>

      {busy && (
        <div className="bg-elevated border border-hairline rounded-xl p-600 mb-600">
          <div className="flex items-center gap-300">
            <Loader2 className="animate-spin text-accent" size={18} />
            <span className="font-medium text-ink-primary">
              {isQueued
                ? 'Waiting for a free research slot…'
                : (progress?.detail ?? 'Researching activities near you…')}
            </span>
          </div>
          <div className="text-ink-muted text-sm mt-200">
            Usually takes 1–2 minutes. · {fmtElapsed(elapsed)} elapsed
          </div>
          {typeof progress?.candidates_found === 'number' && (
            <div className="text-accent text-sm mt-200">
              {progress.candidates_found}
              {/* drop "of N" once we hit the soft target so it never reads "27 of 25" */}
              {progress.candidates_target && progress.candidates_found < progress.candidates_target
                ? ` of ${progress.candidates_target}`
                : ''}{' '}
              found
            </div>
          )}
          {Array.isArray(progress?.recent) && progress.recent.length > 0 && (
            <ul className="mt-400 flex flex-col gap-100 border-t border-hairline pt-400">
              {progress.recent
                .slice()
                .reverse()
                .map((r, i) => (
                  <li
                    key={`${i}-${r}`}
                    className={`text-sm ${i === 0 ? 'text-ink-primary' : 'text-ink-muted'}`}
                  >
                    {r}
                  </li>
                ))}
            </ul>
          )}
        </div>
      )}
      {err && <div className="text-error mb-600">{err}</div>}

      {/* Phase C — live partial results while the run is in flight. Read-only
          preview cards (no Save); the authoritative list replaces them on done. */}
      {busy && hasPreview && (
        <div className="mb-600">
          <div className="text-ink-muted text-xs uppercase tracking-wide mb-300">
            Found so far
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-500">
            {previewList.map((p, i) => (
              <div
                key={`${i}-${p.name}`}
                className="bg-elevated border border-hairline rounded-xl p-600 opacity-90"
              >
                <div className="flex items-start justify-between gap-400">
                  <h2 className="font-medium text-ink-primary">{p.name}</h2>
                  {p.fit_score != null && (
                    <span className="text-accent font-mono text-sm">
                      {Math.round(p.fit_score * 100)}%
                    </span>
                  )}
                </div>
                {p.city && (
                  <div className="text-ink-secondary text-sm mt-200">{p.city}</div>
                )}
                {(p.category || p.kid_name) && (
                  <div className="flex flex-wrap gap-200 mt-400 text-sm text-ink-secondary">
                    {p.kid_name && (
                      <span className="bg-accent-tint rounded px-300 py-100">{p.kid_name}</span>
                    )}
                    {p.category && (
                      <span className="bg-canvas rounded px-300 py-100">{p.category}</span>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Skeleton shimmer before the first preview arrives (and not queued). */}
      {busy && !hasPreview && !isQueued && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-500 mb-600">
          {[0, 1, 2, 3].map((i) => (
            <div
              key={i}
              className="bg-elevated border border-hairline rounded-xl p-600 animate-pulse"
            >
              <div className="h-4 w-2/3 bg-canvas rounded" />
              <div className="h-3 w-1/3 bg-canvas rounded mt-400" />
              <div className="flex gap-200 mt-400">
                <div className="h-5 w-16 bg-canvas rounded" />
                <div className="h-5 w-12 bg-canvas rounded" />
              </div>
            </div>
          ))}
        </div>
      )}

      {exploring.length > 0 && (
        <div className="mb-700">
          <div className="flex items-baseline justify-between mb-300">
            <h2 className="font-display text-2xl text-ink-primary">Exploring</h2>
            <span className="text-ink-muted font-mono text-sm">{exploring.length}</span>
          </div>
          <p className="text-ink-secondary text-sm mb-400">
            Camps you’re considering. Ask your chief of staff to weigh the tradeoffs and help
            you decide.
          </p>
          <div className="flex flex-col gap-300">
            {exploring.map((a) => (
              <div
                key={a.id}
                className="bg-elevated border border-hairline rounded-xl p-500 flex items-center justify-between gap-400"
              >
                <div className="flex items-center gap-300 min-w-0">
                  <BookmarkCheck className="text-accent shrink-0" size={16} />
                  <span className="font-medium text-ink-primary truncate">{a.name}</span>
                  {a.kid_name && (
                    <span className="bg-accent-tint rounded px-300 py-100 text-sm text-ink-secondary shrink-0">
                      {a.kid_name}
                    </span>
                  )}
                  {a.provider && (
                    <span className="text-ink-secondary text-sm truncate">{a.provider}</span>
                  )}
                </div>
                <div className="flex items-center gap-300 shrink-0">
                  {a.price_amount != null && (
                    <span className="font-mono text-sm text-ink-secondary">
                      ${Math.round(a.price_amount)}
                    </span>
                  )}
                  <button
                    onClick={() => removeActivity(a.id)}
                    className="text-ink-muted hover:text-error p-100"
                    aria-label="Remove from shortlist"
                  >
                    <X size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {candidates.length > 0 && (
        <div className="flex items-baseline justify-between mb-300">
          <h2 className="font-display text-2xl text-ink-primary">Best matches</h2>
          <span className="text-ink-muted font-mono text-sm">
            {/* When filters are active, show how many of the pool are shown.
                Otherwise, if we curated from a larger searched pool, say so. */}
            {activeFilterCount > 0
              ? `${filtered.length} of ${candidates.length} shown`
              : progress?.candidates_considered &&
                  progress.candidates_considered > candidates.length
                ? `Top ${candidates.length} of ${progress.candidates_considered} reviewed`
                : `${candidates.length} found`}
          </span>
        </div>
      )}

      {/* Phase B — instant client-side facet filters over the loaded pool. */}
      {hasFacetBar && (
        <div className="bg-elevated border border-hairline rounded-xl p-500 mb-500 flex flex-col gap-300">
          {facetGroup('City', cityFacets, cityFilter, setCityFilter)}
          {facetGroup('Type', categoryFacets, categoryFilter, setCategoryFilter)}
          {facetGroup('Kid', kidFacets, kidFilter, setKidFilter)}
          {activeFilterCount > 0 && (
            <button
              onClick={clearFilters}
              className="self-start flex items-center gap-100 text-sm text-ink-muted hover:text-ink-secondary"
            >
              <X size={14} /> Clear {activeFilterCount} filter{activeFilterCount > 1 ? 's' : ''}
            </button>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-500">
        {filtered.map((c) => (
          <div key={c.id} className="bg-elevated border border-hairline rounded-xl p-600">
            <div className="flex items-start justify-between gap-400">
              <h2 className="font-medium text-ink-primary">{c.name}</h2>
              {c.fit_score != null && (
                <span className="text-accent font-mono text-sm">
                  {Math.round(c.fit_score * 100)}%
                </span>
              )}
            </div>
            <div className="text-ink-secondary text-sm mt-200">
              {[c.provider, c.location_text].filter(Boolean).join(' · ')}
            </div>
            <div className="flex flex-wrap gap-200 mt-400 text-sm text-ink-secondary">
              {(c.fit_kids && c.fit_kids.length > 0
                ? c.fit_kids
                : c.kid_name
                  ? [c.kid_name]
                  : []
              ).map((k) => (
                <span key={k} className="bg-accent-tint rounded px-300 py-100">
                  {k}
                </span>
              ))}
              {c.category && <span className="bg-canvas rounded px-300 py-100">{c.category}</span>}
              {(c.price_text ?? (c.price_amount != null ? `$${c.price_amount}` : null)) && (
                <span className="bg-canvas rounded px-300 py-100">
                  {c.price_text ?? `$${c.price_amount}`}
                </span>
              )}
            </div>
            <div className="text-ink-muted text-sm mt-300">
              {[c.start_date, c.end_date].filter(Boolean).join(' – ') || c.schedule_text}
            </div>
            <div className="flex items-center justify-between mt-400">
              {c.signup_url ? (
                <a
                  href={c.signup_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-accent text-sm"
                >
                  Open signup ↗
                </a>
              ) : (
                <span />
              )}
              <button
                onClick={() => toggleSave(c)}
                disabled={savingIds.has(c.id)}
                className="flex items-center gap-200 text-sm rounded-lg px-300 py-200 border border-hairline hover:border-accent group"
                aria-label={savedIds.has(c.id) ? 'Saved — click to remove' : 'Save to shortlist'}
              >
                {savingIds.has(c.id) ? (
                  <Loader2 className="animate-spin" size={15} />
                ) : savedIds.has(c.id) ? (
                  <BookmarkCheck className="text-accent" size={15} />
                ) : (
                  <Bookmark size={15} />
                )}
                <span className={savedIds.has(c.id) ? 'text-accent' : 'text-ink-secondary'}>
                  {savedIds.has(c.id) ? 'Exploring' : 'Save'}
                </span>
              </button>
            </div>
          </div>
        ))}
      </div>

      {candidates.length > 0 && filtered.length === 0 && (
        <p className="text-ink-muted">
          No matches for these filters.{' '}
          <button onClick={clearFilters} className="text-accent">
            Clear filters
          </button>
        </p>
      )}

      {!busy && candidates.length === 0 && !err && (
        <p className="text-ink-muted">
          Click “Find activities” to research camps and classes near you.
        </p>
      )}
    </div>
  );
}
