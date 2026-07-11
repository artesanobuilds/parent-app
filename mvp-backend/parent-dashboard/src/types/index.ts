// Types mirror the backend response shapes. Confirmed against:
//   app/research/router.py, app/duckdb_storage.py (list_candidates / list_research_runs),
//   app/cos/router.py, app/cos/planning.py (build_plan_summary).

// ── Auth ──────────────────────────────────────────────────────────────
export interface AuthTokenResponse {
  token: string;
  user_id: string;
}

// Mirrors app/profiling.py ParentProfile / ChildProfile (all optional). The
// profile editor reads + writes these; list fields are replaced server-side.
export interface ParentProfile {
  name?: string | null;
  pronouns?: string | null;
  postal_code?: string | null;
  country?: string | null;
  primary_language?: string | null;
  parent_age_range?: string | null;
  adults_in_household?: number | null;
  household_structure?: string | null;
  employment?: string | null;
  work_hours?: string | null;
  energy_pattern?: string | null;
  default_stress_response?: string | null;
  dreaded_moment?: string | null;
  support_system?: string | null;
  support_boundaries?: string | null;
  cultural_background?: string | null;
  parenting_style?: string | null;
  stressors?: string[];
  goals?: string[];
  coping_strategies?: string[];
  deescalation_works?: string[];
  deescalation_backfires?: string[];
  mental_health_notes?: string | null;
  co_parenting?: string | null;
  guidance_style?: string | null;
}

export interface ChildProfile {
  name?: string | null;
  pronouns?: string | null;
  age?: number | null;
  grade_band?: string | null;
  temperament?: string | null;
  interests?: string[];
  strengths?: string[];
  academic_strengths?: string[];
  challenges?: string[];
  emotion_regulation?: string | null;
  social_profile?: string | null;
  learning_profile?: string | null;
  neurodiversity?: string | null;
  sensory_notes?: string | null;
  sleep_routine?: string | null;
  health_notes?: string | null;
  triggers?: string[];
  escalation_pattern?: string | null;
  calming_strategies?: string[];
  recent_changes?: string[];
  school_context?: string | null;
  teacher_notes?: string | null;
  sibling_conflicts?: string[];
  repair_helpers?: string[];
  motivators?: string[];
  safety_flags?: string | null;
}

export interface FamilyProfile {
  parent?: ParentProfile;
  children?: Record<string, ChildProfile>;
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
  candidates_considered?: number; // pool size the surfaced set was curated from
  recent?: string[];           // last few actions, oldest→newest
  // Live, capped preview of what's been found so far (streamed during a run).
  candidates_preview?: {
    name: string;
    city: string | null;
    category: string | null;
    fit_score: number | null;
    kid_name: string | null;
  }[];
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
  city?: string | null;
  region?: string | null;
  distance_mi?: number | null;
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
  // camp | extracurricular | outing | school_event | trip (null on pre-Phase-0 rows)
  activity_type: string | null;
  week_start: string | null; // derived anchor for week_block items (= start_date)
  start_date: string | null;
  end_date: string | null;
  rrule: string | null; // RFC-5545; weekly-only for now
  recur_time: string | null;
  recur_duration_min: number | null;
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

// ── Activity lifecycle board (GET /cos/plan/board) ───────────────────
// Mirrors app/cos/lifecycle.py build_board / next_step.

// Open to-do joined onto a board card (subset of Todo, most urgent first).
export interface BoardTodo {
  id: string;
  title: string;
  kind: string; // payment | form | action | task
  due_date: string | null;
  status: string;
}

// The ONE next action for a card. Labels state their consequence.
export interface NextStep {
  stage: string; // considering | to_register | registered | all_set | blocked | declined
  action:
    | 'plan'
    | 'register'
    | 'mark_registered'
    | 'complete_todo'
    | 'resolve'
    | 'restore'
    | 'none';
  label: string;
  hint: string;
  url?: string | null; // action=register
  todo_id?: string | null; // action=complete_todo
}

export interface BoardActivity extends TrackedActivity {
  open_todos: BoardTodo[];
  next_step: NextStep;
  watchable: boolean; // has a contact email
  watching: boolean; // gmail connected + watchable + registered
  // Server-rendered date line ("Week of Jul 13" / "Tuesdays 4:00 PM") —
  // rendered VERBATIM; date-display logic never forks per client.
  when: string | null;
}

export interface BoardStage {
  key: string;
  title: string;
  blurb: string;
  activities: BoardActivity[];
}

export interface PlanBoard {
  gmail_connected: boolean;
  stages: BoardStage[];
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
