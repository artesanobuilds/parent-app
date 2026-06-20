import { useEffect, useRef, useState } from 'react';
import { Loader2 } from 'lucide-react';
import { createResearchRun, getCandidates, getProfile, getResearchRun } from '../api';
import type { Candidate, ResearchProgress } from '../types';

export default function Discovery() {
  const [progress, setProgress] = useState<ResearchProgress | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [zip, setZip] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const pollRef = useRef<number | undefined>(undefined);

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
            {c.signup_url && (
              <a
                href={c.signup_url}
                target="_blank"
                rel="noreferrer"
                className="text-accent text-sm mt-400 inline-block"
              >
                Open signup ↗
              </a>
            )}
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
