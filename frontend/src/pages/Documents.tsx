import { useState, useCallback } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { LayoutGrid, List, FileDown } from "lucide-react";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { FilterSidebar } from "../components/documents/FilterSidebar";
import { DocumentTable } from "../components/documents/DocumentTable";
import { DocumentCard } from "../components/documents/DocumentCard";
import { clsx } from "clsx";

type ViewMode = "table" | "card";

// Sample data for development
const SAMPLE_DOCS = [
  { id: "1", title: "EU AI Act - Final Implementation Guidelines", jurisdiction: "EU", urgencyLevel: "critical", status: "enriched", publishedAt: "2024-12-15", summary: "Comprehensive guidelines for AI Act compliance." },
  { id: "2", title: "NIST AI Risk Management Framework Update", jurisdiction: "US-Federal", urgencyLevel: "high", status: "enriched", publishedAt: "2024-11-20", summary: "Updated risk management framework." },
  { id: "3", title: "UK ICO AI and Data Protection Guidance", jurisdiction: "UK", urgencyLevel: "normal", status: "processing", publishedAt: "2024-10-05", summary: "Guidance on data protection for AI." },
  { id: "4", title: "Canada AIDA Bill Second Reading", jurisdiction: "Canada", urgencyLevel: "normal", status: "ingested", publishedAt: "2024-09-18", summary: null },
  { id: "5", title: "Singapore AI Governance Framework v2", jurisdiction: "APAC", urgencyLevel: "low", status: "enriched", publishedAt: "2024-08-30", summary: "Updated governance framework." },
];

export default function Documents() {
  const [_searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState<ViewMode>("table");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [sortField, setSortField] = useState("publishedAt");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const toggleSelect = useCallback((id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) { next.delete(id); } else { next.add(id); }
      return next;
    });
  }, []);

  const toggleSelectAll = useCallback(() => {
    setSelectedIds((prev) => {
      if (prev.size === SAMPLE_DOCS.length) return new Set();
      return new Set(SAMPLE_DOCS.map((d) => d.id));
    });
  }, []);

  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDir("asc");
    }
  };

  const handleGenerateReport = () => {
    const ids = Array.from(selectedIds).join(",");
    navigate(`/reports?document_ids=${ids}`);
  };

  return (
    <div className="flex gap-6">
      {/* Filter Sidebar */}
      <div className="w-56 shrink-0 hidden lg:block">
        <Card>
          <FilterSidebar />
        </Card>
      </div>

      {/* Main Content */}
      <div className="flex-1 space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Regulatory Documents</h1>
          <div className="flex items-center gap-3">
            {selectedIds.size > 0 && (
              <Button size="sm" onClick={handleGenerateReport}>
                <FileDown className="h-4 w-4" />
                Generate Report ({selectedIds.size})
              </Button>
            )}
            <div className="flex bg-slate-100 dark:bg-slate-800 rounded-lg overflow-hidden">
              <button
                onClick={() => setViewMode("table")}
                className={clsx("p-2", viewMode === "table" ? "bg-accent text-white" : "text-slate-500")}
                aria-label="Table view"
              >
                <List className="h-4 w-4" />
              </button>
              <button
                onClick={() => setViewMode("card")}
                className={clsx("p-2", viewMode === "card" ? "bg-accent text-white" : "text-slate-500")}
                aria-label="Card view"
              >
                <LayoutGrid className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>

        <Card>
          {viewMode === "table" ? (
            <DocumentTable
              documents={SAMPLE_DOCS}
              selectedIds={selectedIds}
              onToggleSelect={toggleSelect}
              onToggleSelectAll={toggleSelectAll}
              sortField={sortField}
              sortDir={sortDir}
              onSort={handleSort}
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {SAMPLE_DOCS.map((doc) => (
                <DocumentCard
                  key={doc.id}
                  id={doc.id}
                  title={doc.title}
                  jurisdiction={doc.jurisdiction}
                  urgencyLevel={doc.urgencyLevel}
                  status={doc.status}
                  summary={doc.summary ?? undefined}
                  selected={selectedIds.has(doc.id)}
                  onToggleSelect={() => toggleSelect(doc.id)}
                />
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
