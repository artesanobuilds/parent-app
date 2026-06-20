interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ConfirmDialog({
  open,
  title,
  message,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40"
        onClick={onCancel}
      />

      {/* Dialog card */}
      <div className="relative z-10 w-full max-w-md rounded-lg bg-elevated p-700 shadow-e3">
        <h3 className="text-title-lg font-semibold text-ink-primary">{title}</h3>
        <p className="mt-200 text-body-md text-ink-muted">{message}</p>

        <div className="mt-700 flex justify-end gap-400">
          <button
            type="button"
            onClick={onCancel}
            className="rounded-md border border-hairline bg-elevated px-500 py-300 text-title-md font-medium text-ink-primary shadow-e0 hover:bg-sober transition-colors duration-fast"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className="rounded-md border border-error bg-elevated px-500 py-300 text-title-md font-medium text-error shadow-e0 hover:bg-error-tint transition-colors duration-fast"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  );
}
