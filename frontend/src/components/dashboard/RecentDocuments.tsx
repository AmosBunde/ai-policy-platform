import { useNavigate } from "react-router-dom";
import { Badge } from "../ui/Badge";
import { Card } from "../ui/Card";

interface RecentDocument {
  id: string;
  title: string;
  jurisdiction: string;
  urgencyLevel: string;
  status: string;
  createdAt: string;
}

interface RecentDocumentsProps {
  documents: RecentDocument[];
  loading?: boolean;
}

function urgencyVariant(level: string): "danger" | "warning" | "info" | "success" | "default" {
  switch (level) {
    case "critical": return "danger";
    case "high": return "warning";
    case "normal": return "info";
    case "low": return "success";
    default: return "default";
  }
}

function statusVariant(status: string): "success" | "warning" | "danger" | "info" | "default" {
  switch (status) {
    case "enriched": return "success";
    case "processing": return "warning";
    case "failed": return "danger";
    case "ingested": return "info";
    default: return "default";
  }
}

function timeAgo(dateStr: string): string {
  const seconds = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

function TableSkeleton() {
  return (
    <Card>
      <div className="animate-pulse space-y-3">
        <div className="h-5 w-40 bg-slate-200 dark:bg-slate-700 rounded" />
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-10 bg-slate-100 dark:bg-slate-800 rounded" />
        ))}
      </div>
    </Card>
  );
}

export function RecentDocuments({ documents, loading }: RecentDocumentsProps) {
  const navigate = useNavigate();

  if (loading) return <TableSkeleton />;

  return (
    <Card>
      <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-4">
        Recent Documents
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-slate-500 border-b border-slate-200 dark:border-slate-700">
              <th className="pb-2 font-medium">Title</th>
              <th className="pb-2 font-medium">Jurisdiction</th>
              <th className="pb-2 font-medium">Urgency</th>
              <th className="pb-2 font-medium">Status</th>
              <th className="pb-2 font-medium text-right">Time</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((doc) => (
              <tr
                key={doc.id}
                onClick={() => navigate(`/documents/${doc.id}`)}
                className="border-b border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer transition-colors"
              >
                <td className="py-2.5 pr-4 font-medium text-slate-800 dark:text-slate-200 max-w-xs truncate">
                  {doc.title}
                </td>
                <td className="py-2.5 pr-4">
                  <Badge>{doc.jurisdiction}</Badge>
                </td>
                <td className="py-2.5 pr-4">
                  <Badge variant={urgencyVariant(doc.urgencyLevel)}>
                    {doc.urgencyLevel}
                  </Badge>
                </td>
                <td className="py-2.5 pr-4">
                  <Badge variant={statusVariant(doc.status)}>
                    {doc.status}
                  </Badge>
                </td>
                <td className="py-2.5 text-right text-xs text-slate-500">
                  {timeAgo(doc.createdAt)}
                </td>
              </tr>
            ))}
            {documents.length === 0 && (
              <tr>
                <td colSpan={5} className="py-8 text-center text-slate-400">
                  No documents found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
