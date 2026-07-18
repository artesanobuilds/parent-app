import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  getLegalOverview,
  getLegalVersions,
  putLegalDraft,
  deleteLegalDraft,
  publishLegal,
  type LegalDoc,
} from '../api';
import { toast } from '../components/shared/Toast';

// Legal editor: a plain monospace textarea, deliberately NOT TipTap —
// tiptap-markdown round-trips can silently reflow nested clause lists, and
// byte fidelity beats WYSIWYG for legal text (which arrives as exact markdown
// from the Google Docs review round). Saving writes THE draft row (last write
// wins); Publish… promotes it to the current version.
export function LegalEditor() {
  const { slug } = useParams<{ slug: string }>();
  const [current, setCurrent] = useState<LegalDoc | null>(null);
  const [versions, setVersions] = useState<LegalDoc[]>([]);
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [hasDraft, setHasDraft] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [showPublish, setShowPublish] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [pubVersion, setPubVersion] = useState('');
  const [pubEffective, setPubEffective] = useState('');
  const [pubReaccept, setPubReaccept] = useState(false);
  const [publishing, setPublishing] = useState(false);

  const load = useMemo(
    () => async () => {
      if (!slug) return;
      setLoading(true);
      try {
        const overview = await getLegalOverview();
        const entry = overview.find((d) => d.slug === slug);
        const base = entry?.draft ?? entry?.current ?? null;
        setCurrent(entry?.current ?? null);
        setHasDraft(!!entry?.draft);
        setTitle(base?.title ?? slug);
        setBody(base?.body_md ?? '');
        setDirty(false);
        setVersions(await getLegalVersions(slug));
      } catch {
        toast.error('Failed to load document');
      } finally {
        setLoading(false);
      }
    },
    [slug],
  );

  useEffect(() => {
    load();
  }, [load]);

  if (!slug) return null;

  const saveDraft = async () => {
    setSaving(true);
    try {
      await putLegalDraft(slug, title, body);
      setHasDraft(true);
      setDirty(false);
      toast.success('Draft saved');
    } catch {
      toast.error('Failed to save draft');
    } finally {
      setSaving(false);
    }
  };

  const discardDraft = async () => {
    try {
      await deleteLegalDraft(slug);
      toast.success('Draft discarded');
      await load();
    } catch {
      toast.error('Failed to discard draft');
    }
  };

  const openPublish = () => {
    setPubVersion(suggestNextVersion(current?.version));
    setPubEffective(new Date().toISOString().slice(0, 10));
    setPubReaccept(false);
    setShowPublish(true);
  };

  const doPublish = async () => {
    setPublishing(true);
    try {
      // Publish promotes the saved draft — make sure the latest text is in it.
      if (dirty || !hasDraft) await putLegalDraft(slug, title, body);
      await publishLegal(slug, {
        version: pubVersion.trim(),
        effective_date: pubEffective || undefined,
        requires_reacceptance: pubReaccept,
      });
      toast.success(`Published v${pubVersion.trim()}`);
      setShowPublish(false);
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Publish failed');
    } finally {
      setPublishing(false);
    }
  };

  return (
    <div className="p-800 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-600">
        <div>
          <Link to="/legal" className="text-body-sm text-ink-muted hover:text-ink-primary">
            ← Legal
          </Link>
          <h1 className="font-display text-display-sm text-ink-primary mt-200">
            {title || slug}
          </h1>
          <div className="text-body-sm text-ink-muted mt-100">
            {current ? `Current: v${current.version}` : 'Not yet published'}
            {hasDraft ? ' · editing draft' : ''}
            {dirty ? ' · unsaved changes' : ''}
          </div>
        </div>
        <div className="flex gap-300">
          <button
            onClick={() => setShowHistory((v) => !v)}
            className="rounded-md border border-hairline px-500 py-300 text-title-md text-ink-primary hover:bg-canvas transition-colors duration-fast"
          >
            History ({versions.length})
          </button>
          <button
            onClick={() => setShowPreview((v) => !v)}
            className="rounded-md border border-hairline px-500 py-300 text-title-md text-ink-primary hover:bg-canvas transition-colors duration-fast"
          >
            {showPreview ? 'Edit' : 'Preview'}
          </button>
          <button
            onClick={saveDraft}
            disabled={saving || loading}
            className="rounded-md border border-hairline px-500 py-300 text-title-md text-ink-primary hover:bg-canvas transition-colors duration-fast disabled:opacity-50"
          >
            {saving ? 'Saving…' : 'Save draft'}
          </button>
          <button
            onClick={openPublish}
            disabled={loading}
            className="rounded-md bg-accent px-500 py-300 text-title-md font-medium text-ink-on-photo-light hover:bg-accent-press transition-colors duration-fast disabled:opacity-50"
          >
            Publish…
          </button>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-1000 text-ink-muted text-body-sm">Loading...</div>
      ) : showHistory ? (
        <div className="rounded-lg border border-hairline bg-elevated divide-y divide-hairline">
          {versions.map((v) => (
            <details key={v.id} className="px-500 py-400">
              <summary className="cursor-pointer text-ink-primary font-medium">
                v{v.version}
                {v.is_current ? ' (current)' : ''}
                <span className="text-ink-muted font-normal">
                  {' '}
                  · published {v.published_at?.slice(0, 10) ?? '—'} by {v.published_by}
                  {v.requires_reacceptance ? ' · required re-acceptance' : ''}
                </span>
              </summary>
              <pre className="mt-300 whitespace-pre-wrap text-body-sm text-ink-muted font-mono">
                {v.body_md}
              </pre>
            </details>
          ))}
        </div>
      ) : showPreview ? (
        <article className="rounded-lg border border-hairline bg-elevated px-700 py-600 prose-docs">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{body}</ReactMarkdown>
        </article>
      ) : (
        <div className="flex flex-col gap-400">
          <input
            value={title}
            onChange={(e) => {
              setTitle(e.target.value);
              setDirty(true);
            }}
            placeholder="Title"
            className="rounded-md border border-hairline bg-elevated px-400 py-300 text-title-md text-ink-primary"
          />
          <textarea
            value={body}
            onChange={(e) => {
              setBody(e.target.value);
              setDirty(true);
            }}
            spellCheck={false}
            rows={28}
            className="rounded-md border border-hairline bg-elevated px-400 py-300 font-mono text-body-sm text-ink-primary leading-relaxed"
          />
          {hasDraft ? (
            <button
              onClick={discardDraft}
              className="self-start text-body-sm text-ink-muted underline hover:text-ink-primary"
            >
              Discard draft (revert to published)
            </button>
          ) : null}
        </div>
      )}

      {showPublish ? (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="rounded-lg bg-elevated border border-hairline p-700 w-full max-w-md">
            <h2 className="font-display text-title-lg text-ink-primary mb-400">
              Publish {title}
            </h2>
            <label className="block text-label text-ink-muted uppercase tracking-wider mb-100">
              Version
            </label>
            <input
              value={pubVersion}
              onChange={(e) => setPubVersion(e.target.value)}
              className="w-full rounded-md border border-hairline bg-canvas px-400 py-300 text-body-md text-ink-primary mb-400"
            />
            <label className="block text-label text-ink-muted uppercase tracking-wider mb-100">
              Effective date
            </label>
            <input
              type="date"
              value={pubEffective}
              onChange={(e) => setPubEffective(e.target.value)}
              className="w-full rounded-md border border-hairline bg-canvas px-400 py-300 text-body-md text-ink-primary mb-400"
            />
            <label className="flex items-start gap-300 mb-500 cursor-pointer">
              <input
                type="checkbox"
                checked={pubReaccept}
                onChange={(e) => setPubReaccept(e.target.checked)}
                className="mt-100"
              />
              <span className="text-body-sm text-ink-primary">
                Requires re-acceptance
                <span className="block text-ink-muted">
                  Every existing user will see a re-accept prompt in the app until
                  they agree to this version. Leave unchecked for typo-level fixes.
                </span>
              </span>
            </label>
            <div className="flex justify-end gap-300">
              <button
                onClick={() => setShowPublish(false)}
                disabled={publishing}
                className="rounded-md border border-hairline px-500 py-300 text-title-md text-ink-primary hover:bg-canvas transition-colors duration-fast"
              >
                Cancel
              </button>
              <button
                onClick={doPublish}
                disabled={publishing || !pubVersion.trim()}
                className="rounded-md bg-accent px-500 py-300 text-title-md font-medium text-ink-on-photo-light hover:bg-accent-press transition-colors duration-fast disabled:opacity-50"
              >
                {publishing ? 'Publishing…' : `Publish v${pubVersion.trim() || '?'}`}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function suggestNextVersion(current?: string): string {
  if (!current) return '1.0';
  const parts = current.split('.');
  const minor = Number(parts[parts.length - 1]);
  if (Number.isFinite(minor)) {
    return [...parts.slice(0, -1), String(minor + 1)].join('.');
  }
  return current;
}
