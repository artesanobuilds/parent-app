// Types mirror the backend response shapes. Confirmed against:
//   app/research/router.py, app/duckdb_storage.py (list_candidates / list_research_runs),
//   app/cos/router.py, app/cos/planning.py (build_plan_summary).

// ── Auth ──────────────────────────────────────────────────────────────
export interface AuthTokenResponse {
  token: string;
  user_id: string;
}

export interface FamilyProfile {
  parent?: { name?: string; postal_code?: string | null; country?: string | null };
  children?: Record<string, { name?: string; age?: number | null }>;
}

// ── Discovery / research ──────────────────────────────────────────────
export interface ResearchRun {
  id: string;
  user_id: string;
  status: string; // queued | running | done | error | canceled
  location: Record<string, unknown>;
  kids: unknown[];
  params: Record<string, unknown>;
  progress: ResearchProgress;
  candidate_count: number;
  error: string | null;
  created_at: string | null;
  started_at: string | null;
  finished_at: string | null;
}

export interface ResearchProgress {
  phase?: string;
  message?: string;
  detail?: string;             // human-friendly current action ("Searching: …")
  candidates_found?: number;   // running count
  candidates_target?: number;  // how many we're aiming for
  recent?: string[];           // last few actions, oldest→newest
  [k: string]: unknown;
}

export interface ResearchRunStatus {
  run_id: string;
  status: string;
  progress: ResearchProgress;
  candidate_count: number;
  error: string | null;
}

export interface Candidate {
  id: string;
  run_id: string;
  user_id: string;
  kid_name: string | null;
  name: string;
  provider: string | null;
  category: string | null;
  age_min: number | null;
  age_max: number | null;
  start_date: string | null;
  end_date: string | null;
  schedule_text: string | null;
  price_text: string | null;
  price_amount: number | null;
  location_text: string | null;
  signup_url: string | null;
  source_url: string | null;
  contact: Record<string, unknown> | null;
  fit_score: number | null;
  raw: Record<string, unknown> | null;
  created_at: string | null;
  fit_kids?: string[]; // family kids that fit by age (computed by the API)
}

// ── Chief-of-Staff: plan ──────────────────────────────────────────────
export interface CalendarEntry {
  id: string;
  user_id: string;
  kid_name: string | null;
  activity_id: string | null;
  title: string;
  week_start: string | null;
  start_ts: string | null;
  end_ts: string | null;
  all_day: boolean;
  location_text: string | null;
  kind: string; // camp | class | program | appointment | ...
  status: string; // confirmed | tentative | ...
  source: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface Todo {
  id: string;
  user_id: string;
  kid_name: string | null;
  activity_id: string | null;
  kind: string;
  title: string;
  detail: string | null;
  due_date: string | null;
  status: string; // open | done | ...
  source: string | null;
  source_artifact_id: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface TrackedActivity {
  id: string;
  user_id: string;
  kid_name: string | null;
  candidate_id: string | null;
  name: string;
  provider: string | null;
  week_start: string | null;
  status: string;
  pending_reason: string | null;
  price_amount: number | null;
  price_status: string;
  signup_url: string | null;
  contact: Record<string, unknown> | null;
  carpool_with: string | null;
  details: Record<string, unknown> | null;
  notes: string | null;
  decision_rationale: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface CostSummary {
  confirmed_total: number;
  tbd_count: number;
  item_count: number;
  lines: unknown[];
  by_kid: Record<string, number>;
}

export interface Conflict {
  kid_name: string | null;
  calendar_entry_id: string | null;
  calendar_title: string | null;
  recurring_id: string | null;
  recurring_title: string | null;
  weekday: number | null;
  detail: string;
}

export interface CoverageGap {
  id: string | null;
  week_start: string | null;
  kid_name: string | null;
  task: string | null;
  status: string | null;
  reason: string;
}

export interface UncoveredWeek {
  kid_name: string | null;
  week_start: string | null;
}

export interface PlanSummary {
  cost: CostSummary;
  conflicts: Conflict[];
  coverage_gaps: CoverageGap[];
  uncovered_weeks: UncoveredWeek[];
  pending_eligibility: TrackedActivity[];
}

// ── Chat ──────────────────────────────────────────────────────────────
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}
