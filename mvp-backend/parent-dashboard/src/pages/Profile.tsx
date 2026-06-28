import { useEffect, useState } from 'react';
import { X } from 'lucide-react';
import { getProfile, updateProfile, updateKid } from '../api';
import type { ChildProfile, FamilyProfile, ParentProfile } from '../types';

// Settings → Profile editor (web parity, 2026-06-28). Edits the full parent +
// kid field set (most populated by the coaching/onboarding agents over time),
// adds a kid, and surfaces the "What we've learned" fields for review/correction.
// Writes via PATCH /profile and PATCH /profile/kids/{name}.

const OPT = {
  language: ['en', 'es', 'zh', 'other'],
  ageRange: ['<25', '25-34', '35-44', '45-54', '55+', 'prefer_not_to_say'],
  household: ['single', 'co-parenting', 'two-parent', 'divorced', 'widowed', 'blended', 'multigenerational'],
  employment: ['stay-at-home', 'part-time', 'full-time', 'shift', 'other'],
  gradeBand: ['preschool', 'elementary', 'middle', 'high'],
  guidanceStyle: ['concise scripts', 'explanations'],
  stressResponse: ['raise voice', 'withdraw', 'stays regulated'],
};

export default function Profile() {
  const [parent, setParent] = useState<ParentProfile>({});
  const [kids, setKids] = useState<Record<string, ChildProfile>>({});
  const [err, setErr] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);

  async function load() {
    try {
      const fam = await getProfile();
      setParent(fam.parent ?? {});
      setKids(fam.children ?? {});
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Failed to load profile');
    }
  }
  useEffect(() => {
    void load();
  }, []);

  function apply(fam: FamilyProfile) {
    setParent(fam.parent ?? {});
    setKids(fam.children ?? {});
  }

  function flash(msg: string) {
    setNote(msg);
    setErr(null);
    window.setTimeout(() => setNote(null), 2500);
  }

  async function saveParent() {
    try {
      apply(await updateProfile(parentPayload(parent)));
      flash('Saved your profile.');
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Save failed');
    }
  }

  async function saveKid(key: string) {
    try {
      apply(await updateKid(key, kidPayload(kids[key] ?? {})));
      flash('Saved.');
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Save failed');
    }
  }

  function setKid(key: string, patch: Partial<ChildProfile>) {
    setKids((prev) => ({ ...prev, [key]: { ...prev[key], ...patch } }));
  }

  return (
    <div className="p-700 max-w-4xl">
      <div className="text-ink-muted text-xs uppercase tracking-wide">Settings</div>
      <h1 className="font-display text-3xl text-ink-primary mb-600">Profile</h1>
      {err && <div className="text-error mb-500">{err}</div>}
      {note && <div className="text-accent mb-500">{note}</div>}

      {/* ── Parent ─────────────────────────────────────────────── */}
      <Card title="You">
        <Grid>
          <Field label="Name" value={parent.name} onChange={(v) => setParent({ ...parent, name: v })} />
          <Field label="Pronouns" value={parent.pronouns} onChange={(v) => setParent({ ...parent, pronouns: v })} />
          <Field label="ZIP / Postal code" value={parent.postal_code} onChange={(v) => setParent({ ...parent, postal_code: v })} />
          <Field label="Country" value={parent.country} onChange={(v) => setParent({ ...parent, country: v })} />
          <Select label="Language" options={OPT.language} value={parent.primary_language} onChange={(v) => setParent({ ...parent, primary_language: v })} />
          <Select label="Age range" options={OPT.ageRange} value={parent.parent_age_range} onChange={(v) => setParent({ ...parent, parent_age_range: v })} />
          <Field label="Adults at home" type="number" value={parent.adults_in_household ?? undefined} onChange={(v) => setParent({ ...parent, adults_in_household: v ? Number(v) : null })} />
          <Select label="Household" options={OPT.household} value={parent.household_structure} onChange={(v) => setParent({ ...parent, household_structure: v })} />
          <Select label="Employment" options={OPT.employment} value={parent.employment} onChange={(v) => setParent({ ...parent, employment: v })} />
          <Field label="Work hours" value={parent.work_hours} onChange={(v) => setParent({ ...parent, work_hours: v })} />
          <Field label="Energy pattern" value={parent.energy_pattern} onChange={(v) => setParent({ ...parent, energy_pattern: v })} />
        </Grid>

        <Learned>
          <Field label="Parenting style" value={parent.parenting_style} onChange={(v) => setParent({ ...parent, parenting_style: v })} />
          <Select label="Guidance style" options={OPT.guidanceStyle} value={parent.guidance_style} onChange={(v) => setParent({ ...parent, guidance_style: v })} />
          <Select label="Stress response" options={OPT.stressResponse} value={parent.default_stress_response} onChange={(v) => setParent({ ...parent, default_stress_response: v })} />
          <Field label="Dreaded moment" value={parent.dreaded_moment} onChange={(v) => setParent({ ...parent, dreaded_moment: v })} />
          <Field label="Support system" value={parent.support_system} onChange={(v) => setParent({ ...parent, support_system: v })} />
          <Field label="Support boundaries" value={parent.support_boundaries} onChange={(v) => setParent({ ...parent, support_boundaries: v })} />
          <Field label="Co-parenting" value={parent.co_parenting} onChange={(v) => setParent({ ...parent, co_parenting: v })} />
          <Field label="Mental-health notes" value={parent.mental_health_notes} onChange={(v) => setParent({ ...parent, mental_health_notes: v })} />
          <Chips label="Stressors" values={parent.stressors} onChange={(v) => setParent({ ...parent, stressors: v })} />
          <Chips label="Goals" values={parent.goals} onChange={(v) => setParent({ ...parent, goals: v })} />
          <Chips label="Coping strategies" values={parent.coping_strategies} onChange={(v) => setParent({ ...parent, coping_strategies: v })} />
          <Chips label="What helps me de-escalate" values={parent.deescalation_works} onChange={(v) => setParent({ ...parent, deescalation_works: v })} />
          <Chips label="What backfires" values={parent.deescalation_backfires} onChange={(v) => setParent({ ...parent, deescalation_backfires: v })} />
        </Learned>

        <SaveBar onSave={saveParent} />
      </Card>

      {/* ── Kids ───────────────────────────────────────────────── */}
      {Object.keys(kids).sort().map((key) => {
        const kid = kids[key] ?? {};
        return (
          <Card key={key} title={kid.name ?? key}>
            <Grid>
              <Field label="Name" value={kid.name} onChange={(v) => setKid(key, { name: v })} />
              <Field label="Pronouns" value={kid.pronouns} onChange={(v) => setKid(key, { pronouns: v })} />
              <Field label="Age" type="number" value={kid.age ?? undefined} onChange={(v) => setKid(key, { age: v ? Number(v) : null })} />
              <Select label="Grade band" options={OPT.gradeBand} value={kid.grade_band} onChange={(v) => setKid(key, { grade_band: v })} />
            </Grid>
            <Learned>
              <Field label="Temperament" value={kid.temperament} onChange={(v) => setKid(key, { temperament: v })} />
              <Chips label="Interests" values={kid.interests} onChange={(v) => setKid(key, { interests: v })} />
              <Chips label="Strengths" values={kid.strengths} onChange={(v) => setKid(key, { strengths: v })} />
              <Chips label="Academic strengths" values={kid.academic_strengths} onChange={(v) => setKid(key, { academic_strengths: v })} />
              <Chips label="Challenges" values={kid.challenges} onChange={(v) => setKid(key, { challenges: v })} />
              <Chips label="Triggers" values={kid.triggers} onChange={(v) => setKid(key, { triggers: v })} />
              <Chips label="Calming strategies" values={kid.calming_strategies} onChange={(v) => setKid(key, { calming_strategies: v })} />
              <Chips label="Motivators" values={kid.motivators} onChange={(v) => setKid(key, { motivators: v })} />
              <Chips label="Repair helpers" values={kid.repair_helpers} onChange={(v) => setKid(key, { repair_helpers: v })} />
              <Chips label="Recent changes" values={kid.recent_changes} onChange={(v) => setKid(key, { recent_changes: v })} />
              <Chips label="Sibling conflicts" values={kid.sibling_conflicts} onChange={(v) => setKid(key, { sibling_conflicts: v })} />
              <Field label="Emotion regulation" value={kid.emotion_regulation} onChange={(v) => setKid(key, { emotion_regulation: v })} />
              <Field label="Social profile" value={kid.social_profile} onChange={(v) => setKid(key, { social_profile: v })} />
              <Field label="Learning profile" value={kid.learning_profile} onChange={(v) => setKid(key, { learning_profile: v })} />
              <Field label="Neurodiversity" value={kid.neurodiversity} onChange={(v) => setKid(key, { neurodiversity: v })} />
              <Field label="Sensory notes" value={kid.sensory_notes} onChange={(v) => setKid(key, { sensory_notes: v })} />
              <Field label="Sleep routine" value={kid.sleep_routine} onChange={(v) => setKid(key, { sleep_routine: v })} />
              <Field label="Health notes" value={kid.health_notes} onChange={(v) => setKid(key, { health_notes: v })} />
              <Field label="Escalation pattern" value={kid.escalation_pattern} onChange={(v) => setKid(key, { escalation_pattern: v })} />
              <Field label="School context" value={kid.school_context} onChange={(v) => setKid(key, { school_context: v })} />
              <Field label="Teacher notes" value={kid.teacher_notes} onChange={(v) => setKid(key, { teacher_notes: v })} />
              <Field label="Safety flags" value={kid.safety_flags} onChange={(v) => setKid(key, { safety_flags: v })} />
            </Learned>
            <SaveBar onSave={() => saveKid(key)} />
          </Card>
        );
      })}

      <AddKid onAdded={apply} onError={setErr} />
    </div>
  );
}

// ── Add-a-kid form ──────────────────────────────────────────────────────

function AddKid({ onAdded, onError }: { onAdded: (f: FamilyProfile) => void; onError: (m: string) => void }) {
  const [name, setName] = useState('');
  const [age, setAge] = useState('');
  const [grade, setGrade] = useState('');

  async function add() {
    const n = name.trim();
    if (!n) return;
    try {
      const fields: Record<string, unknown> = { name: n };
      if (age.trim()) fields.age = Number(age);
      if (grade) fields.grade_band = grade;
      onAdded(await updateKid(n, fields));
      setName('');
      setAge('');
      setGrade('');
    } catch (e) {
      onError(e instanceof Error ? e.message : 'Could not add kid');
    }
  }

  return (
    <Card title="Add a kid">
      <Grid>
        <Field label="Name" value={name} onChange={(v) => setName(v ?? '')} />
        <Field label="Age" type="number" value={age} onChange={(v) => setAge(v ?? '')} />
        <Select label="Grade band" options={OPT.gradeBand} value={grade} onChange={(v) => setGrade(v ?? '')} />
      </Grid>
      <div className="mt-500">
        <button
          onClick={add}
          disabled={!name.trim()}
          className="bg-accent text-white px-500 py-300 rounded-lg text-sm font-medium disabled:opacity-50"
        >
          Add kid
        </button>
      </div>
    </Card>
  );
}

// ── Small presentational helpers ────────────────────────────────────────

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="bg-elevated border border-hairline rounded-lg p-600 mb-600">
      <h2 className="font-display text-xl text-ink-primary mb-500">{title}</h2>
      {children}
    </section>
  );
}

function Grid({ children }: { children: React.ReactNode }) {
  return <div className="grid grid-cols-1 md:grid-cols-2 gap-400">{children}</div>;
}

function Learned({ children }: { children: React.ReactNode }) {
  return (
    <div className="mt-600 pt-500 border-t border-hairline">
      <div className="text-ink-muted text-xs uppercase tracking-wide mb-100">✦ What we've learned</div>
      <div className="text-ink-secondary text-sm mb-400">
        Gathered from your conversations with your coach. Edit or remove anything that's off.
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-400">{children}</div>
    </div>
  );
}

function SaveBar({ onSave }: { onSave: () => void }) {
  return (
    <div className="mt-500">
      <button onClick={onSave} className="bg-accent text-white px-500 py-300 rounded-lg text-sm font-medium">
        Save
      </button>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  type = 'text',
}: {
  label: string;
  value?: string | number | null;
  onChange: (v: string) => void;
  type?: string;
}) {
  return (
    <label className="flex flex-col gap-100">
      <span className="text-ink-muted text-xs">{label}</span>
      <input
        type={type}
        value={value ?? ''}
        onChange={(e) => onChange(e.target.value)}
        className="border border-hairline rounded px-300 py-200 bg-canvas text-ink-primary text-sm"
      />
    </label>
  );
}

function Select({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: string[];
  value?: string | null;
  onChange: (v: string) => void;
}) {
  return (
    <label className="flex flex-col gap-100">
      <span className="text-ink-muted text-xs">{label}</span>
      <select
        value={value ?? ''}
        onChange={(e) => onChange(e.target.value)}
        className="border border-hairline rounded px-300 py-200 bg-canvas text-ink-primary text-sm"
      >
        <option value="">Not set</option>
        {options.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    </label>
  );
}

function Chips({
  label,
  values,
  onChange,
}: {
  label: string;
  values?: string[];
  onChange: (v: string[]) => void;
}) {
  const [draft, setDraft] = useState('');
  const items = values ?? [];

  function add() {
    const t = draft.trim();
    if (t && !items.includes(t)) onChange([...items, t]);
    setDraft('');
  }

  return (
    <label className="flex flex-col gap-100 md:col-span-2">
      <span className="text-ink-muted text-xs">{label}</span>
      <div className="flex flex-wrap gap-200 items-center">
        {items.map((item, i) => (
          <span key={i} className="inline-flex items-center gap-100 bg-accent-tint text-ink-primary text-sm px-300 py-100 rounded-full">
            {item}
            <button
              onClick={() => onChange(items.filter((_, j) => j !== i))}
              className="text-ink-muted hover:text-ink-primary"
              aria-label={`Remove ${item}`}
            >
              <X size={13} />
            </button>
          </span>
        ))}
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              add();
            }
          }}
          onBlur={add}
          placeholder="Add…"
          className="border border-hairline rounded px-300 py-100 bg-canvas text-ink-primary text-sm min-w-24 flex-1"
        />
      </div>
    </label>
  );
}

// ── Payload builders (always include the editable keys so removals persist) ──

function parentPayload(p: ParentProfile): Record<string, unknown> {
  return {
    name: p.name ?? '',
    pronouns: p.pronouns ?? '',
    postal_code: p.postal_code ?? '',
    country: p.country ?? '',
    primary_language: p.primary_language ?? '',
    parent_age_range: p.parent_age_range ?? '',
    adults_in_household: p.adults_in_household ?? null,
    household_structure: p.household_structure ?? '',
    employment: p.employment ?? '',
    work_hours: p.work_hours ?? '',
    energy_pattern: p.energy_pattern ?? '',
    parenting_style: p.parenting_style ?? '',
    guidance_style: p.guidance_style ?? '',
    default_stress_response: p.default_stress_response ?? '',
    dreaded_moment: p.dreaded_moment ?? '',
    support_system: p.support_system ?? '',
    support_boundaries: p.support_boundaries ?? '',
    co_parenting: p.co_parenting ?? '',
    mental_health_notes: p.mental_health_notes ?? '',
    stressors: p.stressors ?? [],
    goals: p.goals ?? [],
    coping_strategies: p.coping_strategies ?? [],
    deescalation_works: p.deescalation_works ?? [],
    deescalation_backfires: p.deescalation_backfires ?? [],
  };
}

function kidPayload(c: ChildProfile): Record<string, unknown> {
  return {
    name: c.name ?? '',
    pronouns: c.pronouns ?? '',
    age: c.age ?? null,
    grade_band: c.grade_band ?? '',
    temperament: c.temperament ?? '',
    emotion_regulation: c.emotion_regulation ?? '',
    social_profile: c.social_profile ?? '',
    learning_profile: c.learning_profile ?? '',
    neurodiversity: c.neurodiversity ?? '',
    sensory_notes: c.sensory_notes ?? '',
    sleep_routine: c.sleep_routine ?? '',
    health_notes: c.health_notes ?? '',
    escalation_pattern: c.escalation_pattern ?? '',
    school_context: c.school_context ?? '',
    teacher_notes: c.teacher_notes ?? '',
    safety_flags: c.safety_flags ?? '',
    interests: c.interests ?? [],
    strengths: c.strengths ?? [],
    academic_strengths: c.academic_strengths ?? [],
    challenges: c.challenges ?? [],
    triggers: c.triggers ?? [],
    calming_strategies: c.calming_strategies ?? [],
    recent_changes: c.recent_changes ?? [],
    sibling_conflicts: c.sibling_conflicts ?? [],
    repair_helpers: c.repair_helpers ?? [],
    motivators: c.motivators ?? [],
  };
}
