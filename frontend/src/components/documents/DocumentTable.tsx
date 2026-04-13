import { useNavigate } from "react-router-dom";
import { ArrowUpDown } from "lucide-react";
import { Badge } from "../ui/Badge";
import { StatusBadge } from "./StatusBadge";
import { clsx } from "clsx";

interface DocumentRow {
  id: string;
  title: string;
  jurisdiction: string;
  urgencyLevel: string;
  status: string;
  publishedAt: string | null;
}

interface DocumentTableProps {
  documents: DocumentRow[];
  selectedIds: Set<string>;
  onToggleSelect: (id: string) => void;
  onToggleSelectAll: () => void;
  sortField: string;
  sortDir: "asc" | "desc";
  onSort: (field: string) => void;
}

const urgencyVariant = (level: string) => {
  switch (level) {
    case "critical": return "danger" as const;
    case "high": return "warning" as const;
    case "normal": return "info" as const;
    default: return "success" as const;
  }
};

export function DocumentTable({
  documents, selectedIds, onToggleSelect, onToggleSelectAll, sortField, sortDir: _sortDir, onSort,
}: DocumentTableProps) {
  const navigate = useNavigate();
  const allSelected = documents.length > 0 && documents.every((d) => selectedIds.has(d.id));

  const SortHeader = ({ field, children }: { field: string; children: React.ReactNode }) => (
    <th
      className="pb-2 font-medium cursor-pointer select-none"
      onClick={() => onSort(field)}
    >
      <span className="inline-flex items-center gap-1">
        {children}
        <ArrowUpDown className={clsx("h-3 w-3", sortField === field ? "text-accent" : "text-slate-400")} />
      </span>
    </th>
  );

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-xs text-slate-500 border-b border-slate-200 dark:border-slate-700">
            <th className="pb-2 pr-2 w-8">
              <input
                type="checkbox"
                checked={allSelected}
                onChange={onToggleSelectAll}
                className="rounded border-slate-300"
                aria-label="Select all documents"
              />
            </th>
            <SortHeader field="title">Title</SortHeader>
            <SortHeader field="jurisdiction">Jurisdiction</SortHeader>
            <SortHeader field="urgencyLevel">Urgency</SortHeader>
            <th className="pb-2 font-medium">Status</th>
            <SortHeader field="publishedAt">Published</SortHeader>
          </tr>
        </thead>
        <tbody>
          {documents.map((doc) => (
            <tr
              key={doc.id}
              className="border-b border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
            >
              <td className="py-2.5 pr-2">
                <input
                  type="checkbox"
                  checked={selectedIds.has(doc.id)}
                  onChange={() => onToggleSelect(doc.id)}
                  className="rounded border-slate-300"
                  aria-label={`Select ${doc.title}`}
                />
              </td>
              <td
                className="py-2.5 pr-4 font-medium text-slate-800 dark:text-slate-200 max-w-xs truncate cursor-pointer hover:text-accent"
                onClick={() => navigate(`/documents/${doc.id}`)}
              >
                {doc.title}
              </td>
              <td className="py-2.5 pr-4"><Badge>{doc.jurisdiction}</Badge></td>
              <td className="py-2.5 pr-4"><Badge variant={urgencyVariant(doc.urgencyLevel)}>{doc.urgencyLevel}</Badge></td>
              <td className="py-2.5 pr-4"><StatusBadge status={doc.status} /></td>
              <td className="py-2.5 text-xs text-slate-500">{doc.publishedAt ?? "N/A"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
