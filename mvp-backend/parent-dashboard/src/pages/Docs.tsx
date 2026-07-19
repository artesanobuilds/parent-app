import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { DOCS, SECTIONS, getDoc } from '../lib/docs';
import { LEGAL_PAGES, isLegalSlug, fetchLegalDoc, type LegalDocPayload } from '../lib/legalDocs';

// PUBLIC product docs — this page (and its /docs routes) lives OUTSIDE the
// auth guard on purpose: it's the GTM funnel's "read the docs" landing.
// Locked by tests/test_public_docs.py (guard exclusion + registry coverage).
// Product pages render from markdown bundled at build time; the two LEGAL
// pages (privacy-policy, terms) are the exception — they fetch the current
// CMS-published version from /content/legal/{slug} so a publish is live here
// with no deploy (see lib/legalDocs.ts).

function DocsHeader() {
  return (
    <header className="flex items-baseline justify-between border-b border-strong pb-400 mb-600">
      <Link to="/docs" className="text-ink-primary font-semibold text-lg">
        MVP <span className="text-ink-muted font-normal">· How it works</span>
      </Link>
      <Link to="/login" className="text-accent text-sm underline">
        Open the app
      </Link>
    </header>
  );
}

function DocsNav({ current }: { current?: string }) {
  // On phones the nav renders BELOW the article (order-2): a parent following
  // the app's "Terms of Service" link must land on the document, not scroll
  // past the whole docs index first. Desktop keeps the left sidebar.
  return (
    <nav className="order-2 md:order-1 mt-700 pt-500 border-t border-subtle md:mt-0 md:pt-0 md:border-0 flex flex-col gap-500 shrink-0 md:w-56">
      <div className="text-ink-muted text-xs uppercase tracking-wide md:hidden">
        More from the docs
      </div>
      {SECTIONS.map((s) => (
        <div key={s.name}>
          <div className="text-ink-muted text-xs uppercase tracking-wide mb-200">{s.name}</div>
          <div className="flex flex-col gap-100">
            {s.pages.map((p) => (
              <Link
                key={p.slug}
                to={`/docs/${p.slug}`}
                className={
                  p.slug === current
                    ? 'text-ink-primary font-medium text-sm'
                    : 'text-ink-secondary text-sm hover:text-ink-primary'
                }
              >
                {p.title}
              </Link>
            ))}
          </div>
        </div>
      ))}
      <div>
        <div className="text-ink-muted text-xs uppercase tracking-wide mb-200">Legal</div>
        <div className="flex flex-col gap-100">
          {LEGAL_PAGES.map((p) => (
            <Link
              key={p.slug}
              to={`/docs/${p.slug}`}
              className={
                p.slug === current
                  ? 'text-ink-primary font-medium text-sm'
                  : 'text-ink-secondary text-sm hover:text-ink-primary'
              }
            >
              {p.title}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
}

// The two legal slugs render the CMS-published current version from the API.
function LegalDoc({ slug }: { slug: string }) {
  const [doc, setDoc] = useState<LegalDocPayload | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setDoc(null);
    setError(false);
    fetchLegalDoc(slug)
      .then((d) => { if (!cancelled) setDoc(d); })
      .catch(() => { if (!cancelled) setError(true); });
    return () => { cancelled = true; };
  }, [slug]);

  if (error) {
    return (
      <div className="text-ink-secondary">
        We couldn&apos;t load this page right now — please try again in a moment.
      </div>
    );
  }
  if (!doc) {
    return <div className="text-ink-muted">Loading…</div>;
  }
  return (
    <>
      <h1 className="text-2xl font-semibold text-ink-primary mb-400">{doc.title}</h1>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={mdComponents}>
        {doc.body_md}
      </ReactMarkdown>
      <div className="text-ink-muted text-xs mt-700 border-t border-subtle pt-300">
        Version {doc.version}
        {doc.effective_date ? ` · effective ${doc.effective_date}` : null}
      </div>
    </>
  );
}

// Markdown element styling (no typography plugin — explicit map, shared by
// every docs page so the look never drifts per-page).
const mdComponents = {
  h1: (p: object) => <h1 className="text-2xl font-semibold text-ink-primary mb-400" {...p} />,
  h2: (p: object) => <h2 className="text-lg font-semibold text-ink-primary mt-600 mb-300" {...p} />,
  h3: (p: object) => <h3 className="font-semibold text-ink-primary mt-500 mb-200" {...p} />,
  p: (p: object) => <p className="text-ink-secondary leading-relaxed mb-300" {...p} />,
  ul: (p: object) => <ul className="list-disc pl-500 mb-300 text-ink-secondary space-y-100" {...p} />,
  ol: (p: object) => <ol className="list-decimal pl-500 mb-300 text-ink-secondary space-y-100" {...p} />,
  a: (p: object) => <a className="text-accent underline" {...p} />,
  blockquote: (p: object) => (
    <blockquote className="border-l-2 border-strong pl-400 text-ink-muted italic mb-300" {...p} />
  ),
  table: (p: object) => (
    <div className="overflow-x-auto mb-300">
      <table className="text-sm text-ink-secondary border-collapse w-full" {...p} />
    </div>
  ),
  th: (p: object) => (
    <th className="text-left font-semibold text-ink-primary border-b border-strong px-300 py-200" {...p} />
  ),
  td: (p: object) => <td className="border-b border-subtle px-300 py-200 align-top" {...p} />,
  code: (p: object) => <code className="bg-canvas rounded px-100 text-sm" {...p} />,
  // Screenshots/diagrams render as captioned figures: the alt text IS the
  // caption. Portrait phone shots (ios-*) get a narrower column so they read
  // like a phone, not a poster. Spans (block-styled), not <figure> — markdown
  // images arrive inside <p>, where a figure would be invalid nesting.
  img: ({ src, alt }: { src?: string; alt?: string }) => (
    <span className={`block my-500 ${src?.includes('/ios-') ? 'max-w-[340px]' : ''}`}>
      <img
        src={src}
        alt={alt ?? ''}
        loading="lazy"
        className="w-full rounded-lg border border-hairline shadow-sm"
      />
      {alt ? (
        <span className="block text-ink-muted text-xs mt-200 text-center">{alt}</span>
      ) : null}
    </span>
  ),
};

export default function Docs() {
  const { slug } = useParams();
  const doc = getDoc(slug);

  return (
    <div className="min-h-screen bg-surface">
      <div className="max-w-4xl mx-auto px-500 py-600">
        <DocsHeader />
        {isLegalSlug(slug) ? (
          <div className="flex flex-col md:flex-row gap-700">
            <DocsNav current={slug} />
            <article className="order-1 md:order-2 min-w-0 flex-1">
              <LegalDoc slug={slug!} />
            </article>
          </div>
        ) : slug && !doc ? (
          <div className="text-ink-secondary">
            That page doesn&apos;t exist. <Link to="/docs" className="text-accent underline">Back to the docs.</Link>
          </div>
        ) : doc ? (
          <div className="flex flex-col md:flex-row gap-700">
            <DocsNav current={doc.slug} />
            <article className="order-1 md:order-2 min-w-0 flex-1">
              <ReactMarkdown remarkPlugins={[remarkGfm]} components={mdComponents}>
                {doc.body}
              </ReactMarkdown>
            </article>
          </div>
        ) : (
          <div>
            <h1 className="text-2xl font-semibold text-ink-primary mb-200">How MVP works</h1>
            <p className="text-ink-secondary mb-600 max-w-prose">
              The product, explained the way it behaves — from first sign-in to a fully
              handled camp season.
            </p>
            <div className="flex flex-col gap-600 md:flex-row md:flex-wrap">
              {SECTIONS.map((s) => (
                <div key={s.name} className="md:w-64">
                  <div className="text-ink-muted text-xs uppercase tracking-wide mb-300">{s.name}</div>
                  <div className="flex flex-col gap-300">
                    {s.pages.map((p) => (
                      <Link
                        key={p.slug}
                        to={`/docs/${p.slug}`}
                        className="text-ink-primary hover:text-accent font-medium"
                      >
                        {p.title}
                      </Link>
                    ))}
                  </div>
                </div>
              ))}
              <div className="md:w-64">
                <div className="text-ink-muted text-xs uppercase tracking-wide mb-300">Legal</div>
                <div className="flex flex-col gap-300">
                  {LEGAL_PAGES.map((p) => (
                    <Link
                      key={p.slug}
                      to={`/docs/${p.slug}`}
                      className="text-ink-primary hover:text-accent font-medium"
                    >
                      {p.title}
                    </Link>
                  ))}
                </div>
              </div>
            </div>
            <div className="text-ink-muted text-xs mt-700">
              {DOCS.length} pages · updated with every release
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
