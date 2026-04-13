import { useEffect, useState, type ReactNode } from "react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { clsx } from "clsx";
import { Card } from "../ui/Card";

interface KPICardProps {
  label: string;
  value: number;
  icon: ReactNode;
  trend?: "up" | "down" | "neutral";
  trendLabel?: string;
  loading?: boolean;
}

function AnimatedCounter({ target, duration = 1000 }: { target: number; duration?: number }) {
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (target === 0) { setCount(0); return; }
    const steps = 30;
    const increment = target / steps;
    const interval = duration / steps;
    let current = 0;
    const timer = setInterval(() => {
      current += increment;
      if (current >= target) {
        setCount(target);
        clearInterval(timer);
      } else {
        setCount(Math.floor(current));
      }
    }, interval);
    return () => clearInterval(timer);
  }, [target, duration]);

  return <>{count.toLocaleString()}</>;
}

function KPICardSkeleton() {
  return (
    <Card>
      <div className="animate-pulse space-y-3">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 bg-slate-200 dark:bg-slate-700 rounded-lg" />
          <div className="h-4 w-24 bg-slate-200 dark:bg-slate-700 rounded" />
        </div>
        <div className="h-8 w-20 bg-slate-200 dark:bg-slate-700 rounded" />
        <div className="h-4 w-16 bg-slate-200 dark:bg-slate-700 rounded" />
      </div>
    </Card>
  );
}

export function KPICard({ label, value, icon, trend = "neutral", trendLabel, loading }: KPICardProps) {
  if (loading) return <KPICardSkeleton />;

  const TrendIcon = trend === "up" ? TrendingUp : trend === "down" ? TrendingDown : Minus;
  const trendColor = trend === "up" ? "text-success" : trend === "down" ? "text-danger" : "text-slate-400";

  return (
    <Card>
      <div className="flex items-center gap-3 mb-2">
        <div className="h-10 w-10 rounded-lg bg-accent/10 text-accent flex items-center justify-center">
          {icon}
        </div>
        <p className="text-sm text-slate-500 dark:text-slate-400">{label}</p>
      </div>
      <p className="text-3xl font-bold">
        <AnimatedCounter target={value} />
      </p>
      {trendLabel && (
        <div className={clsx("flex items-center gap-1 mt-2 text-xs font-medium", trendColor)}>
          <TrendIcon className="h-3.5 w-3.5" />
          <span>{trendLabel}</span>
        </div>
      )}
    </Card>
  );
}
