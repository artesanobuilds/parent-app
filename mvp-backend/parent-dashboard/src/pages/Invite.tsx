import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

// PUBLIC invite landing — deliberately OUTSIDE ProtectedRoute, like /docs.
// The whole point is that the person opening it has NO account: a nanny, a
// grandparent, a co-parent. Bouncing them to /login would strand them.
//
// This is the page `CIRCLE_INVITE_BASE_URL` points at (app/circle.py). Until it
// existed, a minted invite link 404'd — or worse, hit the SPA catch-all and
// silently redirected to the plan board, which reads as "the link is broken".
//
// It reads the preview (GET /circle/invites/{token}) and stops there. Claiming
// requires an authenticated account, so this page's job is to tell the invitee
// what they've been invited to and send them to the app to accept — it never
// claims on their behalf.

interface InvitePreview {
  inviter_name: string;
  household_label: string;
  kids_label: string;
  expired: boolean;
  claimed: boolean;
}

type State =
  | { kind: 'loading' }
  | { kind: 'ready'; preview: InvitePreview }
  | { kind: 'missing' }
  | { kind: 'error'; message: string };

const APP_STORE_URL = 'https://testflight.apple.com/';

export default function Invite() {
  const { token } = useParams<{ token: string }>();
  const [state, setState] = useState<State>({ kind: 'loading' });

  useEffect(() => {
    if (!token) {
      setState({ kind: 'missing' });
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`/circle/invites/${encodeURIComponent(token)}`);
        if (res.status === 404) {
          if (!cancelled) setState({ kind: 'missing' });
          return;
        }
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const preview: InvitePreview = await res.json();
        if (!cancelled) setState({ kind: 'ready', preview });
      } catch (err) {
        if (!cancelled) {
          setState({ kind: 'error', message: err instanceof Error ? err.message : 'unknown' });
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token]);

  return (
    <div className="min-h-screen bg-canvas px-500 py-800 flex justify-center">
      <div className="w-full max-w-md">
        <header className="mb-700">
          <span className="text-ink-primary font-semibold text-lg">MVP</span>
        </header>
        <Body state={state} />
        <footer className="mt-800 text-ink-muted text-xs">
          <Link to="/docs/circle" className="underline">
            What is a Circle?
          </Link>
        </footer>
      </div>
    </div>
  );
}

function Shell({ title, children }: { title: string; children?: React.ReactNode }) {
  return (
    <div>
      <h1 className="text-ink-primary text-2xl font-semibold mb-300">{title}</h1>
      <div className="text-ink-secondary">{children}</div>
    </div>
  );
}

function Body({ state }: { state: State }) {
  if (state.kind === 'loading') {
    return <Shell title="Opening your invite…" />;
  }

  // A bad token and a deleted invite are the same thing to the visitor, and we
  // deliberately don't distinguish them — "does this token exist" is not
  // information an unauthenticated stranger should be able to probe.
  if (state.kind === 'missing') {
    return (
      <Shell title="This invite isn't valid">
        <p>
          The link may have expired, or it may have already been used. Ask whoever
          invited you to send a new one.
        </p>
      </Shell>
    );
  }

  if (state.kind === 'error') {
    return (
      <Shell title="Something went wrong">
        <p>
          We couldn't load this invite just now. Try again in a moment — the link
          itself is probably fine.
        </p>
      </Shell>
    );
  }

  const { preview } = state;

  if (preview.expired) {
    return (
      <Shell title="This invite has expired">
        <p>
          Invites are good for two weeks. Ask {preview.inviter_name} to send you a
          fresh one.
        </p>
      </Shell>
    );
  }

  if (preview.claimed) {
    return (
      <Shell title="This invite was already used">
        <p>
          If that was you, open MVP and you'll find {preview.inviter_name}'s Circle
          waiting. If it wasn't, ask them for a new link.
        </p>
      </Shell>
    );
  }

  const kids = preview.kids_label?.trim();

  return (
    <Shell title={`${preview.inviter_name} invited you to their Circle`}>
      <p className="mb-400">
        A Circle is the small group of people who help with a family day to day —
        a co-parent, a grandparent, a sitter, a close friend.
        {kids ? ` You'd be joining ${preview.household_label} to help with ${kids}.` : ''}
      </p>
      <p className="mb-600">
        You'll be able to see and reply to the conversations {preview.inviter_name}
        {' '}includes you in. You won't see anything else about their family, and
        you can leave at any time.
      </p>
      {/* `text-ink-on-photo-light` (white), not a `text-on-accent` — that token
          does not exist in index.css and would render as unstyled inherited ink
          on the olive fill. */}
      <a
        href={APP_STORE_URL}
        className="inline-block bg-accent text-ink-on-photo-light rounded-md px-500 py-300 font-semibold"
      >
        Get MVP to accept
      </a>
      <p className="mt-400 text-ink-muted text-sm">
        Already have MVP? Open the app and sign in — the invite is waiting on your
        Circle tab.
      </p>
    </Shell>
  );
}
