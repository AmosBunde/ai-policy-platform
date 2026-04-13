import { type HTMLAttributes } from "react";
import { clsx } from "clsx";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "glass";
}

export function Card({ variant = "default", className, children, ...props }: CardProps) {
  return (
    <div
      className={clsx(
        "rounded-xl p-6",
        variant === "glass"
          ? "glass"
          : "bg-white dark:bg-surface border border-slate-200 dark:border-slate-700",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}
