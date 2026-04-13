import { useState } from "react";
import { Shield, UserCog, Globe, Activity, CheckCircle2, AlertTriangle, XCircle } from "lucide-react";
import { clsx } from "clsx";
import { Card } from "../ui/Card";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";
import { Modal } from "../ui/Modal";

/* ------------------------------------------------------------------ */
/*  Types & Sample Data                                                */
/* ------------------------------------------------------------------ */

interface ManagedUser {
  id: string;
  email: string;
  fullName: string;
  role: string;
  status: "active" | "inactive";
}

interface RegSource {
  id: string;
  name: string;
  url: string;
  status: "active" | "paused" | "error";
  lastCrawled: string;
}

interface ServiceHealth {
  name: string;
  status: "healthy" | "degraded" | "down";
  uptime: string;
}

const SAMPLE_USERS: ManagedUser[] = [
  { id: "u1", email: "admin@regulatorai.com", fullName: "Admin User", role: "admin", status: "active" },
  { id: "u2", email: "analyst@regulatorai.com", fullName: "Jane Analyst", role: "analyst", status: "active" },
  { id: "u3", email: "viewer@regulatorai.com", fullName: "Bob Viewer", role: "viewer", status: "active" },
  { id: "u4", email: "inactive@regulatorai.com", fullName: "Old User", role: "analyst", status: "inactive" },
];

const SAMPLE_SOURCES: RegSource[] = [
  { id: "s1", name: "EUR-Lex", url: "https://eur-lex.europa.eu", status: "active", lastCrawled: "2024-12-22T08:00:00Z" },
  { id: "s2", name: "Federal Register", url: "https://federalregister.gov", status: "active", lastCrawled: "2024-12-22T06:30:00Z" },
  { id: "s3", name: "UK Legislation", url: "https://legislation.gov.uk", status: "paused", lastCrawled: "2024-12-20T12:00:00Z" },
  { id: "s4", name: "Singapore Statutes", url: "https://sso.agc.gov.sg", status: "error", lastCrawled: "2024-12-19T10:00:00Z" },
];

const SAMPLE_HEALTH: ServiceHealth[] = [
  { name: "Ingestion Service", status: "healthy", uptime: "99.9%" },
  { name: "Enrichment Service", status: "healthy", uptime: "99.7%" },
  { name: "Compliance Service", status: "degraded", uptime: "98.2%" },
  { name: "Notification Service", status: "healthy", uptime: "99.8%" },
];

const HEALTH_CONFIG: Record<ServiceHealth["status"], { icon: typeof CheckCircle2; color: string; label: string }> = {
  healthy: { icon: CheckCircle2, color: "text-success", label: "Healthy" },
  degraded: { icon: AlertTriangle, color: "text-accent-600", label: "Degraded" },
  down: { icon: XCircle, color: "text-danger", label: "Down" },
};

const ROLES = ["admin", "analyst", "viewer"];

/* ------------------------------------------------------------------ */
/*  AdminPanel                                                         */
/* ------------------------------------------------------------------ */

export function AdminPanel() {
  const [users, setUsers] = useState<ManagedUser[]>(SAMPLE_USERS);
  const [sources, setSources] = useState<RegSource[]>(SAMPLE_SOURCES);
  const [roleModal, setRoleModal] = useState<{ user: ManagedUser; newRole: string } | null>(null);

  const toggleUserStatus = (id: string) => {
    setUsers((prev) =>
      prev.map((u) =>
        u.id === id ? { ...u, status: u.status === "active" ? "inactive" : "active" } : u,
      ),
    );
  };

  const changeRole = () => {
    if (!roleModal) return;
    setUsers((prev) =>
      prev.map((u) => (u.id === roleModal.user.id ? { ...u, role: roleModal.newRole } : u)),
    );
    setRoleModal(null);
  };

  const toggleSource = (id: string) => {
    setSources((prev) =>
      prev.map((s) =>
        s.id === id
          ? { ...s, status: s.status === "active" ? "paused" : "active" }
          : s,
      ),
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-accent-600">
        <Shield className="h-5 w-5" />
        <h3 className="text-lg font-semibold">Administration</h3>
      </div>

      {/* User management */}
      <Card>
        <div className="flex items-center gap-2 mb-4">
          <UserCog className="h-4 w-4 text-slate-500" />
          <h4 className="font-medium">User Management</h4>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-700 text-left text-slate-500">
                <th className="pb-2 font-medium">Email</th>
                <th className="pb-2 font-medium">Name</th>
                <th className="pb-2 font-medium">Role</th>
                <th className="pb-2 font-medium">Status</th>
                <th className="pb-2 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b border-slate-100 dark:border-slate-800">
                  <td className="py-2">{u.email}</td>
                  <td className="py-2">{u.fullName}</td>
                  <td className="py-2 capitalize">{u.role}</td>
                  <td className="py-2">
                    <Badge variant={u.status === "active" ? "success" : "default"}>
                      {u.status === "active" ? "Active" : "Inactive"}
                    </Badge>
                  </td>
                  <td className="py-2">
                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleUserStatus(u.id)}
                      >
                        {u.status === "active" ? "Deactivate" : "Activate"}
                      </Button>
                      <select
                        value={u.role}
                        onChange={(e) => setRoleModal({ user: u, newRole: e.target.value })}
                        className="px-2 py-1 text-xs rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-navy-900"
                        aria-label={`Change role for ${u.email}`}
                      >
                        {ROLES.map((r) => (
                          <option key={r} value={r}>{r}</option>
                        ))}
                      </select>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Regulatory sources */}
      <Card>
        <div className="flex items-center gap-2 mb-4">
          <Globe className="h-4 w-4 text-slate-500" />
          <h4 className="font-medium">Regulatory Sources</h4>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-700 text-left text-slate-500">
                <th className="pb-2 font-medium">Name</th>
                <th className="pb-2 font-medium">URL</th>
                <th className="pb-2 font-medium">Status</th>
                <th className="pb-2 font-medium">Last Crawled</th>
                <th className="pb-2 font-medium">Toggle</th>
              </tr>
            </thead>
            <tbody>
              {sources.map((s) => (
                <tr key={s.id} className="border-b border-slate-100 dark:border-slate-800">
                  <td className="py-2 font-medium">{s.name}</td>
                  <td className="py-2 text-slate-500 truncate max-w-[200px]">{s.url}</td>
                  <td className="py-2">
                    <Badge
                      variant={
                        s.status === "active" ? "success" : s.status === "error" ? "danger" : "default"
                      }
                    >
                      {s.status}
                    </Badge>
                  </td>
                  <td className="py-2 text-slate-500">{new Date(s.lastCrawled).toLocaleString()}</td>
                  <td className="py-2">
                    <button
                      type="button"
                      role="switch"
                      aria-checked={s.status === "active"}
                      aria-label={`Toggle ${s.name}`}
                      onClick={() => toggleSource(s.id)}
                      className={clsx(
                        "relative w-10 h-5 rounded-full shrink-0 transition-colors",
                        s.status === "active" ? "bg-success" : "bg-slate-300 dark:bg-slate-600",
                      )}
                    >
                      <span
                        className={clsx(
                          "absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform",
                          s.status === "active" && "translate-x-5",
                        )}
                      />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* System health */}
      <Card>
        <div className="flex items-center gap-2 mb-4">
          <Activity className="h-4 w-4 text-slate-500" />
          <h4 className="font-medium">System Health</h4>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {SAMPLE_HEALTH.map((svc) => {
            const cfg = HEALTH_CONFIG[svc.status];
            const Icon = cfg.icon;
            return (
              <div
                key={svc.name}
                className="flex items-center gap-3 p-3 rounded-lg border border-slate-200 dark:border-slate-700"
              >
                <Icon className={clsx("h-5 w-5 shrink-0", cfg.color)} />
                <div className="min-w-0">
                  <p className="text-sm font-medium truncate">{svc.name}</p>
                  <p className="text-xs text-slate-500">
                    {cfg.label} &middot; {svc.uptime}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      {/* Role change confirmation */}
      <Modal
        open={roleModal !== null}
        onClose={() => setRoleModal(null)}
        title="Change User Role"
      >
        <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
          Change <strong>{roleModal?.user.fullName}</strong>&apos;s role from{" "}
          <strong className="capitalize">{roleModal?.user.role}</strong> to{" "}
          <strong className="capitalize">{roleModal?.newRole}</strong>?
        </p>
        <div className="flex items-center gap-2 justify-end">
          <Button variant="ghost" size="sm" onClick={() => setRoleModal(null)}>
            Cancel
          </Button>
          <Button size="sm" onClick={changeRole}>
            Confirm
          </Button>
        </div>
      </Modal>
    </div>
  );
}
