import { useSearchParams } from "react-router-dom";
import { X } from "lucide-react";
import { Select } from "../ui/Select";
import { Input } from "../ui/Input";

const JURISDICTIONS = [
  { value: "", label: "All Jurisdictions" },
  { value: "EU", label: "EU" },
  { value: "US-Federal", label: "US Federal" },
  { value: "UK", label: "UK" },
  { value: "APAC", label: "APAC" },
  { value: "Canada", label: "Canada" },
];

const STATUSES = [
  { value: "", label: "All Statuses" },
  { value: "ingested", label: "Ingested" },
  { value: "processing", label: "Processing" },
  { value: "enriched", label: "Enriched" },
  { value: "failed", label: "Failed" },
];

const URGENCY_LEVELS = [
  { value: "", label: "All Urgency" },
  { value: "critical", label: "Critical" },
  { value: "high", label: "High" },
  { value: "normal", label: "Normal" },
  { value: "low", label: "Low" },
];

const CATEGORIES = [
  { value: "", label: "All Categories" },
  { value: "privacy", label: "Privacy" },
  { value: "safety", label: "Safety" },
  { value: "intellectual_property", label: "IP" },
  { value: "antitrust", label: "Antitrust" },
  { value: "transparency", label: "Transparency" },
  { value: "liability", label: "Liability" },
];

export function FilterSidebar() {
  const [searchParams, setSearchParams] = useSearchParams();

  const setFilter = (key: string, value: string) => {
    const next = new URLSearchParams(searchParams);
    if (value) {
      next.set(key, value);
    } else {
      next.delete(key);
    }
    next.set("page", "1");
    setSearchParams(next);
  };

  const clearAll = () => {
    setSearchParams({});
  };

  const hasFilters = Array.from(searchParams.entries()).some(
    ([k]) => ["jurisdiction", "status", "urgency", "category", "date_from", "date_to"].includes(k),
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300">Filters</h3>
        {hasFilters && (
          <button onClick={clearAll} className="text-xs text-accent hover:underline flex items-center gap-1">
            <X className="h-3 w-3" /> Clear
          </button>
        )}
      </div>
      <Select
        label="Jurisdiction"
        options={JURISDICTIONS}
        value={searchParams.get("jurisdiction") ?? ""}
        onChange={(e) => setFilter("jurisdiction", e.target.value)}
      />
      <Select
        label="Category"
        options={CATEGORIES}
        value={searchParams.get("category") ?? ""}
        onChange={(e) => setFilter("category", e.target.value)}
      />
      <Select
        label="Status"
        options={STATUSES}
        value={searchParams.get("status") ?? ""}
        onChange={(e) => setFilter("status", e.target.value)}
      />
      <Select
        label="Urgency"
        options={URGENCY_LEVELS}
        value={searchParams.get("urgency") ?? ""}
        onChange={(e) => setFilter("urgency", e.target.value)}
      />
      <Input
        label="From Date"
        type="date"
        value={searchParams.get("date_from") ?? ""}
        onChange={(e) => setFilter("date_from", e.target.value)}
      />
      <Input
        label="To Date"
        type="date"
        value={searchParams.get("date_to") ?? ""}
        onChange={(e) => setFilter("date_to", e.target.value)}
      />
    </div>
  );
}
