import { useState } from "react";
import { User, Eye, Bell, Shield } from "lucide-react";
import { clsx } from "clsx";
import { useAuthStore } from "../store/authStore";
import { ProfileSection } from "../components/settings/ProfileSection";
import { WatchRulesSection } from "../components/settings/WatchRulesSection";
import { NotificationPreferences } from "../components/settings/NotificationPreferences";
import { AdminPanel } from "../components/settings/AdminPanel";

type TabId = "profile" | "watch-rules" | "notifications" | "admin";

interface Tab {
  id: TabId;
  label: string;
  icon: typeof User;
  adminOnly?: boolean;
}

const TABS: Tab[] = [
  { id: "profile", label: "Profile", icon: User },
  { id: "watch-rules", label: "Watch Rules", icon: Eye },
  { id: "notifications", label: "Notifications", icon: Bell },
  { id: "admin", label: "Admin", icon: Shield, adminOnly: true },
];

export default function Settings() {
  const user = useAuthStore((s) => s.user);
  const isAdmin = user?.role === "admin";
  const [activeTab, setActiveTab] = useState<TabId>("profile");

  const visibleTabs = TABS.filter((t) => !t.adminOnly || isAdmin);

  // If current tab is admin but user lost admin role, fall back
  if (activeTab === "admin" && !isAdmin) {
    setActiveTab("profile");
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>

      {/* Tab bar */}
      <nav aria-label="Settings tabs" className="flex gap-1 border-b border-slate-200 dark:border-slate-700">
        {visibleTabs.map((tab) => {
          const Icon = tab.icon;
          const active = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              role="tab"
              aria-selected={active}
              onClick={() => setActiveTab(tab.id)}
              className={clsx(
                "flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors",
                active
                  ? "border-accent text-accent"
                  : "border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300",
              )}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </button>
          );
        })}
      </nav>

      {/* Tab content */}
      <div>
        {activeTab === "profile" && <ProfileSection />}
        {activeTab === "watch-rules" && <WatchRulesSection />}
        {activeTab === "notifications" && <NotificationPreferences />}
        {activeTab === "admin" && isAdmin && <AdminPanel />}
      </div>
    </div>
  );
}
