import { useNavigate } from "react-router-dom";
import { Card } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { StatusBadge } from "./StatusBadge";

interface DocumentCardProps {
  id: string;
  title: string;
  jurisdiction: string;
  urgencyLevel: string;
  status: string;
  summary?: string;
  selected: boolean;
  onToggleSelect: () => void;
}

const urgencyVariant = (level: string) => {
  switch (level) {
    case "critical": return "danger" as const;
    case "high": return "warning" as const;
    case "normal": return "info" as const;
    default: return "success" as const;
  }
};

export function DocumentCard({
  id, title, jurisdiction, urgencyLevel, status, summary, selected, onToggleSelect,
}: DocumentCardProps) {
  const navigate = useNavigate();

  return (
    <Card className="relative hover:ring-1 hover:ring-accent/50 transition-all">
      <div className="absolute top-4 right-4">
        <input
          type="checkbox"
          checked={selected}
          onChange={onToggleSelect}
          className="rounded border-slate-300"
          aria-label={`Select ${title}`}
        />
      </div>
      <div
        className="cursor-pointer"
        onClick={() => navigate(`/documents/${id}`)}
      >
        <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200 pr-8 line-clamp-2">
          {title}
        </h3>
        {summary && (
          <p className="text-xs text-slate-500 mt-2 line-clamp-3">{summary}</p>
        )}
        <div className="flex flex-wrap gap-2 mt-3">
          <Badge>{jurisdiction}</Badge>
          <Badge variant={urgencyVariant(urgencyLevel)}>{urgencyLevel}</Badge>
          <StatusBadge status={status} />
        </div>
      </div>
    </Card>
  );
}
