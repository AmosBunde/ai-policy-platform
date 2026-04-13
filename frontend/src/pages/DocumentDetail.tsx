import { useParams, Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { StatusBadge } from "../components/documents/StatusBadge";
import { EnrichmentPanel } from "../components/documents/EnrichmentPanel";

// Sample data
const SAMPLE_DOC = {
  id: "1",
  title: "EU AI Act - Final Implementation Guidelines",
  content: "The European Union's AI Act establishes a comprehensive regulatory framework for artificial intelligence systems. This regulation classifies AI systems by risk level and imposes requirements proportional to that risk. High-risk AI systems must undergo conformity assessments, maintain documentation, and ensure human oversight. The Act introduces new obligations for general-purpose AI models and foundation models.",
  jurisdiction: "EU",
  documentType: "regulation",
  status: "enriched",
  publishedAt: "2024-12-15",
  url: "https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai",
};

const SAMPLE_ENRICHMENT = {
  summary: "The EU AI Act establishes a risk-based regulatory framework for AI systems. It classifies AI into four risk tiers (unacceptable, high, limited, minimal) and introduces mandatory requirements for high-risk systems including conformity assessments, transparency obligations, and human oversight provisions. General-purpose AI models face additional obligations around documentation and systemic risk management.",
  keyChanges: [
    { change: "Mandatory conformity assessments for high-risk AI systems", affectedParties: ["AI developers", "Deployers", "Notified bodies"] },
    { change: "Transparency obligations for AI-generated content", affectedParties: ["AI providers", "Content platforms"] },
    { change: "Prohibition of social scoring and real-time biometric identification", affectedParties: ["Government agencies", "Law enforcement"] },
    { change: "Foundation model disclosure requirements", affectedParties: ["Foundation model providers", "Downstream deployers"] },
  ],
  classification: [
    { domain: "safety", confidence: 0.95 },
    { domain: "transparency", confidence: 0.88 },
    { domain: "liability", confidence: 0.72 },
    { domain: "privacy", confidence: 0.65 },
  ],
  impactScores: [
    { region: "EU", productCategory: "Enterprise AI", score: 10, justification: "Direct regulatory mandate" },
    { region: "EU", productCategory: "Healthcare AI", score: 9, justification: "High-risk classification" },
    { region: "US-Federal", productCategory: "Enterprise AI", score: 5, justification: "Extraterritorial effect" },
    { region: "UK", productCategory: "Enterprise AI", score: 6, justification: "Expected alignment" },
  ],
  draftResponse: "We acknowledge the European Union's AI Act and its implications for our organization. Based on our analysis, several of our AI systems fall within the high-risk classification, requiring conformity assessments and enhanced documentation.\n\nRecommended actions:\n1. Conduct inventory of all AI systems and classify by risk tier (Q1 2025)\n2. Implement conformity assessment procedures for high-risk systems (Q2 2025)\n3. Update transparency disclosures for AI-generated content (Q1 2025)\n4. Establish governance framework for foundation model usage (Q2 2025)\n\nEstimated resource requirement: 3 FTEs for 12 months.",
  urgencyLevel: "critical",
  confidenceScore: 0.92,
};

export default function DocumentDetail() {
  const { id: _id } = useParams<{ id: string }>();

  const urgencyVariant = (level: string) => {
    switch (level) {
      case "critical": return "danger" as const;
      case "high": return "warning" as const;
      default: return "info" as const;
    }
  };

  return (
    <div className="space-y-6">
      <Link to="/documents" className="flex items-center gap-1 text-sm text-accent hover:underline">
        <ArrowLeft className="h-4 w-4" /> Back to Documents
      </Link>

      <Card>
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-xl font-bold text-slate-800 dark:text-slate-200">
              {SAMPLE_DOC.title}
            </h1>
            <div className="flex items-center gap-2 mt-2">
              <Badge>{SAMPLE_DOC.jurisdiction}</Badge>
              <Badge variant={urgencyVariant(SAMPLE_ENRICHMENT.urgencyLevel)}>
                {SAMPLE_ENRICHMENT.urgencyLevel}
              </Badge>
              <StatusBadge status={SAMPLE_DOC.status} />
              <span className="text-xs text-slate-500">Published: {SAMPLE_DOC.publishedAt}</span>
            </div>
          </div>
        </div>

        {/* Document content rendered as plain text (security: no HTML injection) */}
        <div className="prose prose-sm dark:prose-invert max-w-none">
          <h3 className="text-sm font-semibold text-slate-600 dark:text-slate-400 mb-2">Document Content</h3>
          <p className="text-slate-700 dark:text-slate-300 whitespace-pre-wrap">
            {SAMPLE_DOC.content}
          </p>
        </div>
      </Card>

      <h2 className="text-lg font-semibold">AI Enrichment</h2>
      <EnrichmentPanel enrichment={SAMPLE_ENRICHMENT} />
    </div>
  );
}
