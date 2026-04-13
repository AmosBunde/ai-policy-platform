import { Link } from "react-router-dom";
import { FileText, Calendar } from "lucide-react";
import { Badge } from "../ui/Badge";
import type { SearchResult } from "../../hooks/useSearch";

const URGENCY_VARIANT: Record<string, "danger" | "warning" | "info" | "default"> = {
  critical: "danger",
  high: "warning",
  normal: "info",
  low: "default",
};

/**
 * Safely render a snippet with highlights.
 *
 * Highlights from the API are plain text strings (no HTML tags).
 * We split the snippet on each highlight phrase and wrap matches in <mark>.
 * The rest of the text is rendered as plain text — no dangerouslySetInnerHTML.
 */
function HighlightedSnippet({
  snippet,
  highlights,
}: {
  snippet: string;
  highlights: string[];
}) {
  if (!highlights.length) {
    return <span>{snippet}</span>;
  }

  // Build a regex that matches any of the highlight phrases (case-insensitive)
  const escaped = highlights.map((h) =>
    h.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"),
  );
  const pattern = new RegExp(`(${escaped.join("|")})`, "gi");
  const parts = snippet.split(pattern);

  return (
    <span>
      {parts.map((part, i) => {
        const isHighlight = highlights.some(
          (h) => h.toLowerCase() === part.toLowerCase(),
        );
        return isHighlight ? (
          <mark
            key={i}
            className="bg-accent-50 text-accent-600 dark:bg-accent-900/30 dark:text-accent-400 px-0.5 rounded"
          >
            {part}
          </mark>
        ) : (
          <span key={i}>{part}</span>
        );
      })}
    </span>
  );
}

interface ResultCardProps {
  result: SearchResult;
}

export function ResultCard({ result }: ResultCardProps) {
  const urgencyVariant = URGENCY_VARIANT[result.urgency_level ?? ""] ?? "default";

  return (
    <div className="p-4 bg-white dark:bg-surface rounded-xl border border-slate-200 dark:border-slate-700 hover:shadow-md transition-shadow">
      <div className="flex items-start gap-3">
        <div className="p-2 rounded-lg bg-accent-50 text-accent-600 shrink-0 mt-0.5">
          <FileText className="h-4 w-4" />
        </div>
        <div className="flex-1 min-w-0">
          {/* Title */}
          <Link
            to={`/documents/${result.document_id}`}
            className="text-sm font-medium hover:text-accent transition-colors line-clamp-1"
          >
            {result.title}
          </Link>

          {/* Snippet with safe highlights */}
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400 line-clamp-2">
            <HighlightedSnippet
              snippet={result.snippet}
              highlights={result.highlights}
            />
          </p>

          {/* Metadata row */}
          <div className="mt-2 flex flex-wrap items-center gap-2">
            {result.jurisdiction && (
              <Badge variant="info">{result.jurisdiction}</Badge>
            )}
            {result.urgency_level && (
              <Badge variant={urgencyVariant}>{result.urgency_level}</Badge>
            )}
            {result.published_at && (
              <span className="flex items-center gap-1 text-xs text-slate-400">
                <Calendar className="h-3 w-3" />
                {new Date(result.published_at).toLocaleDateString()}
              </span>
            )}
            {/* Relevance score */}
            <span className="ml-auto text-xs text-slate-400">
              {Math.round(result.score * 100)}% match
            </span>
          </div>

          {/* Score bar */}
          <div className="mt-2 h-1 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-accent rounded-full transition-all"
              style={{ width: `${Math.round(result.score * 100)}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
