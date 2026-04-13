import { Eye, Download, Trash2, FileText, FileBarChart, FileSpreadsheet } from "lucide-react";
import { Card } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";

export interface Report {
  id: string;
  title: string;
  status: "draft" | "generating" | "completed" | "failed";
  template: "standard" | "executive" | "detailed";
  format: "pdf" | "docx";
  createdAt: string;
  documentCount: number;
}

const STATUS_VARIANT: Record<Report["status"], "default" | "warning" | "success" | "danger"> = {
  draft: "default",
  generating: "warning",
  completed: "success",
  failed: "danger",
};

const STATUS_LABEL: Record<Report["status"], string> = {
  draft: "Draft",
  generating: "Generating",
  completed: "Completed",
  failed: "Failed",
};

const TEMPLATE_ICON: Record<Report["template"], typeof FileText> = {
  standard: FileText,
  executive: FileBarChart,
  detailed: FileSpreadsheet,
};

const TEMPLATE_LABEL: Record<Report["template"], string> = {
  standard: "Standard",
  executive: "Executive",
  detailed: "Detailed",
};

interface ReportCardProps {
  report: Report;
  onView: (id: string) => void;
  onDownload: (id: string) => void;
  onDelete: (id: string) => void;
}

export function ReportCard({ report, onView, onDownload, onDelete }: ReportCardProps) {
  const Icon = TEMPLATE_ICON[report.template];

  return (
    <Card className="flex items-start gap-4">
      <div className="p-2 rounded-lg bg-accent-50 text-accent-600 shrink-0">
        <Icon className="h-5 w-5" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-medium text-sm truncate">{report.title}</h3>
          <Badge variant={STATUS_VARIANT[report.status]}>{STATUS_LABEL[report.status]}</Badge>
        </div>
        <div className="mt-1 flex items-center gap-3 text-xs text-slate-500">
          <span>{TEMPLATE_LABEL[report.template]} template</span>
          <span>{report.documentCount} doc{report.documentCount !== 1 ? "s" : ""}</span>
          <span>{new Date(report.createdAt).toLocaleDateString()}</span>
          <span className="uppercase">{report.format}</span>
        </div>
        <div className="mt-3 flex items-center gap-2">
          <Button size="sm" variant="ghost" onClick={() => onView(report.id)} aria-label="View report">
            <Eye className="h-3.5 w-3.5" /> View
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => onDownload(report.id)}
            disabled={report.status !== "completed"}
            aria-label="Download report"
          >
            <Download className="h-3.5 w-3.5" /> Download
          </Button>
          <Button size="sm" variant="ghost" onClick={() => onDelete(report.id)} aria-label="Delete report">
            <Trash2 className="h-3.5 w-3.5 text-danger" />
          </Button>
        </div>
      </div>
    </Card>
  );
}
