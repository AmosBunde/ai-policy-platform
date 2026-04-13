import { useState } from "react";
import { ChevronDown, ChevronRight, X } from "lucide-react";
import type { FacetCounts } from "../../hooks/useSearch";

interface FacetPanelProps {
  facets: FacetCounts | undefined;
  selectedJurisdictions: Set<string>;
  selectedCategories: Set<string>;
  selectedUrgency: Set<string>;
  onToggleJurisdiction: (value: string) => void;
  onToggleCategory: (value: string) => void;
  onToggleUrgency: (value: string) => void;
  onClearAll: () => void;
}

function FacetGroup({
  title,
  items,
  selected,
  onToggle,
}: {
  title: string;
  items: { value: string; label: string; count: number }[];
  selected: Set<string>;
  onToggle: (value: string) => void;
}) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="border-b border-slate-100 dark:border-slate-700 pb-3">
      <button
        type="button"
        onClick={() => setCollapsed((c) => !c)}
        className="flex items-center justify-between w-full py-1.5 text-sm font-medium text-slate-700 dark:text-slate-300"
        aria-expanded={!collapsed}
      >
        {title}
        {collapsed ? (
          <ChevronRight className="h-4 w-4 text-slate-400" />
        ) : (
          <ChevronDown className="h-4 w-4 text-slate-400" />
        )}
      </button>
      {!collapsed && (
        <div className="space-y-1 mt-1">
          {items.map((item) => (
            <label
              key={item.value}
              className="flex items-center gap-2 py-0.5 cursor-pointer text-sm hover:bg-slate-50 dark:hover:bg-slate-800 rounded px-1 -mx-1"
            >
              <input
                type="checkbox"
                checked={selected.has(item.value)}
                onChange={() => onToggle(item.value)}
                className="rounded border-slate-300 text-accent focus:ring-accent/50"
              />
              <span className="flex-1 text-slate-600 dark:text-slate-400">{item.label}</span>
              <span className="text-xs text-slate-400">{item.count}</span>
            </label>
          ))}
        </div>
      )}
    </div>
  );
}

export function FacetPanel({
  facets,
  selectedJurisdictions,
  selectedCategories,
  selectedUrgency,
  onToggleJurisdiction,
  onToggleCategory,
  onToggleUrgency,
  onClearAll,
}: FacetPanelProps) {
  const hasFilters =
    selectedJurisdictions.size > 0 ||
    selectedCategories.size > 0 ||
    selectedUrgency.size > 0;

  if (!facets) return null;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300">Filters</h3>
        {hasFilters && (
          <button
            type="button"
            onClick={onClearAll}
            className="text-xs text-accent hover:underline flex items-center gap-1"
          >
            <X className="h-3 w-3" /> Clear all
          </button>
        )}
      </div>

      <FacetGroup
        title="Jurisdiction"
        items={facets.jurisdictions}
        selected={selectedJurisdictions}
        onToggle={onToggleJurisdiction}
      />
      <FacetGroup
        title="Category"
        items={facets.categories}
        selected={selectedCategories}
        onToggle={onToggleCategory}
      />
      <FacetGroup
        title="Urgency"
        items={facets.urgency}
        selected={selectedUrgency}
        onToggle={onToggleUrgency}
      />
    </div>
  );
}
