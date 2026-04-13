import { RefreshCw } from "lucide-react";
import { clsx } from "clsx";

interface RefreshControlProps {
  interval: number | null;
  onIntervalChange: (interval: number | null) => void;
}

const OPTIONS: { label: string; value: number | null }[] = [
  { label: "30s", value: 30_000 },
  { label: "60s", value: 60_000 },
  { label: "Off", value: null },
];

export function RefreshControl({ interval, onIntervalChange }: RefreshControlProps) {
  return (
    <div className="flex items-center gap-2 text-xs text-slate-500">
      <RefreshCw className={clsx("h-3.5 w-3.5", interval !== null && "animate-spin")} />
      <span>Auto-refresh:</span>
      <div className="flex bg-slate-100 dark:bg-slate-800 rounded-lg overflow-hidden">
        {OPTIONS.map((opt) => (
          <button
            key={opt.label}
            onClick={() => onIntervalChange(opt.value)}
            className={clsx(
              "px-2.5 py-1 text-xs transition-colors",
              interval === opt.value
                ? "bg-accent text-white"
                : "text-slate-500 hover:text-slate-700 dark:hover:text-slate-300",
            )}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}
