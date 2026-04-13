import { Badge } from "../ui/Badge";

const STATUS_MAP: Record<string, { variant: "info" | "warning" | "success" | "danger" | "default"; label: string }> = {
  ingested: { variant: "info", label: "Ingested" },
  processing: { variant: "warning", label: "Processing" },
  enriched: { variant: "success", label: "Enriched" },
  failed: { variant: "danger", label: "Failed" },
  archived: { variant: "default", label: "Archived" },
};

interface StatusBadgeProps {
  status: string;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const config = STATUS_MAP[status] ?? { variant: "default" as const, label: status };
  return <Badge variant={config.variant}>{config.label}</Badge>;
}
