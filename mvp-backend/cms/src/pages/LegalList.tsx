import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getLegalOverview, type LegalOverviewEntry } from '../api';
import { toast } from '../components/shared/Toast';

// Legal documents are versioned: the editor works on a private draft, and an
// explicit Publish step (with an optional "requires re-acceptance" flag that
// re-prompts every app user) makes it live. Prior versions are immutable —
// this list links into the editor, which shows the history.
export function LegalList() {
  const [docs, setDocs] = useState<LegalOverviewEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getLegalOverview()
      .then(setDocs)
      .catch(() => toast.error('Failed to load legal documents'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-800 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-700">
        <h1 className="font-display text-display-sm text-ink-primary">Legal</h1>
      </div>
      <p className="text-body-sm text-ink-muted mb-600 max-w-prose">
        These pages are what families agree to. Edits are drafts until you publish
        a new version — and publishing with “requires re-acceptance” will prompt
        every user in the app.
      </p>

      {loading ? (
        <div className="text-center py-1000 text-ink-muted text-body-sm">Loading...</div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-hairline bg-elevated">
          <table className="w-full text-body-md">
            <thead>
              <tr className="border-b border-hairline bg-canvas text-left text-label font-semibold uppercase tracking-wider text-ink-muted">
                <th className="px-500 py-400">Document</th>
                <th className="px-500 py-400">Current version</th>
                <th className="px-500 py-400">Effective</th>
                <th className="px-500 py-400">Versions</th>
                <th className="px-500 py-400">Draft</th>
                <th className="px-500 py-400 w-20">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-hairline">
              {docs.map((d) => (
                <tr key={d.slug} className="hover:bg-canvas transition-colors duration-fast">
                  <td className="px-500 py-400 font-medium text-ink-primary">
                    {d.current?.title ?? d.slug}
                  </td>
                  <td className="px-500 py-400 text-ink-muted">
                    {d.current ? `v${d.current.version}` : '— not published —'}
                  </td>
                  <td className="px-500 py-400 text-ink-muted">
                    {d.current?.effective_date ?? '—'}
                  </td>
                  <td className="px-500 py-400 text-ink-muted">{d.version_count}</td>
                  <td className="px-500 py-400">
                    {d.draft ? (
                      <span className="rounded-full bg-canvas border border-hairline px-300 py-100 text-label text-ink-muted">
                        draft in progress
                      </span>
                    ) : (
                      <span className="text-ink-muted">—</span>
                    )}
                  </td>
                  <td className="px-500 py-400">
                    <Link
                      to={`/legal/${d.slug}`}
                      className="text-accent hover:text-accent-press font-medium transition-colors duration-fast"
                    >
                      Edit
                    </Link>
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
