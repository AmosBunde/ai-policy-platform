import { useQuery, useMutation } from "@tanstack/react-query";
import { api } from "../services/api";

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

export interface SearchResult {
  document_id: string;
  title: string;
  snippet: string;
  score: number;
  jurisdiction: string | null;
  published_at: string | null;
  urgency_level: string | null;
  highlights: string[];
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  page: number;
  page_size: number;
  query: string;
}

export interface SearchParams {
  query: string;
  search_type?: "keyword" | "semantic" | "hybrid";
  jurisdiction?: string;
  category?: string;
  urgency_level?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

export interface FacetCounts {
  jurisdictions: { value: string; label: string; count: number }[];
  categories: { value: string; label: string; count: number }[];
  urgency: { value: string; label: string; count: number }[];
}

/* ------------------------------------------------------------------ */
/*  Sample data                                                        */
/* ------------------------------------------------------------------ */

const SAMPLE_RESULTS: SearchResult[] = [
  {
    document_id: "1",
    title: "EU AI Act - Final Implementation Guidelines",
    snippet: "Article 6 requires providers of high-risk AI systems to establish risk management systems...",
    score: 0.95,
    jurisdiction: "EU",
    published_at: "2024-12-15T00:00:00Z",
    urgency_level: "critical",
    highlights: ["EU AI Act", "implementation guidelines", "high-risk AI systems"],
  },
  {
    document_id: "2",
    title: "NIST AI Risk Management Framework Update",
    snippet: "The updated framework introduces mandatory bias testing requirements for federal agencies...",
    score: 0.87,
    jurisdiction: "US-Federal",
    published_at: "2024-11-20T00:00:00Z",
    urgency_level: "high",
    highlights: ["risk management", "bias testing", "federal agencies"],
  },
  {
    document_id: "3",
    title: "UK ICO AI and Data Protection Guidance",
    snippet: "Guidance on the application of data protection principles to artificial intelligence systems...",
    score: 0.82,
    jurisdiction: "UK",
    published_at: "2024-10-05T00:00:00Z",
    urgency_level: "normal",
    highlights: ["data protection", "artificial intelligence"],
  },
  {
    document_id: "4",
    title: "Canada AIDA Bill Second Reading",
    snippet: "The Artificial Intelligence and Data Act introduces new requirements for responsible AI deployment...",
    score: 0.74,
    jurisdiction: "Canada",
    published_at: "2024-09-18T00:00:00Z",
    urgency_level: "normal",
    highlights: ["AIDA", "responsible AI"],
  },
  {
    document_id: "5",
    title: "Singapore AI Governance Framework v2",
    snippet: "Updated governance framework with enhanced provisions for generative AI and foundation models...",
    score: 0.68,
    jurisdiction: "APAC",
    published_at: "2024-08-30T00:00:00Z",
    urgency_level: "low",
    highlights: ["governance framework", "generative AI"],
  },
];

const SAMPLE_FACETS: FacetCounts = {
  jurisdictions: [
    { value: "EU", label: "EU", count: 42 },
    { value: "US-Federal", label: "US Federal", count: 38 },
    { value: "UK", label: "UK", count: 24 },
    { value: "APAC", label: "APAC", count: 18 },
    { value: "Canada", label: "Canada", count: 12 },
  ],
  categories: [
    { value: "privacy", label: "Privacy", count: 56 },
    { value: "safety", label: "Safety", count: 34 },
    { value: "intellectual_property", label: "IP", count: 21 },
    { value: "antitrust", label: "Antitrust", count: 15 },
    { value: "transparency", label: "Transparency", count: 28 },
    { value: "liability", label: "Liability", count: 10 },
  ],
  urgency: [
    { value: "critical", label: "Critical", count: 8 },
    { value: "high", label: "High", count: 23 },
    { value: "normal", label: "Normal", count: 67 },
    { value: "low", label: "Low", count: 36 },
  ],
};

const SAMPLE_SUGGESTIONS = [
  "EU AI Act compliance",
  "GDPR data protection",
  "algorithmic accountability",
  "AI risk management",
  "bias mitigation requirements",
];

/* ------------------------------------------------------------------ */
/*  Hooks                                                              */
/* ------------------------------------------------------------------ */

export function useSearchDocuments() {
  return useMutation({
    mutationFn: async (params: SearchParams): Promise<SearchResponse> => {
      try {
        const resp = await api.post("/search", params);
        return resp.data as SearchResponse;
      } catch {
        // Return sample data when API unavailable
        const filtered = SAMPLE_RESULTS.filter((r) => {
          if (params.jurisdiction && r.jurisdiction !== params.jurisdiction) return false;
          if (params.urgency_level && r.urgency_level !== params.urgency_level) return false;
          return true;
        });
        return {
          results: filtered,
          total: filtered.length,
          page: params.page ?? 1,
          page_size: params.page_size ?? 20,
          query: params.query,
        };
      }
    },
  });
}

export function useSearchSuggestions(query: string) {
  return useQuery({
    queryKey: ["search", "suggest", query],
    queryFn: async (): Promise<string[]> => {
      try {
        const resp = await api.get("/search/suggest", { params: { q: query } });
        return resp.data as string[];
      } catch {
        const q = query.toLowerCase();
        return SAMPLE_SUGGESTIONS.filter((s) => s.toLowerCase().includes(q));
      }
    },
    enabled: query.length >= 2,
    staleTime: 10_000,
  });
}

export function useSearchFacets() {
  return useQuery({
    queryKey: ["search", "facets"],
    queryFn: async (): Promise<FacetCounts> => {
      try {
        const resp = await api.get("/search/facets");
        return resp.data as FacetCounts;
      } catch {
        return SAMPLE_FACETS;
      }
    },
    placeholderData: SAMPLE_FACETS,
    staleTime: 60_000,
  });
}

/* ------------------------------------------------------------------ */
/*  Search history helpers                                             */
/* ------------------------------------------------------------------ */

const HISTORY_KEY = "regulatorai_search_history";
const MAX_HISTORY = 20;

export function getSearchHistory(): string[] {
  try {
    const raw = sessionStorage.getItem(HISTORY_KEY);
    return raw ? (JSON.parse(raw) as string[]) : [];
  } catch {
    return [];
  }
}

export function addSearchHistory(query: string): void {
  const trimmed = query.trim();
  if (!trimmed) return;
  const history = getSearchHistory().filter((h) => h !== trimmed);
  history.unshift(trimmed);
  sessionStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(0, MAX_HISTORY)));
}

export function clearSearchHistory(): void {
  sessionStorage.removeItem(HISTORY_KEY);
}

/* ------------------------------------------------------------------ */
/*  Sanitization                                                       */
/* ------------------------------------------------------------------ */

export function sanitizeSearchInput(input: string): string {
  return input.replace(/<[^>]*>/g, "").trim();
}
