import { useState, useMemo } from "react";
import { Check, Search, FileText, FileBarChart, FileSpreadsheet, ChevronRight, ChevronLeft } from "lucide-react";
import { clsx } from "clsx";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { Card } from "../ui/Card";

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface Document {
  id: string;
  title: string;
  jurisdiction: string;
  status: string;
}

export interface WizardResult {
  documentIds: string[];
  template: "standard" | "executive" | "detailed";
  title: string;
  audience: string;
  format: "pdf" | "docx";
}

interface ReportWizardProps {
  documents: Document[];
  initialDocumentIds?: string[];
  onGenerate: (result: WizardResult) => void;
  onCancel: () => void;
}

/* ------------------------------------------------------------------ */
/*  Step indicator                                                     */
/* ------------------------------------------------------------------ */

const STEPS = ["Select Documents", "Choose Template", "Configure", "Review"] as const;

function StepIndicator({ current }: { current: number }) {
  return (
    <nav aria-label="Wizard progress" className="flex items-center gap-2 mb-8">
      {STEPS.map((label, i) => (
        <div key={label} className="flex items-center gap-2">
          <div
            className={clsx(
              "flex items-center justify-center w-8 h-8 rounded-full text-xs font-semibold",
              i < current && "bg-success text-white",
              i === current && "bg-accent text-white",
              i > current && "bg-slate-200 dark:bg-slate-700 text-slate-500",
            )}
          >
            {i < current ? <Check className="h-4 w-4" /> : i + 1}
          </div>
          <span
            className={clsx(
              "text-sm hidden sm:inline",
              i === current ? "font-medium" : "text-slate-500",
            )}
          >
            {label}
          </span>
          {i < STEPS.length - 1 && (
            <ChevronRight className="h-4 w-4 text-slate-400 hidden sm:block" />
          )}
        </div>
      ))}
    </nav>
  );
}

/* ------------------------------------------------------------------ */
/*  Step 1 — Select documents                                         */
/* ------------------------------------------------------------------ */

function StepDocuments({
  documents,
  selectedIds,
  onToggle,
}: {
  documents: Document[];
  selectedIds: Set<string>;
  onToggle: (id: string) => void;
}) {
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    if (!query) return documents;
    const q = query.toLowerCase();
    return documents.filter(
      (d) =>
        d.title.toLowerCase().includes(q) ||
        d.jurisdiction.toLowerCase().includes(q),
    );
  }, [documents, query]);

  return (
    <div className="space-y-4">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
        <input
          type="text"
          placeholder="Search documents..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full pl-10 pr-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-navy-900 focus:outline-none focus:ring-2 focus:ring-accent/50"
          aria-label="Search documents"
        />
      </div>
      <p className="text-xs text-slate-500">{selectedIds.size} selected</p>
      <div className="max-h-64 overflow-y-auto space-y-1">
        {filtered.map((doc) => (
          <label
            key={doc.id}
            className={clsx(
              "flex items-center gap-3 p-2 rounded-lg cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800",
              selectedIds.has(doc.id) && "bg-accent-50 dark:bg-accent-900/20",
            )}
          >
            <input
              type="checkbox"
              checked={selectedIds.has(doc.id)}
              onChange={() => onToggle(doc.id)}
              className="rounded border-slate-300 text-accent focus:ring-accent/50"
            />
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium truncate">{doc.title}</p>
              <p className="text-xs text-slate-500">{doc.jurisdiction}</p>
            </div>
          </label>
        ))}
        {filtered.length === 0 && (
          <p className="text-sm text-slate-500 text-center py-4">No documents match your search.</p>
        )}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Step 2 — Choose template                                           */
/* ------------------------------------------------------------------ */

const TEMPLATES = [
  {
    id: "standard" as const,
    label: "Standard",
    description: "Balanced compliance report with key findings and recommendations.",
    icon: FileText,
  },
  {
    id: "executive" as const,
    label: "Executive",
    description: "High-level summary for leadership with risk scores and action items.",
    icon: FileBarChart,
  },
  {
    id: "detailed" as const,
    label: "Detailed",
    description: "Comprehensive analysis with full regulatory text and impact assessments.",
    icon: FileSpreadsheet,
  },
] as const;

function StepTemplate({
  selected,
  onSelect,
}: {
  selected: WizardResult["template"];
  onSelect: (t: WizardResult["template"]) => void;
}) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
      {TEMPLATES.map((t) => {
        const Icon = t.icon;
        const active = selected === t.id;
        return (
          <button
            key={t.id}
            type="button"
            onClick={() => onSelect(t.id)}
            className={clsx(
              "text-left rounded-xl border-2 p-5 transition-colors",
              active
                ? "border-accent bg-accent-50 dark:bg-accent-900/20"
                : "border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600",
            )}
          >
            <Icon className={clsx("h-8 w-8 mb-3", active ? "text-accent" : "text-slate-400")} />
            <h4 className="font-medium text-sm">{t.label}</h4>
            <p className="text-xs text-slate-500 mt-1">{t.description}</p>
          </button>
        );
      })}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Step 3 — Configure                                                 */
/* ------------------------------------------------------------------ */

function StepConfigure({
  title,
  audience,
  format,
  onChangeTitle,
  onChangeAudience,
  onChangeFormat,
  errors,
}: {
  title: string;
  audience: string;
  format: "pdf" | "docx";
  onChangeTitle: (v: string) => void;
  onChangeAudience: (v: string) => void;
  onChangeFormat: (v: "pdf" | "docx") => void;
  errors: { title?: string };
}) {
  return (
    <div className="space-y-4 max-w-md">
      <Input
        label="Report Title"
        value={title}
        onChange={(e) => onChangeTitle(e.target.value)}
        placeholder="e.g. Q1 2025 EU AI Act Compliance Report"
        error={errors.title}
      />
      <div className="space-y-1">
        <label htmlFor="audience-select" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
          Audience
        </label>
        <select
          id="audience-select"
          value={audience}
          onChange={(e) => onChangeAudience(e.target.value)}
          className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-navy-900 focus:outline-none focus:ring-2 focus:ring-accent/50"
        >
          <option value="internal">Internal Team</option>
          <option value="executive">Executive Leadership</option>
          <option value="board">Board of Directors</option>
          <option value="regulator">Regulator / Auditor</option>
        </select>
      </div>
      <div className="space-y-1">
        <span className="block text-sm font-medium text-slate-700 dark:text-slate-300">Format</span>
        <div className="flex gap-3">
          {(["pdf", "docx"] as const).map((f) => (
            <button
              key={f}
              type="button"
              onClick={() => onChangeFormat(f)}
              className={clsx(
                "px-4 py-2 rounded-lg text-sm font-medium border-2 transition-colors uppercase",
                format === f
                  ? "border-accent bg-accent-50 text-accent-600 dark:bg-accent-900/20"
                  : "border-slate-200 dark:border-slate-700 text-slate-500 hover:border-slate-300",
              )}
            >
              {f}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Step 4 — Review                                                    */
/* ------------------------------------------------------------------ */

function StepReview({
  result,
  documentCount,
}: {
  result: WizardResult;
  documentCount: number;
}) {
  return (
    <Card className="max-w-md space-y-3">
      <h4 className="font-medium text-sm text-slate-500 uppercase tracking-wide">Review</h4>
      <dl className="space-y-2 text-sm">
        <div className="flex justify-between">
          <dt className="text-slate-500">Title</dt>
          <dd className="font-medium">{result.title}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-slate-500">Documents</dt>
          <dd className="font-medium">{documentCount}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-slate-500">Template</dt>
          <dd className="font-medium capitalize">{result.template}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-slate-500">Audience</dt>
          <dd className="font-medium capitalize">{result.audience}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-slate-500">Format</dt>
          <dd className="font-medium uppercase">{result.format}</dd>
        </div>
      </dl>
    </Card>
  );
}

/* ------------------------------------------------------------------ */
/*  Main Wizard                                                        */
/* ------------------------------------------------------------------ */

export function ReportWizard({ documents, initialDocumentIds = [], onGenerate, onCancel }: ReportWizardProps) {
  const [step, setStep] = useState(0);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(() => new Set(initialDocumentIds));
  const [template, setTemplate] = useState<WizardResult["template"]>("standard");
  const [title, setTitle] = useState("");
  const [audience, setAudience] = useState("internal");
  const [format, setFormat] = useState<"pdf" | "docx">("pdf");
  const [errors, setErrors] = useState<{ title?: string }>({});

  const toggleDoc = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const canAdvance = (): boolean => {
    if (step === 0) return selectedIds.size > 0;
    if (step === 2) {
      if (!title.trim()) {
        setErrors({ title: "Report title is required" });
        return false;
      }
      setErrors({});
    }
    return true;
  };

  const handleNext = () => {
    if (!canAdvance()) return;
    setStep((s) => Math.min(s + 1, STEPS.length - 1));
  };

  const handleBack = () => setStep((s) => Math.max(s - 1, 0));

  const result: WizardResult = {
    documentIds: Array.from(selectedIds),
    template,
    title,
    audience,
    format,
  };

  return (
    <div>
      <StepIndicator current={step} />

      <div className="min-h-[280px]">
        {step === 0 && (
          <StepDocuments documents={documents} selectedIds={selectedIds} onToggle={toggleDoc} />
        )}
        {step === 1 && <StepTemplate selected={template} onSelect={setTemplate} />}
        {step === 2 && (
          <StepConfigure
            title={title}
            audience={audience}
            format={format}
            onChangeTitle={setTitle}
            onChangeAudience={setAudience}
            onChangeFormat={setFormat}
            errors={errors}
          />
        )}
        {step === 3 && <StepReview result={result} documentCount={selectedIds.size} />}
      </div>

      <div className="mt-6 flex items-center justify-between border-t border-slate-200 dark:border-slate-700 pt-4">
        <div>
          {step > 0 ? (
            <Button variant="ghost" onClick={handleBack}>
              <ChevronLeft className="h-4 w-4" /> Back
            </Button>
          ) : (
            <Button variant="ghost" onClick={onCancel}>
              Cancel
            </Button>
          )}
        </div>
        <div>
          {step < STEPS.length - 1 ? (
            <Button onClick={handleNext} disabled={step === 0 && selectedIds.size === 0}>
              Next <ChevronRight className="h-4 w-4" />
            </Button>
          ) : (
            <Button onClick={() => onGenerate(result)}>Generate Report</Button>
          )}
        </div>
      </div>
    </div>
  );
}
