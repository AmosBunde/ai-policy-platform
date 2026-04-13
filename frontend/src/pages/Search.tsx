import { useState, useEffect, useCallback, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import { Filter, SearchIcon, Sparkles } from "lucide-react";
import { clsx } from "clsx";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Spinner } from "../components/ui/Spinner";
import { SearchInput } from "../components/search/SearchInput";
import { FacetPanel } from "../components/search/FacetPanel";
import { ResultCard } from "../components/search/ResultCard";
import { SearchHistory } from "../components/search/SearchHistory";
import {
  useSearchDocuments,
  useSearchFacets,
  addSearchHistory,
  sanitizeSearchInput,
  type SearchResponse,
} from "../hooks/useSearch";

type SearchType = "keyword" | "semantic" | "hybrid";

function toggleSet(set: Set<string>, value: string): Set<string> {
  const next = new Set(set);
  if (next.has(value)) next.delete(value);
  else next.add(value);
  return next;
}

export default function Search() {
  const [searchParams, setSearchParams] = useSearchParams();
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Read state from URL
  const urlQuery = searchParams.get("q") ?? "";
  const urlType = (searchParams.get("type") as SearchType) || "hybrid";
  const urlPage = parseInt(searchParams.get("page") ?? "1", 10);
  const urlJurisdictions = new Set(
    searchParams.get("jurisdiction")?.split(",").filter(Boolean) ?? [],
  );
  const urlCategories = new Set(
    searchParams.get("category")?.split(",").filter(Boolean) ?? [],
  );
  const urlUrgency = new Set(
    searchParams.get("urgency")?.split(",").filter(Boolean) ?? [],
  );

  // Local state
  const [searchType, setSearchType] = useState<SearchType>(urlType);
  const [jurisdictions, setJurisdictions] = useState<Set<string>>(urlJurisdictions);
  const [categories, setCategories] = useState<Set<string>>(urlCategories);
  const [urgency, setUrgency] = useState<Set<string>>(urlUrgency);
  const [page, setPage] = useState(urlPage);
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [showMobileFacets, setShowMobileFacets] = useState(false);

  const searchMutation = useSearchDocuments();
  const { data: facets } = useSearchFacets();

  // Sync URL params when filters change
  const updateUrl = useCallback(
    (query: string, type: SearchType, p: number, j: Set<string>, c: Set<string>, u: Set<string>) => {
      const params = new URLSearchParams();
      if (query) params.set("q", query);
      if (type !== "hybrid") params.set("type", type);
      if (p > 1) params.set("page", String(p));
      if (j.size) params.set("jurisdiction", Array.from(j).join(","));
      if (c.size) params.set("category", Array.from(c).join(","));
      if (u.size) params.set("urgency", Array.from(u).join(","));
      setSearchParams(params, { replace: true });
    },
    [setSearchParams],
  );

  // Execute search
  const executeSearch = useCallback(
    (query: string, p = 1) => {
      const sanitized = sanitizeSearchInput(query);
      if (!sanitized) return;

      addSearchHistory(sanitized);
      setPage(p);
      updateUrl(sanitized, searchType, p, jurisdictions, categories, urgency);

      searchMutation.mutate(
        {
          query: sanitized,
          search_type: searchType,
          jurisdiction: jurisdictions.size === 1 ? Array.from(jurisdictions)[0] : undefined,
          category: categories.size === 1 ? Array.from(categories)[0] : undefined,
          urgency_level: urgency.size === 1 ? Array.from(urgency)[0] : undefined,
          page: p,
          page_size: 20,
        },
        {
          onSuccess: (data) => setResults(data),
        },
      );
    },
    [searchType, jurisdictions, categories, urgency, searchMutation, updateUrl],
  );

  // Run search on mount if URL has query
  useEffect(() => {
    if (urlQuery) {
      executeSearch(urlQuery, urlPage);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Re-search when facets change (if there's a query)
  const handleFacetChange = useCallback(
    (newJ: Set<string>, newC: Set<string>, newU: Set<string>) => {
      setJurisdictions(newJ);
      setCategories(newC);
      setUrgency(newU);

      if (urlQuery || results) {
        const q = urlQuery || results?.query || "";
        if (q) {
          updateUrl(q, searchType, 1, newJ, newC, newU);
          setPage(1);
          searchMutation.mutate(
            {
              query: q,
              search_type: searchType,
              jurisdiction: newJ.size === 1 ? Array.from(newJ)[0] : undefined,
              category: newC.size === 1 ? Array.from(newC)[0] : undefined,
              urgency_level: newU.size === 1 ? Array.from(newU)[0] : undefined,
              page: 1,
              page_size: 20,
            },
            {
              onSuccess: (data) => setResults(data),
            },
          );
        }
      }
    },
    [urlQuery, results, searchType, searchMutation, updateUrl],
  );

  const handleLoadMore = () => {
    const nextPage = page + 1;
    executeSearch(results?.query ?? urlQuery, nextPage);
  };

  const clearAllFacets = () => {
    handleFacetChange(new Set(), new Set(), new Set());
  };

  const hasQuery = !!urlQuery || !!results;
  const isLoading = searchMutation.isPending;
  const totalResults = results?.total ?? 0;
  const shownResults = results?.results.length ?? 0;

  return (
    <div className="space-y-6">
      {/* Search header */}
      <div className={clsx("transition-all", !hasQuery && "pt-12 pb-8")}>
        <div className={clsx("text-center mb-6", hasQuery && "hidden")}>
          <h1 className="text-3xl font-bold mb-2">Search Regulatory Documents</h1>
          <p className="text-slate-500">
            Search across regulatory documents using keyword, semantic, or hybrid search.
          </p>
        </div>

        <SearchInput
          value={urlQuery}
          searchType={searchType}
          onSearch={(q) => executeSearch(q)}
          onSearchTypeChange={(t) => {
            setSearchType(t);
            if (results?.query) {
              updateUrl(results.query, t, 1, jurisdictions, categories, urgency);
            }
          }}
          inputRef={searchInputRef}
        />

        {/* Search history (shown when no query) */}
        {!hasQuery && (
          <div className="max-w-3xl mx-auto mt-6">
            <SearchHistory onSelect={(q) => executeSearch(q)} />
          </div>
        )}
      </div>

      {/* Empty state with suggestions */}
      {!hasQuery && !isLoading && (
        <Card variant="glass" className="max-w-3xl mx-auto text-center py-12">
          <Sparkles className="h-10 w-10 text-accent mx-auto mb-4" />
          <h3 className="font-medium mb-3">Try searching for</h3>
          <div className="flex flex-wrap justify-center gap-2">
            {["EU AI Act", "GDPR compliance", "algorithmic accountability", "AI risk management", "bias mitigation"].map((q) => (
              <button
                key={q}
                type="button"
                onClick={() => executeSearch(q)}
                className="px-3 py-1.5 text-sm bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 rounded-lg hover:bg-accent-50 hover:text-accent transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
        </Card>
      )}

      {/* Results layout */}
      {hasQuery && (
        <div className="flex gap-6">
          {/* Mobile facet toggle */}
          <Button
            variant="ghost"
            size="sm"
            className="lg:hidden fixed bottom-4 right-4 z-40 shadow-lg bg-white dark:bg-surface border"
            onClick={() => setShowMobileFacets((v) => !v)}
          >
            <Filter className="h-4 w-4" /> Filters
          </Button>

          {/* Facet sidebar */}
          <div
            className={clsx(
              "w-56 shrink-0",
              showMobileFacets
                ? "fixed inset-y-0 left-0 z-50 w-72 bg-white dark:bg-surface p-4 shadow-xl overflow-y-auto"
                : "hidden lg:block",
            )}
          >
            {showMobileFacets && (
              <button
                type="button"
                onClick={() => setShowMobileFacets(false)}
                className="mb-4 text-sm text-accent lg:hidden"
              >
                Close
              </button>
            )}
            <Card>
              <FacetPanel
                facets={facets}
                selectedJurisdictions={jurisdictions}
                selectedCategories={categories}
                selectedUrgency={urgency}
                onToggleJurisdiction={(v) =>
                  handleFacetChange(toggleSet(jurisdictions, v), categories, urgency)
                }
                onToggleCategory={(v) =>
                  handleFacetChange(jurisdictions, toggleSet(categories, v), urgency)
                }
                onToggleUrgency={(v) =>
                  handleFacetChange(jurisdictions, categories, toggleSet(urgency, v))
                }
                onClearAll={clearAllFacets}
              />
            </Card>
          </div>

          {/* Results */}
          <div className="flex-1 space-y-4">
            {/* Results header */}
            {results && !isLoading && (
              <div className="flex items-center justify-between">
                <p className="text-sm text-slate-500">
                  Showing <span className="font-medium text-slate-700 dark:text-slate-300">{shownResults}</span>{" "}
                  of <span className="font-medium text-slate-700 dark:text-slate-300">{totalResults}</span> results
                  for &ldquo;<span className="font-medium">{results.query}</span>&rdquo;
                </p>
              </div>
            )}

            {/* Loading */}
            {isLoading && (
              <div className="flex justify-center py-12">
                <Spinner />
              </div>
            )}

            {/* Result cards */}
            {!isLoading && results?.results.map((result) => (
              <ResultCard key={result.document_id} result={result} />
            ))}

            {/* No results */}
            {!isLoading && results && results.results.length === 0 && (
              <Card className="text-center py-12">
                <SearchIcon className="h-10 w-10 text-slate-300 mx-auto mb-4" />
                <h3 className="font-medium mb-2">No results found</h3>
                <p className="text-sm text-slate-500 mb-4">
                  Try adjusting your search terms or removing filters.
                </p>
                <div className="flex flex-wrap justify-center gap-2">
                  {["broaden your query", "try semantic search", "remove filters"].map((suggestion) => (
                    <span
                      key={suggestion}
                      className="px-2 py-1 text-xs bg-slate-100 dark:bg-slate-700 text-slate-500 rounded"
                    >
                      {suggestion}
                    </span>
                  ))}
                </div>
              </Card>
            )}

            {/* Pagination */}
            {!isLoading && results && shownResults < totalResults && (
              <div className="flex justify-center pt-4">
                <Button variant="secondary" onClick={handleLoadMore} loading={isLoading}>
                  Load more results
                </Button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
