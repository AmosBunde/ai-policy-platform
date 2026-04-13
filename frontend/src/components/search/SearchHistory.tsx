import { Clock, X } from "lucide-react";
import { getSearchHistory, clearSearchHistory } from "../../hooks/useSearch";

interface SearchHistoryProps {
  onSelect: (query: string) => void;
}

export function SearchHistory({ onSelect }: SearchHistoryProps) {
  const history = getSearchHistory();

  if (history.length === 0) return null;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-medium text-slate-500 uppercase tracking-wide">
          Recent Searches
        </h4>
        <button
          type="button"
          onClick={clearSearchHistory}
          className="text-xs text-accent hover:underline flex items-center gap-1"
        >
          <X className="h-3 w-3" /> Clear
        </button>
      </div>
      <div className="flex flex-wrap gap-2">
        {history.slice(0, 10).map((query, i) => (
          <button
            key={`${query}-${i}`}
            type="button"
            onClick={() => onSelect(query)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
          >
            <Clock className="h-3 w-3 text-slate-400" />
            {query}
          </button>
        ))}
      </div>
    </div>
  );
}
