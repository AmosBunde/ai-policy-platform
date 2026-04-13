import { clsx } from "clsx";

interface PasswordStrengthBarProps {
  password: string;
}

type Strength = "empty" | "weak" | "medium" | "strong";

function getStrength(password: string): Strength {
  if (!password) return "empty";

  let score = 0;
  if (password.length >= 8) score++;
  if (password.length >= 12) score++;
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score++;
  if (/\d/.test(password)) score++;
  if (/[^a-zA-Z0-9]/.test(password)) score++;

  if (score <= 1) return "weak";
  if (score <= 3) return "medium";
  return "strong";
}

const strengthConfig: Record<Strength, { label: string; color: string; width: string }> = {
  empty: { label: "", color: "bg-slate-200", width: "w-0" },
  weak: { label: "Weak", color: "bg-danger", width: "w-1/3" },
  medium: { label: "Medium", color: "bg-accent", width: "w-2/3" },
  strong: { label: "Strong", color: "bg-success", width: "w-full" },
};

export function PasswordStrengthBar({ password }: PasswordStrengthBarProps) {
  const strength = getStrength(password);
  const config = strengthConfig[strength];

  if (strength === "empty") return null;

  return (
    <div className="space-y-1">
      <div className="h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
        <div
          className={clsx("h-full rounded-full transition-all duration-300", config.color, config.width)}
        />
      </div>
      <p className={clsx("text-xs", {
        "text-danger": strength === "weak",
        "text-accent-600": strength === "medium",
        "text-success": strength === "strong",
      })}>
        {config.label}
      </p>
    </div>
  );
}
