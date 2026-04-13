import { useState } from "react";
import { ChevronDown, ChevronRight, Copy, Check } from "lucide-react";
import { clsx } from "clsx";
import { Card } from "../ui/Card";
import { Badge } from "../ui/Badge";

interface Enrichment {
  summary: string;
  keyChanges: { change: string; affectedParties: string[] }[];
  classification: { domain: string; confidence: number }[];
  impactScores: { region: string; productCategory: string; score: number; justification: string }[];
  draftResponse: string | null;
  urgencyLevel: string;
  confidenceScore: number;
}

interface EnrichmentPanelProps {
  enrichment: Enrichment | null;
}

type TabId = "summary" | "changes" | "classification" | "impact" | "draft";

const TABS: { id: TabId; label: string }[] = [
  { id: "summary", label: "Summary" },
  { id: "changes", label: "Key Changes" },
  { id: "classification", label: "Classification" },
  { id: "impact", label: "Impact Matrix" },
  { id: "draft", label: "Draft Response" },
];

function ConfidenceBar({ domain, confidence }: { domain: string; confidence: number }) {
  const pct = Math.round(confidence * 100);
  return (
    <div className="flex items-center gap-3 py-1.5">
      <span className="text-xs w-28 text-slate-600 dark:text-slate-400 capitalize">{domain}</span>
      <div className="flex-1 h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
        <div
          className="h-full bg-accent rounded-full transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-medium w-10 text-right">{pct}%</span>
    </div>
  );
}

function ImpactCell({ score }: { score: number }) {
  const color = score >= 8 ? "bg-danger/80 text-white"
    : score >= 6 ? "bg-orange-400/70 text-white"
    : score >= 4 ? "bg-accent/60 text-navy-900"
    : score >= 2 ? "bg-amber-200/60 text-navy-900"
    : "bg-success/30 text-navy-900";

  return (
    <span className={clsx("inline-block px-2 py-0.5 rounded text-xs font-bold", color)}>
      {score}/10
    </span>
  );
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      // Fallback for older browsers
      const textarea = document.createElement("textarea");
      textarea.value = text;
      textarea.style.position = "fixed";
      textarea.style.opacity = "0";
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button
      onClick={handleCopy}
      className="flex items-center gap-1 text-xs text-accent hover:underline"
    >
      {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
      {copied ? "Copied!" : "Copy to clipboard"}
    </button>
  );
}

function KeyChangeAccordion({ change, affectedParties }: { change: string; affectedParties: string[] }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="border-b border-slate-100 dark:border-slate-800 last:border-0">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 w-full py-2 text-left text-sm"
      >
        {open ? <ChevronDown className="h-4 w-4 text-slate-400" /> : <ChevronRight className="h-4 w-4 text-slate-400" />}
        <span className="text-slate-700 dark:text-slate-300">{change}</span>
      </button>
      {open && affectedParties.length > 0 && (
        <div className="pl-6 pb-2">
          <p className="text-xs text-slate-500 mb-1">Affected parties:</p>
          <div className="flex flex-wrap gap-1">
            {affectedParties.map((p) => (
              <Badge key={p}>{p}</Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export function EnrichmentPanel({ enrichment }: EnrichmentPanelProps) {
  const [activeTab, setActiveTab] = useState<TabId>("summary");

  if (!enrichment) {
    return (
      <Card>
        <p className="text-slate-500 text-sm">No enrichment data available.</p>
      </Card>
    );
  }

  return (
    <Card>
      <div className="flex border-b border-slate-200 dark:border-slate-700 mb-4 overflow-x-auto">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={clsx(
              "px-4 py-2 text-sm font-medium whitespace-nowrap transition-colors border-b-2",
              activeTab === tab.id
                ? "border-accent text-accent"
                : "border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300",
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "summary" && (
        <div className="prose prose-sm dark:prose-invert max-w-none">
          <p className="text-slate-700 dark:text-slate-300 whitespace-pre-wrap">{enrichment.summary}</p>
        </div>
      )}

      {activeTab === "changes" && (
        <div>
          {enrichment.keyChanges.length === 0 && (
            <p className="text-sm text-slate-500">No key changes identified.</p>
          )}
          {enrichment.keyChanges.map((kc, i) => (
            <KeyChangeAccordion key={i} change={kc.change} affectedParties={kc.affectedParties} />
          ))}
        </div>
      )}

      {activeTab === "classification" && (
        <div className="space-y-1">
          {enrichment.classification.map((cls) => (
            <ConfidenceBar key={cls.domain} domain={cls.domain} confidence={cls.confidence} />
          ))}
        </div>
      )}

      {activeTab === "impact" && (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left text-slate-500 border-b border-slate-200 dark:border-slate-700">
                <th className="pb-2 font-medium">Region</th>
                <th className="pb-2 font-medium">Category</th>
                <th className="pb-2 font-medium">Score</th>
                <th className="pb-2 font-medium">Justification</th>
              </tr>
            </thead>
            <tbody>
              {enrichment.impactScores.map((is, i) => (
                <tr key={i} className="border-b border-slate-100 dark:border-slate-800">
                  <td className="py-2 pr-3">{is.region}</td>
                  <td className="py-2 pr-3">{is.productCategory}</td>
                  <td className="py-2 pr-3"><ImpactCell score={is.score} /></td>
                  <td className="py-2 text-slate-600 dark:text-slate-400">{is.justification}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === "draft" && (
        <div>
          {enrichment.draftResponse ? (
            <>
              <div className="flex justify-end mb-2">
                <CopyButton text={enrichment.draftResponse} />
              </div>
              <pre className="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap font-mono bg-slate-50 dark:bg-navy-900 p-4 rounded-lg border border-slate-200 dark:border-slate-700">
                {enrichment.draftResponse}
              </pre>
            </>
          ) : (
            <p className="text-sm text-slate-500">No draft response generated.</p>
          )}
        </div>
      )}
    </Card>
  );
}
