import { useEffect } from "react";
import { CheckCircle2, AlertTriangle, XCircle, Info, X } from "lucide-react";
import { clsx } from "clsx";

type ToastVariant = "success" | "error" | "warning" | "info";

interface ToastProps {
  message: string;
  variant?: ToastVariant;
  onClose: () => void;
  duration?: number;
}

const icons: Record<ToastVariant, typeof CheckCircle2> = {
  success: CheckCircle2,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
};

const styles: Record<ToastVariant, string> = {
  success: "bg-success-50 border-success text-success-600",
  error: "bg-danger-50 border-danger text-danger-600",
  warning: "bg-accent-50 border-accent text-accent-600",
  info: "bg-blue-50 border-blue-500 text-blue-600",
};

export function Toast({ message, variant = "info", onClose, duration = 5000 }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(onClose, duration);
    return () => clearTimeout(timer);
  }, [onClose, duration]);

  const Icon = icons[variant];

  return (
    <div
      className={clsx(
        "flex items-center gap-3 px-4 py-3 rounded-lg border shadow-lg max-w-sm",
        styles[variant],
      )}
      role="alert"
    >
      <Icon className="h-5 w-5 shrink-0" />
      <p className="text-sm flex-1">{message}</p>
      <button onClick={onClose} className="p-0.5 hover:opacity-70" aria-label="Dismiss">
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}
