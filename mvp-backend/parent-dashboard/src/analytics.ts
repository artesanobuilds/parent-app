// PostHog for the parent dashboard. Privacy posture matches the backend
// (app/analytics): autocapture + session replay OFF (this surface shows kid /
// family data — never sweep the DOM), explicit allowlisted events only, and
// identify on the OPAQUE analytics_id, never the user_id/name.
//
// No-op unless VITE_POSTHOG_KEY is set at build time.
import posthog from 'posthog-js';

const KEY = import.meta.env.VITE_POSTHOG_KEY as string | undefined;
const HOST = (import.meta.env.VITE_POSTHOG_HOST as string) || 'https://us.i.posthog.com';

let enabled = false;

// event name → allowed property keys (dashboard-relevant subset of the backend
// taxonomy). Anything not listed is dropped.
const EVENTS: Record<string, readonly string[]> = {
  dashboard_page_viewed: ['page'],
  activity_tracked: ['status'],
  plan_exported: ['format'],
  research_run_started: [],
  // Vertical doors — tap distribution informs which vertical ships next.
  door_opened: ['door'],
  door_converted: ['door'],
};

// Keys that must never be sent, whatever a call site passes.
const DENYLIST = new Set([
  'message', 'content', 'text', 'transcript', 'name', 'kid_name', 'child_name',
  'parent_name', 'email', 'pin', 'token', 'address', 'custody',
]);

export function initAnalytics(): void {
  if (!KEY) return;
  posthog.init(KEY, {
    api_host: HOST,
    autocapture: false,             // never — kid/family data on screen
    capture_pageview: false,        // we send explicit, path-only pageviews
    capture_pageleave: false,
    disable_session_recording: true,
    person_profiles: 'identified_only', // no anonymous profiles
  });
  enabled = true;
}

function sanitize(event: string, props?: Record<string, unknown>): Record<string, unknown> {
  const allowed = EVENTS[event] ?? [];
  const out: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(props ?? {})) {
    if (allowed.includes(k) && !DENYLIST.has(k)) out[k] = v;
  }
  return out;
}

export function capture(event: string, props?: Record<string, unknown>): void {
  if (!enabled || !(event in EVENTS)) return;
  posthog.capture(event, sanitize(event, props));
}

/** Identify the session on the OPAQUE analytics id (never the user_id). */
export function identify(analyticsId: string | null | undefined): void {
  if (!enabled || !analyticsId) return;
  posthog.identify(analyticsId);
}

export function resetAnalytics(): void {
  if (!enabled) return;
  posthog.reset();
}

/** Explicit pageview — the route NAME only (dashboard paths carry no PII). */
export function pageview(path: string): void {
  if (!enabled) return;
  posthog.capture('dashboard_page_viewed', { page: path });
}
