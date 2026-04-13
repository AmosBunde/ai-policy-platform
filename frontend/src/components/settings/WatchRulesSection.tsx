import { useState } from "react";
import { Plus, Pencil, Trash2, X } from "lucide-react";
import { clsx } from "clsx";
import { Card } from "../ui/Card";
import { Input } from "../ui/Input";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";
import { Modal } from "../ui/Modal";

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface Condition {
  field: string;
  operator: string;
  value: string;
}

interface WatchRule {
  id: string;
  name: string;
  active: boolean;
  conditions: Condition[];
  channels: string[];
}

const FIELDS = [
  { value: "jurisdiction", label: "Jurisdiction" },
  { value: "urgencyLevel", label: "Urgency Level" },
  { value: "category", label: "Category" },
  { value: "status", label: "Status" },
  { value: "title", label: "Title" },
];

const OPERATORS = [
  { value: "equals", label: "equals" },
  { value: "not_equals", label: "does not equal" },
  { value: "contains", label: "contains" },
  { value: "starts_with", label: "starts with" },
];

const CHANNELS = [
  { value: "email", label: "Email" },
  { value: "slack", label: "Slack" },
  { value: "in_app", label: "In-App" },
];

const SAMPLE_RULES: WatchRule[] = [
  {
    id: "wr1",
    name: "EU High Urgency",
    active: true,
    conditions: [
      { field: "jurisdiction", operator: "equals", value: "EU" },
      { field: "urgencyLevel", operator: "equals", value: "critical" },
    ],
    channels: ["email", "in_app"],
  },
  {
    id: "wr2",
    name: "US Federal Updates",
    active: true,
    conditions: [{ field: "jurisdiction", operator: "equals", value: "US-Federal" }],
    channels: ["email"],
  },
  {
    id: "wr3",
    name: "Privacy Category Watch",
    active: false,
    conditions: [{ field: "category", operator: "contains", value: "privacy" }],
    channels: ["slack", "in_app"],
  },
];

/* ------------------------------------------------------------------ */
/*  Condition Builder                                                  */
/* ------------------------------------------------------------------ */

function ConditionRow({
  condition,
  onChange,
  onRemove,
}: {
  condition: Condition;
  onChange: (c: Condition) => void;
  onRemove: () => void;
}) {
  return (
    <div className="flex items-center gap-2">
      <select
        value={condition.field}
        onChange={(e) => onChange({ ...condition, field: e.target.value })}
        className="px-2 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-navy-900"
        aria-label="Field"
      >
        {FIELDS.map((f) => (
          <option key={f.value} value={f.value}>{f.label}</option>
        ))}
      </select>
      <select
        value={condition.operator}
        onChange={(e) => onChange({ ...condition, operator: e.target.value })}
        className="px-2 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-navy-900"
        aria-label="Operator"
      >
        {OPERATORS.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
      <input
        type="text"
        value={condition.value}
        onChange={(e) => onChange({ ...condition, value: e.target.value })}
        placeholder="Value"
        className="flex-1 px-2 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-navy-900 focus:outline-none focus:ring-2 focus:ring-accent/50"
        aria-label="Value"
      />
      <button
        type="button"
        onClick={onRemove}
        className="p-1 text-slate-400 hover:text-danger"
        aria-label="Remove condition"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Rule Form                                                          */
/* ------------------------------------------------------------------ */

function RuleForm({
  initial,
  onSave,
  onCancel,
}: {
  initial?: WatchRule;
  onSave: (rule: Omit<WatchRule, "id">) => void;
  onCancel: () => void;
}) {
  const [name, setName] = useState(initial?.name ?? "");
  const [conditions, setConditions] = useState<Condition[]>(
    initial?.conditions ?? [{ field: "jurisdiction", operator: "equals", value: "" }],
  );
  const [channels, setChannels] = useState<Set<string>>(new Set(initial?.channels ?? []));
  const [nameError, setNameError] = useState("");

  const updateCondition = (i: number, c: Condition) => {
    setConditions((prev) => prev.map((x, idx) => (idx === i ? c : x)));
  };

  const removeCondition = (i: number) => {
    setConditions((prev) => prev.filter((_, idx) => idx !== i));
  };

  const addCondition = () => {
    setConditions((prev) => [...prev, { field: "jurisdiction", operator: "equals", value: "" }]);
  };

  const toggleChannel = (ch: string) => {
    setChannels((prev) => {
      const next = new Set(prev);
      if (next.has(ch)) next.delete(ch);
      else next.add(ch);
      return next;
    });
  };

  const handleSubmit = () => {
    if (!name.trim()) {
      setNameError("Rule name is required");
      return;
    }
    setNameError("");
    onSave({
      name,
      active: initial?.active ?? true,
      conditions,
      channels: Array.from(channels),
    });
  };

  return (
    <Card className="space-y-4">
      <h4 className="font-medium">{initial ? "Edit Rule" : "Create Rule"}</h4>

      <Input
        label="Rule Name"
        value={name}
        onChange={(e) => setName(e.target.value)}
        error={nameError}
        placeholder="e.g. EU Critical Alerts"
      />

      {/* Conditions */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
          Conditions
        </label>
        {conditions.map((c, i) => (
          <ConditionRow
            key={i}
            condition={c}
            onChange={(updated) => updateCondition(i, updated)}
            onRemove={() => removeCondition(i)}
          />
        ))}
        <Button variant="ghost" size="sm" onClick={addCondition}>
          <Plus className="h-3.5 w-3.5" /> Add Condition
        </Button>
      </div>

      {/* Channels */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
          Notification Channels
        </label>
        <div className="flex gap-4">
          {CHANNELS.map((ch) => (
            <label key={ch.value} className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={channels.has(ch.value)}
                onChange={() => toggleChannel(ch.value)}
                className="rounded border-slate-300 text-accent focus:ring-accent/50"
              />
              {ch.label}
            </label>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Button size="sm" onClick={handleSubmit}>
          {initial ? "Update Rule" : "Create Rule"}
        </Button>
        <Button variant="ghost" size="sm" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </Card>
  );
}

/* ------------------------------------------------------------------ */
/*  Main Section                                                       */
/* ------------------------------------------------------------------ */

export function WatchRulesSection() {
  const [rules, setRules] = useState<WatchRule[]>(SAMPLE_RULES);
  const [showForm, setShowForm] = useState(false);
  const [editingRule, setEditingRule] = useState<WatchRule | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<WatchRule | null>(null);

  const toggleActive = (id: string) => {
    setRules((prev) =>
      prev.map((r) => (r.id === id ? { ...r, active: !r.active } : r)),
    );
  };

  const handleSave = (data: Omit<WatchRule, "id">) => {
    if (editingRule) {
      setRules((prev) =>
        prev.map((r) => (r.id === editingRule.id ? { ...r, ...data } : r)),
      );
      setEditingRule(null);
    } else {
      setRules((prev) => [...prev, { ...data, id: `wr${Date.now()}` }]);
    }
    setShowForm(false);
  };

  const handleDelete = () => {
    if (!deleteTarget) return;
    setRules((prev) => prev.filter((r) => r.id !== deleteTarget.id));
    setDeleteTarget(null);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Watch Rules</h3>
        {!showForm && !editingRule && (
          <Button size="sm" onClick={() => setShowForm(true)}>
            <Plus className="h-4 w-4" /> New Rule
          </Button>
        )}
      </div>

      {/* Create / Edit form */}
      {(showForm || editingRule) && (
        <RuleForm
          initial={editingRule ?? undefined}
          onSave={handleSave}
          onCancel={() => { setShowForm(false); setEditingRule(null); }}
        />
      )}

      {/* Rule list */}
      <div className="space-y-3">
        {rules.map((rule) => (
          <Card key={rule.id} className="flex items-center gap-4">
            {/* Toggle switch */}
            <button
              type="button"
              role="switch"
              aria-checked={rule.active}
              aria-label={`Toggle ${rule.name}`}
              onClick={() => toggleActive(rule.id)}
              className={clsx(
                "relative w-10 h-5 rounded-full shrink-0 transition-colors",
                rule.active ? "bg-success" : "bg-slate-300 dark:bg-slate-600",
              )}
            >
              <span
                className={clsx(
                  "absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform",
                  rule.active && "translate-x-5",
                )}
              />
            </button>

            {/* Info */}
            <div className="flex-1 min-w-0">
              <p className="font-medium text-sm">{rule.name}</p>
              <div className="flex flex-wrap items-center gap-1 mt-1">
                {rule.conditions.map((c, i) => (
                  <Badge key={i} variant="info">
                    {FIELDS.find((f) => f.value === c.field)?.label} {c.operator} &quot;{c.value}&quot;
                  </Badge>
                ))}
                <span className="text-xs text-slate-400 mx-1">→</span>
                {rule.channels.map((ch) => (
                  <Badge key={ch} variant="default">{ch}</Badge>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-1 shrink-0">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => { setEditingRule(rule); setShowForm(false); }}
                aria-label={`Edit ${rule.name}`}
              >
                <Pencil className="h-3.5 w-3.5" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setDeleteTarget(rule)}
                aria-label={`Delete ${rule.name}`}
              >
                <Trash2 className="h-3.5 w-3.5 text-danger" />
              </Button>
            </div>
          </Card>
        ))}
        {rules.length === 0 && (
          <Card>
            <p className="text-sm text-slate-500 text-center py-6">No watch rules configured.</p>
          </Card>
        )}
      </div>

      {/* Delete confirmation */}
      <Modal
        open={deleteTarget !== null}
        onClose={() => setDeleteTarget(null)}
        title="Delete Watch Rule"
      >
        <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
          Are you sure you want to delete <strong>{deleteTarget?.name}</strong>? This action cannot be undone.
        </p>
        <div className="flex items-center gap-2 justify-end">
          <Button variant="ghost" size="sm" onClick={() => setDeleteTarget(null)}>
            Cancel
          </Button>
          <Button variant="danger" size="sm" onClick={handleDelete}>
            Delete
          </Button>
        </div>
      </Modal>
    </div>
  );
}
