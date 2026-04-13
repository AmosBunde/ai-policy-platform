import { useState, useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import { Plus, Filter } from "lucide-react";
import { clsx } from "clsx";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { ReportCard, type Report } from "../components/reports/ReportCard";
import { ReportWizard, type WizardResult } from "../components/reports/ReportWizard";
import { ReportPreview } from "../components/reports/ReportPreview";

/* ------------------------------------------------------------------ */
/*  Sample data                                                        */
/* ------------------------------------------------------------------ */

const SAMPLE_DOCS = [
  { id: "1", title: "EU AI Act - Final Implementation Guidelines", jurisdiction: "EU", status: "enriched" },
  { id: "2", title: "NIST AI Risk Management Framework Update", jurisdiction: "US-Federal", status: "enriched" },
  { id: "3", title: "UK ICO AI and Data Protection Guidance", jurisdiction: "UK", status: "processing" },
  { id: "4", title: "Canada AIDA Bill Second Reading", jurisdiction: "Canada", status: "ingested" },
  { id: "5", title: "Singapore AI Governance Framework v2", jurisdiction: "APAC", status: "enriched" },
];

const SAMPLE_REPORTS: Report[] = [
  { id: "r1", title: "Q4 2024 EU AI Compliance Report", status: "completed", template: "executive", format: "pdf", createdAt: "2024-12-20T10:00:00Z", documentCount: 3 },
  { id: "r2", title: "NIST Framework Gap Analysis", status: "completed", template: "detailed", format: "docx", createdAt: "2024-12-18T14:30:00Z", documentCount: 1 },
  { id: "r3", title: "Multi-Jurisdiction Risk Overview", status: "generating", template: "standard", format: "pdf", createdAt: "2024-12-22T09:15:00Z", documentCount: 5 },
  { id: "r4", title: "UK Data Protection Audit", status: "draft", template: "standard", format: "pdf", createdAt: "2024-12-10T16:45:00Z", documentCount: 2 },
  { id: "r5", title: "Board Compliance Summary Q3", status: "failed", template: "executive", format: "pdf", createdAt: "2024-11-30T08:00:00Z", documentCount: 4 },
];

/* ------------------------------------------------------------------ */
/*  Filters                                                            */
/* ------------------------------------------------------------------ */

type StatusFilter = "all" | Report["status"];
type TemplateFilter = "all" | Report["template"];
type DateFilter = "all" | "7d" | "30d" | "90d";

function matchesDateFilter(createdAt: string, filter: DateFilter): boolean {
  if (filter === "all") return true;
  const days = filter === "7d" ? 7 : filter === "30d" ? 30 : 90;
  const cutoff = Date.now() - days * 24 * 60 * 60 * 1000;
  return new Date(createdAt).getTime() >= cutoff;
}

/* ------------------------------------------------------------------ */
/*  Page                                                               */
/* ------------------------------------------------------------------ */

export default function Reports() {
  const [searchParams] = useSearchParams();
  const preselectedDocIds = searchParams.get("document_ids")?.split(",").filter(Boolean) ?? [];

  const [reports, setReports] = useState<Report[]>(SAMPLE_REPORTS);
  const [showWizard, setShowWizard] = useState(preselectedDocIds.length > 0);
  const [previewId, setPreviewId] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [templateFilter, setTemplateFilter] = useState<TemplateFilter>("all");
  const [dateFilter, setDateFilter] = useState<DateFilter>("all");
  const [showFilters, setShowFilters] = useState(false);

  const filtered = useMemo(() => {
    return reports.filter((r) => {
      if (statusFilter !== "all" && r.status !== statusFilter) return false;
      if (templateFilter !== "all" && r.template !== templateFilter) return false;
      if (!matchesDateFilter(r.createdAt, dateFilter)) return false;
      return true;
    });
  }, [reports, statusFilter, templateFilter, dateFilter]);

  const previewReport = previewId ? reports.find((r) => r.id === previewId) ?? null : null;

  /* Handlers */
  const handleGenerate = (result: WizardResult) => {
    const newReport: Report = {
      id: `r${Date.now()}`,
      title: result.title,
      status: "generating",
      template: result.template,
      format: result.format,
      createdAt: new Date().toISOString(),
      documentCount: result.documentIds.length,
    };
    setReports((prev) => [newReport, ...prev]);
    setShowWizard(false);
  };

  const handleDelete = (id: string) => {
    setReports((prev) => prev.filter((r) => r.id !== id));
    if (previewId === id) setPreviewId(null);
  };

  const handleDownload = (id: string) => {
    const report = reports.find((r) => r.id === id);
    if (!report || report.status !== "completed") return;
    // In production this would open a validated URL in a new tab
    window.open(`/api/reports/${encodeURIComponent(id)}/download?format=${report.format}`, "_blank", "noopener,noreferrer");
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Compliance Reports</h1>
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowFilters((v) => !v)}
            aria-label="Toggle filters"
          >
            <Filter className="h-4 w-4" />
            Filters
          </Button>
          <Button size="sm" onClick={() => setShowWizard(true)}>
            <Plus className="h-4 w-4" /> New Report
          </Button>
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <Card className="flex flex-wrap items-center gap-4">
          <div className="space-y-1">
            <label htmlFor="status-filter" className="text-xs font-medium text-slate-500">Status</label>
            <select
              id="status-filter"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
              className="block px-3 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-navy-900"
            >
              <option value="all">All</option>
              <option value="draft">Draft</option>
              <option value="generating">Generating</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
            </select>
          </div>
          <div className="space-y-1">
            <label htmlFor="template-filter" className="text-xs font-medium text-slate-500">Template</label>
            <select
              id="template-filter"
              value={templateFilter}
              onChange={(e) => setTemplateFilter(e.target.value as TemplateFilter)}
              className="block px-3 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-navy-900"
            >
              <option value="all">All</option>
              <option value="standard">Standard</option>
              <option value="executive">Executive</option>
              <option value="detailed">Detailed</option>
            </select>
          </div>
          <div className="space-y-1">
            <label htmlFor="date-filter" className="text-xs font-medium text-slate-500">Date</label>
            <select
              id="date-filter"
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value as DateFilter)}
              className="block px-3 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-navy-900"
            >
              <option value="all">All time</option>
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="90d">Last 90 days</option>
            </select>
          </div>
        </Card>
      )}

      {/* Wizard */}
      {showWizard && (
        <Card>
          <ReportWizard
            documents={SAMPLE_DOCS}
            initialDocumentIds={preselectedDocIds}
            onGenerate={handleGenerate}
            onCancel={() => setShowWizard(false)}
          />
        </Card>
      )}

      {/* Main content area */}
      <div className={clsx("grid gap-6", previewId ? "grid-cols-1 lg:grid-cols-2" : "grid-cols-1")}>
        {/* Report list */}
        <div className="space-y-3">
          {filtered.length === 0 && (
            <Card>
              <p className="text-sm text-slate-500 text-center py-8">No reports match your filters.</p>
            </Card>
          )}
          {filtered.map((report) => (
            <ReportCard
              key={report.id}
              report={report}
              onView={(id) => setPreviewId(id)}
              onDownload={handleDownload}
              onDelete={handleDelete}
            />
          ))}
        </div>

        {/* Preview panel */}
        {previewId && (
          <Card>
            <ReportPreview
              report={previewReport}
              onDownloadPdf={() => {
                if (previewReport) {
                  window.open(`/api/reports/${encodeURIComponent(previewReport.id)}/download?format=pdf`, "_blank", "noopener,noreferrer");
                }
              }}
              onDownloadDocx={() => {
                if (previewReport) {
                  window.open(`/api/reports/${encodeURIComponent(previewReport.id)}/download?format=docx`, "_blank", "noopener,noreferrer");
                }
              }}
              onClose={() => setPreviewId(null)}
            />
          </Card>
        )}
      </div>
    </div>
  );
}
