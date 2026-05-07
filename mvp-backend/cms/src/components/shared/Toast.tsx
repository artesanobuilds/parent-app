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
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`rounded-lg px-4 py-3 text-sm font-medium text-white shadow-lg transition-all ${
            t.type === "success" ? "bg-green-600" : "bg-red-600"
          }`}
        >
          {t.message}
        </div>
      ))}
    </div>
  );
}
