// Legal pages (privacy policy, terms) are the ONE exception to the
// bundled-markdown docs pipeline: their text is CMS-published, versioned, and
// served by the backend at /content/legal/{slug} — so an edit + publish in the
// CMS is live here with no deploy, and the page can show the exact version a
// user accepted. Everything else under /docs stays build-time markdown.
// Do NOT add privacy-policy.md / terms.md under parent-dashboard/docs/ — a
// bundled copy would silently shadow the published one (guarded by
// tests/test_public_docs.py).

export interface LegalPageMeta {
  slug: string;
  title: string;
}

export interface LegalDocPayload {
  slug: string;
  title: string;
  version: string;
  effective_date: string | null;
  body_md: string;
}

// Static metadata so the sidebar renders without a fetch.
export const LEGAL_PAGES: LegalPageMeta[] = [
  { slug: 'privacy-policy', title: 'Privacy Policy' },
  { slug: 'terms', title: 'Terms of Service' },
];

export function isLegalSlug(slug?: string): boolean {
  return !!slug && LEGAL_PAGES.some((p) => p.slug === slug);
}

export async function fetchLegalDoc(slug: string): Promise<LegalDocPayload> {
  const res = await fetch(`/content/legal/${slug}`);
  if (!res.ok) throw new Error(`legal doc ${slug}: HTTP ${res.status}`);
  return res.json();
}
