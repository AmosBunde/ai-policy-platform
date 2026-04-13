import { useState } from "react";
import { Save, Mail, MessageSquare, Bell } from "lucide-react";
import { clsx } from "clsx";
import { Card } from "../ui/Card";
import { Button } from "../ui/Button";
import { Toast } from "../ui/Toast";

interface ChannelState {
  email: boolean;
  slack: boolean;
  inApp: boolean;
}

type DigestFrequency = "immediate" | "daily" | "weekly";

const CHANNELS = [
  { key: "email" as const, label: "Email", description: "Receive notifications via email", icon: Mail },
  { key: "slack" as const, label: "Slack", description: "Post to your Slack channel", icon: MessageSquare },
  { key: "inApp" as const, label: "In-App", description: "Show in notification center", icon: Bell },
];

const FREQUENCIES: { value: DigestFrequency; label: string; description: string }[] = [
  { value: "immediate", label: "Immediate", description: "Get notified as events happen" },
  { value: "daily", label: "Daily Digest", description: "One summary email per day at 9 AM" },
  { value: "weekly", label: "Weekly Digest", description: "One summary email per week on Monday" },
];

export function NotificationPreferences() {
  const [channels, setChannels] = useState<ChannelState>({ email: true, slack: false, inApp: true });
  const [frequency, setFrequency] = useState<DigestFrequency>("immediate");
  const [toast, setToast] = useState<{ message: string; variant: "success" | "error" } | null>(null);

  const toggleChannel = (key: keyof ChannelState) => {
    setChannels((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleSave = () => {
    setToast({ message: "Notification preferences saved.", variant: "success" });
  };

  return (
    <div className="space-y-6">
      {toast && (
        <div className="fixed top-4 right-4 z-50">
          <Toast message={toast.message} variant={toast.variant} onClose={() => setToast(null)} />
        </div>
      )}

      {/* Channel toggles */}
      <Card>
        <h3 className="text-lg font-semibold mb-4">Notification Channels</h3>
        <div className="space-y-4">
          {CHANNELS.map((ch) => {
            const Icon = ch.icon;
            const active = channels[ch.key];
            return (
              <div key={ch.key} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={clsx(
                    "p-2 rounded-lg",
                    active ? "bg-accent-50 text-accent-600" : "bg-slate-100 dark:bg-slate-800 text-slate-400",
                  )}>
                    <Icon className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">{ch.label}</p>
                    <p className="text-xs text-slate-500">{ch.description}</p>
                  </div>
                </div>
                <button
                  type="button"
                  role="switch"
                  aria-checked={active}
                  aria-label={`Toggle ${ch.label}`}
                  onClick={() => toggleChannel(ch.key)}
                  className={clsx(
                    "relative w-10 h-5 rounded-full shrink-0 transition-colors",
                    active ? "bg-success" : "bg-slate-300 dark:bg-slate-600",
                  )}
                >
                  <span
                    className={clsx(
                      "absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform",
                      active && "translate-x-5",
                    )}
                  />
                </button>
              </div>
            );
          })}
        </div>
      </Card>

      {/* Digest frequency */}
      <Card>
        <h3 className="text-lg font-semibold mb-4">Digest Frequency</h3>
        <div className="space-y-2">
          {FREQUENCIES.map((f) => (
            <label
              key={f.value}
              className={clsx(
                "flex items-center gap-3 p-3 rounded-lg cursor-pointer border-2 transition-colors",
                frequency === f.value
                  ? "border-accent bg-accent-50 dark:bg-accent-900/20"
                  : "border-slate-200 dark:border-slate-700 hover:border-slate-300",
              )}
            >
              <input
                type="radio"
                name="digest-frequency"
                value={f.value}
                checked={frequency === f.value}
                onChange={() => setFrequency(f.value)}
                className="text-accent focus:ring-accent/50"
              />
              <div>
                <p className="text-sm font-medium">{f.label}</p>
                <p className="text-xs text-slate-500">{f.description}</p>
              </div>
            </label>
          ))}
        </div>
      </Card>

      <Button size="sm" onClick={handleSave}>
        <Save className="h-4 w-4" /> Save Preferences
      </Button>
    </div>
  );
}
