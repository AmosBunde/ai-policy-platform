import { useState, useEffect, useRef, useCallback } from "react";
import { Search, X, Keyboard } from "lucide-react";
import { clsx } from "clsx";
import {
  useSearchSuggestions,
  getSearchHistory,
  clearSearchHistory,
  sanitizeSearchInput,
} from "../../hooks/useSearch";

type SearchType = "keyword" | "semantic" | "hybrid";

interface SearchInputProps {
  value: string;
  searchType: SearchType;
  onSearch: (query: string) => void;
  onSearchTypeChange: (type: SearchType) => void;
  inputRef?: React.RefObject<HTMLInputElement>;
}

const SEARCH_TYPES: { value: SearchType; label: string }[] = [
  { value: "keyword", label: "Keyword" },
  { value: "semantic", label: "Semantic" },
  { value: "hybrid", label: "Hybrid" },
];

export function SearchInput({
  value,
  searchType,
  onSearch,
  onSearchTypeChange,
  inputRef,
}: SearchInputProps) {
  const [inputValue, setInputValue] = useState(value);
  const [showDropdown, setShowDropdown] = useState(false);
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);
  const internalRef = useRef<HTMLInputElement>(null);
  const ref = inputRef ?? internalRef;

  // Sync external value changes
  useEffect(() => {
    setInputValue(value);
  }, [value]);

  // Debounce for suggestions (300ms)
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(sanitizeSearchInput(inputValue));
    }, 300);
    return () => clearTimeout(timer);
  }, [inputValue]);

  const { data: suggestions } = useSearchSuggestions(debouncedQuery);
  const history = !inputValue.trim() ? getSearchHistory() : [];

  const handleSubmit = useCallback(
    (q?: string) => {
      const query = sanitizeSearchInput(q ?? inputValue);
      if (query) {
        onSearch(query);
        setShowDropdown(false);
      }
    },
    [inputValue, onSearch],
  );

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleSubmit();
    }
    if (e.key === "Escape") {
      setShowDropdown(false);
    }
  };

  // Close dropdown on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const dropdownItems =
    inputValue.trim() && suggestions?.length
      ? suggestions
      : history;

  const showClearHistory = !inputValue.trim() && history.length > 0;

  return (
    <div ref={containerRef} className="w-full max-w-3xl mx-auto space-y-3">
      {/* Search input */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
        <input
          ref={ref}
          type="text"
          value={inputValue}
          onChange={(e) => {
            setInputValue(e.target.value);
            setShowDropdown(true);
          }}
          onFocus={() => setShowDropdown(true)}
          onKeyDown={handleKeyDown}
          placeholder="Search regulatory documents..."
          maxLength={500}
          aria-label="Search"
          className="w-full pl-12 pr-20 py-3.5 text-base rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-surface focus:outline-none focus:ring-2 focus:ring-accent/50 shadow-sm"
        />
        <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1">
          {inputValue && (
            <button
              type="button"
              onClick={() => {
                setInputValue("");
                ref.current?.focus();
              }}
              className="p-1 text-slate-400 hover:text-slate-600"
              aria-label="Clear search"
            >
              <X className="h-4 w-4" />
            </button>
          )}
          <span className="hidden sm:flex items-center gap-0.5 text-xs text-slate-400 bg-slate-100 dark:bg-slate-700 px-1.5 py-0.5 rounded">
            <Keyboard className="h-3 w-3" />
            {navigator.platform.includes("Mac") ? "⌘K" : "Ctrl+K"}
          </span>
        </div>

        {/* Dropdown */}
        {showDropdown && dropdownItems.length > 0 && (
          <div className="absolute top-full mt-1 w-full bg-white dark:bg-surface rounded-lg shadow-lg border border-slate-200 dark:border-slate-700 z-50 max-h-64 overflow-y-auto">
            {showClearHistory && (
              <div className="flex items-center justify-between px-3 py-1.5 border-b border-slate-100 dark:border-slate-700">
                <span className="text-xs text-slate-500">Recent searches</span>
                <button
                  type="button"
                  onClick={() => {
                    clearSearchHistory();
                    setShowDropdown(false);
                  }}
                  className="text-xs text-accent hover:underline"
                >
                  Clear history
                </button>
              </div>
            )}
            {dropdownItems.map((item, i) => (
              <button
                key={`${item}-${i}`}
                type="button"
                className="flex items-center gap-2 w-full px-3 py-2 text-sm text-left hover:bg-slate-50 dark:hover:bg-slate-800"
                onMouseDown={(e) => {
                  e.preventDefault();
                  setInputValue(item);
                  handleSubmit(item);
                }}
              >
                <Search className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                <span className="truncate">{item}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Search type toggle */}
      <div className="flex items-center justify-center gap-1">
        {SEARCH_TYPES.map((t) => (
          <button
            key={t.value}
            type="button"
            onClick={() => onSearchTypeChange(t.value)}
            className={clsx(
              "px-3 py-1.5 text-xs font-medium rounded-lg transition-colors",
              searchType === t.value
                ? "bg-accent text-white"
                : "bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600",
            )}
          >
            {t.label}
          </button>
        ))}
      </div>
    </div>
  );
}
