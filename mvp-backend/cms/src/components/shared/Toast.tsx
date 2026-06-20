import { useEffect, useState } from "react";

type ToastType = "success" | "error";

interface ToastMessage {
  id: number;
  type: ToastType;
  message: string;
}

let addToast: (type: ToastType, message: string) => void = () => {};

let nextId = 0;

export const toast = {
  success: (message: string) => addToast("success", message),
  error: (message: string) => addToast("error", message),
};

export function Toaster() {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  useEffect(() => {
    addToast = (type: ToastType, message: string) => {
      const id = nextId++;
      setToasts((prev) => [...prev, { id, type, message }]);
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, 3000);
    };
    return () => {
      addToast = () => {};
    };
  }, []);

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-500 right-500 z-50 flex flex-col gap-300">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`rounded-md px-500 py-400 text-body-md font-medium shadow-e2 transition-all duration-base ${
            t.type === "success"
              ? "bg-success-tint text-success border border-success/30"
              : "bg-error-tint text-error border border-error/30"
          }`}
        >
          {t.message}
        </div>
      ))}
    </div>
  );
}
