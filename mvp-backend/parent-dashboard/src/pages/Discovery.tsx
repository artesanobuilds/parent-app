import { useEffect, useRef, useState } from 'react';
import { Bookmark, BookmarkCheck, Loader2 } from 'lucide-react';
import {
  createResearchRun,
  getActivities,
  getCandidates,
  getProfile,
  getResearchRun,
  trackActivity,
} from '../api';
import type { Candidate, ResearchProgress, TrackedActivity } from '../types';

export default function Discovery() {
  const [progress, setProgress] = useState<ResearchProgress | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [zip, setZip] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const pollRef = useRef<number | undefined>(undefined);

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

  useEffect(
    () => () => {
      if (pollRef.current) window.clearInterval(pollRef.current);
    },
    [],
  );

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

  async function run() {
    setBusy(true);
    setErr(null);
    setCandidates([]);
    setProgress(null);
    try {
      const trimmedZip = zip.trim();
      const { run_id } = await createResearchRun(
        { season: 'summer 2026' },
        trimmedZip ? { postal_code: trimmedZip, country: 'US' } : undefined,
      );
      pollRef.current = window.setInterval(async () => {
        try {
          const s = await getResearchRun(run_id);
          setProgress(s.progress ?? null);
          if (s.status === 'done') {
            window.clearInterval(pollRef.current);
            setCandidates(await getCandidates(run_id));
            setBusy(false);
          } else if (s.status === 'failed' || s.status === 'error') {
            window.clearInterval(pollRef.current);
            setErr(s.error ?? 'The discovery run failed.');
            setBusy(false);
          }
        } catch (e) {
          window.clearInterval(pollRef.current);
          setErr(e instanceof Error ? e.message : 'Polling failed');
          setBusy(false);
        }
      }, 2000);
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Could not start a run');
      setBusy(false);
    }
  }

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
          <button
            onClick={run}
            disabled={busy}
            className="bg-accent text-ink-on-photo-light rounded-lg px-500 py-300 font-medium disabled:opacity-60"
          >
            {busy ? 'Searching…' : 'Find activities'}
          </button>
        </div>
      </div>

      {busy && (
        <div className="bg-elevated border border-hairline rounded-xl p-600 mb-600">
          <div className="flex items-center gap-300">
            <Loader2 className="animate-spin text-accent" size={18} />
            <span className="font-medium text-ink-primary">
              {progress?.detail ?? 'Researching activities near you…'}
            </span>
          </div>
          {typeof progress?.candidates_found === 'number' && (
            <div className="text-accent text-sm mt-200">
              {progress.candidates_found}
              {progress.candidates_target ? ` of ${progress.candidates_target}` : ''} found
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
                {a.price_amount != null && (
                  <span className="font-mono text-sm text-ink-secondary shrink-0">
                    ${Math.round(a.price_amount)}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-500">
        {candidates.map((c) => (
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
                onClick={() => saveCandidate(c)}
                disabled={savedIds.has(c.id) || savingIds.has(c.id)}
                className="flex items-center gap-200 text-sm rounded-lg px-300 py-200 border border-hairline disabled:opacity-100 hover:border-accent"
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

      {!busy && candidates.length === 0 && !err && (
        <p className="text-ink-muted">
          Click “Find activities” to research camps and classes near you.
        </p>
      )}
    </div>
  );
}
