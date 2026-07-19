// Public product docs, bundled at build time (the plan's Phase 7 rule: docs
// ship with every deploy by construction — no CMS, no fetch). Each markdown
// file under ../../docs carries frontmatter: title, section, order, draft.
// `draft: true` pages are excluded from the public site so a flag-gated
// vertical's page isn't public weeks early.

export interface DocPage {
  slug: string;
  title: string;
  section: string;
  order: number;
  draft: boolean;
  body: string;
}

const raw = import.meta.glob('../../docs/*.md', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>;

// ~20-line frontmatter parser (the plan's "no Docusaurus" budget): a leading
// `---` block of `key: value` lines, everything after is the body.
function parse(slug: string, text: string): DocPage {
  const meta: Record<string, string> = {};
  let body = text;
  if (text.startsWith('---')) {
    const end = text.indexOf('\n---', 3);
    if (end !== -1) {
      for (const line of text.slice(3, end).split('\n')) {
        const i = line.indexOf(':');
        if (i > 0) meta[line.slice(0, i).trim()] = line.slice(i + 1).trim();
      }
      body = text.slice(end + 4).replace(/^\s*\n/, '');
    }
  }
  return {
    slug,
    title: meta.title ?? slug,
    section: meta.section ?? 'Docs',
    order: Number(meta.order ?? 999),
    draft: (meta.draft ?? 'false').toLowerCase() === 'true',
    body,
  };
}

export const DOCS: DocPage[] = Object.entries(raw)
  .map(([path, text]) => parse(path.split('/').pop()!.replace(/\.md$/, ''), text))
  .filter((d) => !d.draft)
  .sort((a, b) => a.order - b.order || a.title.localeCompare(b.title));

// Section display order (sections not listed sort last, alphabetically).
const SECTION_ORDER = [
  'Getting started',
  "What's new",
  'Your plan',
  'Activities',
  'Coach & companions',
  'Connections',
  'Trust',
];

export const SECTIONS: { name: string; pages: DocPage[] }[] = [
  ...new Set(DOCS.map((d) => d.section)),
]
  .sort((a, b) => {
    const ia = SECTION_ORDER.indexOf(a);
    const ib = SECTION_ORDER.indexOf(b);
    return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib) || a.localeCompare(b);
  })
  .map((name) => ({ name, pages: DOCS.filter((d) => d.section === name) }));

export function getDoc(slug: string | undefined): DocPage | undefined {
  return DOCS.find((d) => d.slug === slug);
}
