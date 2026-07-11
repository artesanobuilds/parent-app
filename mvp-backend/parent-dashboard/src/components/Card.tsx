import { useState } from 'react';
import { Check, ExternalLink, Eye, Trash2, Undo2, X } from 'lucide-react';
import { deleteActivity, patchTodo, updateActivity } from '../api';
import type { BoardActivity } from '../types';

// THE board-card primitive (one per platform — iOS mirrors this in
// BoardCardView.swift). Extracted from Plan.tsx when the vertical chip became
// the second per-card divergence. All state/CTA logic stays server-driven
// (next_step / when / activity_type); this component only renders it.

// Chip labels for every canonical vertical — includes not-yet-doored types so
// an organically-typed card still gets a sensible chip. Server registry is
// the source of truth for DOOR copy; these are display fallbacks only.
export const CHIP_LABELS: Record<string, string> = {
  camp: 'Camp',
  extracurricular: 'Class',
  outing: 'Outing',
  school_event: 'School',
  trip: 'Trip',
};

export function BoardCard({
  a,
  gmailConnected,
  busy,
  showVerticalChip,
  onMutate,
}: {
  a: BoardActivity;
  gmailConnected: boolean;
  busy: boolean;
  /** Show the vertical chip only when the board actually spans verticals. */
  showVerticalChip?: boolean;
  onMutate: (activityId: string, fn: () => Promise<unknown>) => void;
}) {
  const step = a.next_step;
  // Register opens the signup page in a new tab; once opened, offer the
  // follow-through button so the parent can confirm they signed up.
  const [openedSignup, setOpenedSignup] = useState(false);
  // Two-tap inline confirms (same idiom as the register → "Mark registered"
  // follow-through): first tap arms, second tap commits.
  const [confirmPass, setConfirmPass] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const registeredStage = step.stage === 'registered' || step.stage === 'all_set';
  const declined = step.stage === 'declined';
  // The top to-do is the primary button for complete_todo cards; the rest
  // render as a small list with their own checkmarks.
  const restTodos = step.action === 'complete_todo' ? a.open_todos.slice(1) : a.open_todos;

  const primaryBtn =
    'flex items-center gap-200 bg-accent text-ink-on-photo-light rounded-lg px-400 py-200 text-sm font-medium disabled:opacity-60';
  const secondaryBtn =
    'border border-hairline rounded-lg px-400 py-200 text-sm text-ink-primary hover:bg-accent-tint disabled:opacity-50';

  const patchStatus = (fields: Record<string, unknown>) =>
    onMutate(a.id, () => updateActivity(a.id, fields));

  // Declining also auto-dismisses the activity's open to-dos (server-side).
  const pass = () =>
    patchStatus({ status: 'declined', decision_rationale: 'Passed from the board' });

  function onPrimary() {
    switch (step.action) {
      case 'plan':
        patchStatus({ status: 'planned' });
        break;
      case 'register':
        window.open(step.url ?? undefined, '_blank', 'noopener');
        setOpenedSignup(true);
        break;
      case 'mark_registered':
        patchStatus({ status: 'signed_up' });
        break;
      case 'complete_todo':
        if (step.todo_id) onMutate(a.id, () => patchTodo(step.todo_id!, 'done'));
        break;
      case 'restore':
        patchStatus({ status: 'exploring' });
        break;
    }
  }

  return (
    <div className={`bg-elevated border border-hairline rounded-xl p-600 ${busy ? 'opacity-60' : ''}`}>
      <div className="flex items-start justify-between gap-400">
        <h4 className="font-medium text-ink-primary">{a.name}</h4>
        {/* Pass is available from any stage; once registered it clears the
            activity's open to-dos, so require a second tap to confirm. */}
        {!declined &&
          (confirmPass ? (
            <div className="flex items-center gap-300 shrink-0">
              <button
                onClick={pass}
                disabled={busy}
                className="text-error text-sm hover:underline disabled:opacity-50"
              >
                Really pass? Clears its to-dos
              </button>
              <button
                onClick={() => setConfirmPass(false)}
                disabled={busy}
                className="text-ink-muted hover:text-ink-primary disabled:opacity-50"
                aria-label="Cancel pass"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <button
              onClick={() => (registeredStage ? setConfirmPass(true) : pass())}
              disabled={busy}
              className="text-ink-muted text-sm hover:text-ink-primary disabled:opacity-50 shrink-0"
            >
              Pass
            </button>
          ))}
      </div>
      <div className="flex flex-wrap gap-200 mt-300 text-sm text-ink-secondary">
        {showVerticalChip && a.activity_type && (
          <span className="border border-hairline rounded px-300 py-100 text-xs uppercase tracking-wide">
            {CHIP_LABELS[a.activity_type] ?? a.activity_type}
          </span>
        )}
        {a.kid_name && <span className="bg-accent-tint rounded px-300 py-100">{a.kid_name}</span>}
        {a.provider && <span className="bg-canvas rounded px-300 py-100">{a.provider}</span>}
        {a.price_amount != null && (
          <span className="bg-canvas rounded px-300 py-100 font-mono">${a.price_amount}</span>
        )}
      </div>
      {/* Server-rendered date line — shown verbatim (never re-formatted here) */}
      {a.when && <div className="mt-200 text-sm text-ink-secondary">{a.when}</div>}

      {/* The ONE primary action, hint (its consequence) directly underneath */}
      {step.action !== 'none' && (
        <div className="mt-400">
          {step.action === 'resolve' ? (
            <div className="text-warning text-sm">{step.label}</div>
          ) : step.action === 'register' ? (
            <div className="flex flex-wrap items-center gap-300">
              <button onClick={onPrimary} disabled={busy} className={primaryBtn}>
                <ExternalLink className="w-4 h-4" />
                {step.label}
              </button>
              {openedSignup && (
                <button
                  onClick={() => patchStatus({ status: 'signed_up' })}
                  disabled={busy}
                  className={secondaryBtn}
                >
                  Mark registered
                </button>
              )}
            </div>
          ) : (
            <div className="flex flex-wrap items-center gap-300">
              <button onClick={onPrimary} disabled={busy} className={primaryBtn}>
                {step.action === 'complete_todo' && <Check className="w-4 h-4" />}
                {step.action === 'restore' && <Undo2 className="w-4 h-4" />}
                {step.label}
              </button>
              {/* Declined cards can be removed for good (two-tap confirm). */}
              {declined &&
                (confirmDelete ? (
                  <div className="flex items-center gap-300">
                    <button
                      onClick={() => onMutate(a.id, () => deleteActivity(a.id))}
                      disabled={busy}
                      className="flex items-center gap-200 text-error text-sm hover:underline disabled:opacity-50"
                    >
                      <Trash2 className="w-4 h-4" />
                      Really delete?
                    </button>
                    <button
                      onClick={() => setConfirmDelete(false)}
                      disabled={busy}
                      className="text-ink-muted hover:text-ink-primary disabled:opacity-50"
                      aria-label="Cancel delete"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => setConfirmDelete(true)}
                    disabled={busy}
                    className="flex items-center gap-200 text-error text-sm hover:underline disabled:opacity-50"
                  >
                    <Trash2 className="w-4 h-4" />
                    Delete forever
                  </button>
                ))}
            </div>
          )}
          {step.hint && <div className="text-ink-muted text-xs mt-200">{step.hint}</div>}
          {declined && confirmDelete && (
            <div className="text-ink-muted text-xs mt-200">
              This permanently removes it and its to-dos/calendar entries
            </div>
          )}
        </div>
      )}

      {/* Remaining open to-dos, each completable in place */}
      {restTodos.length > 0 && (
        <div className="mt-300 flex flex-col gap-200">
          {restTodos.map((t) => (
            <div key={t.id} className="flex items-center gap-300 text-sm">
              <button
                onClick={() => onMutate(a.id, () => patchTodo(t.id, 'done'))}
                disabled={busy}
                className="w-4 h-4 rounded-full border border-strong hover:bg-accent-tint shrink-0 disabled:opacity-50"
                aria-label={`Complete ${t.title}`}
              />
              <span className="text-ink-secondary">{t.title}</span>
              {t.due_date && (
                <span className="text-ink-muted text-xs font-mono">Due {t.due_date}</span>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Tracking line: is the system watching this activity's emails? */}
      {registeredStage &&
        (a.watching ? (
          <div className="flex items-center gap-200 text-ink-muted text-xs mt-300">
            <Eye className="w-4 h-4 shrink-0" />
            <span>
              Watching {a.provider ?? a.name}&apos;s emails for confirmations &amp; payment
              reminders
            </span>
          </div>
        ) : !a.watchable ? (
          <div className="text-warning text-xs mt-300">
            Add the provider&apos;s contact email so I can watch for confirmations
          </div>
        ) : !gmailConnected ? (
          <div className="text-ink-muted text-xs mt-300">
            Connect Gmail to auto-track activity emails
          </div>
        ) : null)}
    </div>
  );
}
