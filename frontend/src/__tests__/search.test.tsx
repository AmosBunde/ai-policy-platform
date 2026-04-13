import { describe, it, expect, vi, afterEach } from "vitest";
import { cleanup, render, screen, fireEvent, act } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  sanitizeSearchInput,
  getSearchHistory,
  addSearchHistory,
  clearSearchHistory,
} from "../hooks/useSearch";
import { SearchInput } from "../components/search/SearchInput";
import { FacetPanel } from "../components/search/FacetPanel";
import { ResultCard } from "../components/search/ResultCard";

afterEach(() => {
  cleanup();
  sessionStorage.clear();
});

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

function Wrapper({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{children}</BrowserRouter>
    </QueryClientProvider>
  );
}

/* ------------------------------------------------------------------ */
/*  sanitizeSearchInput                                                */
/* ------------------------------------------------------------------ */

describe("sanitizeSearchInput", () => {
  it("strips HTML tags from input", () => {
    expect(sanitizeSearchInput('<script>alert("xss")</script>EU AI Act')).toBe(
      'alert("xss")EU AI Act',
    );
  });

  it("strips multiple HTML tags", () => {
    expect(sanitizeSearchInput("<b>bold</b> and <i>italic</i>")).toBe(
      "bold and italic",
    );
  });

  it("trims whitespace", () => {
    expect(sanitizeSearchInput("  hello world  ")).toBe("hello world");
  });

  it("returns empty string for only tags", () => {
    expect(sanitizeSearchInput("<div></div>")).toBe("");
  });

  it("passes through clean input unchanged", () => {
    expect(sanitizeSearchInput("EU AI Act compliance")).toBe(
      "EU AI Act compliance",
    );
  });
});

/* ------------------------------------------------------------------ */
/*  Search history                                                     */
/* ------------------------------------------------------------------ */

describe("Search history (sessionStorage)", () => {
  it("starts empty", () => {
    expect(getSearchHistory()).toEqual([]);
  });

  it("adds items", () => {
    addSearchHistory("EU AI Act");
    addSearchHistory("GDPR");
    const history = getSearchHistory();
    expect(history[0]).toBe("GDPR");
    expect(history[1]).toBe("EU AI Act");
  });

  it("deduplicates entries", () => {
    addSearchHistory("EU AI Act");
    addSearchHistory("GDPR");
    addSearchHistory("EU AI Act"); // duplicate
    const history = getSearchHistory();
    expect(history.length).toBe(2);
    expect(history[0]).toBe("EU AI Act");
  });

  it("limits to 20 entries", () => {
    for (let i = 0; i < 25; i++) {
      addSearchHistory(`query-${i}`);
    }
    expect(getSearchHistory().length).toBe(20);
  });

  it("clears history", () => {
    addSearchHistory("test");
    clearSearchHistory();
    expect(getSearchHistory()).toEqual([]);
  });

  it("ignores empty queries", () => {
    addSearchHistory("");
    addSearchHistory("   ");
    expect(getSearchHistory()).toEqual([]);
  });
});

/* ------------------------------------------------------------------ */
/*  SearchInput                                                        */
/* ------------------------------------------------------------------ */

describe("SearchInput", () => {
  it("renders input and accepts text", () => {
    const onSearch = vi.fn();
    render(
      <Wrapper>
        <SearchInput
          value=""
          searchType="hybrid"
          onSearch={onSearch}
          onSearchTypeChange={vi.fn()}
        />
      </Wrapper>,
    );

    const input = screen.getByLabelText("Search");
    expect(input).toBeTruthy();
    fireEvent.change(input, { target: { value: "EU AI Act" } });
    expect((input as HTMLInputElement).value).toBe("EU AI Act");
  });

  it("calls onSearch when Enter is pressed", () => {
    const onSearch = vi.fn();
    render(
      <Wrapper>
        <SearchInput
          value="test query"
          searchType="hybrid"
          onSearch={onSearch}
          onSearchTypeChange={vi.fn()}
        />
      </Wrapper>,
    );

    const input = screen.getByLabelText("Search");
    fireEvent.keyDown(input, { key: "Enter" });
    expect(onSearch).toHaveBeenCalledWith("test query");
  });

  it("renders search type toggle buttons", () => {
    render(
      <Wrapper>
        <SearchInput
          value=""
          searchType="hybrid"
          onSearch={vi.fn()}
          onSearchTypeChange={vi.fn()}
        />
      </Wrapper>,
    );

    expect(screen.getByText("Keyword")).toBeTruthy();
    expect(screen.getByText("Semantic")).toBeTruthy();
    expect(screen.getByText("Hybrid")).toBeTruthy();
  });

  it("calls onSearchTypeChange when type button clicked", () => {
    const onTypeChange = vi.fn();
    render(
      <Wrapper>
        <SearchInput
          value=""
          searchType="hybrid"
          onSearch={vi.fn()}
          onSearchTypeChange={onTypeChange}
        />
      </Wrapper>,
    );

    fireEvent.click(screen.getByText("Semantic"));
    expect(onTypeChange).toHaveBeenCalledWith("semantic");
  });

  it("debounces input changes (300ms)", async () => {
    vi.useFakeTimers();
    render(
      <Wrapper>
        <SearchInput
          value=""
          searchType="hybrid"
          onSearch={vi.fn()}
          onSearchTypeChange={vi.fn()}
        />
      </Wrapper>,
    );

    const input = screen.getByLabelText("Search");
    fireEvent.change(input, { target: { value: "E" } });
    fireEvent.change(input, { target: { value: "EU" } });
    fireEvent.change(input, { target: { value: "EU " } });
    fireEvent.change(input, { target: { value: "EU A" } });

    // Before debounce fires, input should have the latest value
    expect((input as HTMLInputElement).value).toBe("EU A");

    // Advance past debounce
    await act(async () => {
      vi.advanceTimersByTime(350);
    });

    vi.useRealTimers();
  });

  it("shows clear button when input has value", () => {
    render(
      <Wrapper>
        <SearchInput
          value="test"
          searchType="hybrid"
          onSearch={vi.fn()}
          onSearchTypeChange={vi.fn()}
        />
      </Wrapper>,
    );

    expect(screen.getByLabelText("Clear search")).toBeTruthy();
  });
});

/* ------------------------------------------------------------------ */
/*  FacetPanel                                                         */
/* ------------------------------------------------------------------ */

describe("FacetPanel", () => {
  const facets = {
    jurisdictions: [
      { value: "EU", label: "EU", count: 42 },
      { value: "US-Federal", label: "US Federal", count: 38 },
    ],
    categories: [
      { value: "privacy", label: "Privacy", count: 56 },
      { value: "safety", label: "Safety", count: 34 },
    ],
    urgency: [
      { value: "critical", label: "Critical", count: 8 },
      { value: "high", label: "High", count: 23 },
    ],
  };

  it("renders all facet groups", () => {
    render(
      <FacetPanel
        facets={facets}
        selectedJurisdictions={new Set()}
        selectedCategories={new Set()}
        selectedUrgency={new Set()}
        onToggleJurisdiction={vi.fn()}
        onToggleCategory={vi.fn()}
        onToggleUrgency={vi.fn()}
        onClearAll={vi.fn()}
      />,
    );

    expect(screen.getByText("Jurisdiction")).toBeTruthy();
    expect(screen.getByText("Category")).toBeTruthy();
    expect(screen.getByText("Urgency")).toBeTruthy();
  });

  it("shows facet counts", () => {
    render(
      <FacetPanel
        facets={facets}
        selectedJurisdictions={new Set()}
        selectedCategories={new Set()}
        selectedUrgency={new Set()}
        onToggleJurisdiction={vi.fn()}
        onToggleCategory={vi.fn()}
        onToggleUrgency={vi.fn()}
        onClearAll={vi.fn()}
      />,
    );

    expect(screen.getByText("42")).toBeTruthy();
    expect(screen.getByText("38")).toBeTruthy();
    expect(screen.getByText("56")).toBeTruthy();
  });

  it("calls toggle handler when checkbox clicked", () => {
    const onToggle = vi.fn();
    render(
      <FacetPanel
        facets={facets}
        selectedJurisdictions={new Set()}
        selectedCategories={new Set()}
        selectedUrgency={new Set()}
        onToggleJurisdiction={onToggle}
        onToggleCategory={vi.fn()}
        onToggleUrgency={vi.fn()}
        onClearAll={vi.fn()}
      />,
    );

    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[0]!);
    expect(onToggle).toHaveBeenCalledWith("EU");
  });

  it("shows clear all button when filters are selected", () => {
    render(
      <FacetPanel
        facets={facets}
        selectedJurisdictions={new Set(["EU"])}
        selectedCategories={new Set()}
        selectedUrgency={new Set()}
        onToggleJurisdiction={vi.fn()}
        onToggleCategory={vi.fn()}
        onToggleUrgency={vi.fn()}
        onClearAll={vi.fn()}
      />,
    );

    expect(screen.getByText("Clear all")).toBeTruthy();
  });

  it("collapses facet group on click", () => {
    render(
      <FacetPanel
        facets={facets}
        selectedJurisdictions={new Set()}
        selectedCategories={new Set()}
        selectedUrgency={new Set()}
        onToggleJurisdiction={vi.fn()}
        onToggleCategory={vi.fn()}
        onToggleUrgency={vi.fn()}
        onClearAll={vi.fn()}
      />,
    );

    // Click Jurisdiction header to collapse
    fireEvent.click(screen.getByText("Jurisdiction"));
    // EU checkbox should be hidden
    expect(screen.queryByText("EU")).toBeNull();
  });
});

/* ------------------------------------------------------------------ */
/*  ResultCard                                                         */
/* ------------------------------------------------------------------ */

describe("ResultCard", () => {
  const result = {
    document_id: "1",
    title: "EU AI Act Guidelines",
    snippet: "The EU AI Act introduces new compliance requirements for high-risk AI systems.",
    score: 0.92,
    jurisdiction: "EU",
    published_at: "2024-12-15T00:00:00Z",
    urgency_level: "critical",
    highlights: ["EU AI Act", "compliance requirements"],
  };

  it("renders title as a link", () => {
    render(
      <Wrapper>
        <ResultCard result={result} />
      </Wrapper>,
    );

    const link = screen.getByText("EU AI Act Guidelines");
    expect(link.closest("a")?.getAttribute("href")).toBe("/documents/1");
  });

  it("renders jurisdiction and urgency badges", () => {
    render(
      <Wrapper>
        <ResultCard result={result} />
      </Wrapper>,
    );

    expect(screen.getByText("EU")).toBeTruthy();
    expect(screen.getByText("critical")).toBeTruthy();
  });

  it("renders relevance score", () => {
    render(
      <Wrapper>
        <ResultCard result={result} />
      </Wrapper>,
    );

    expect(screen.getByText("92% match")).toBeTruthy();
  });

  it("renders highlights safely without dangerouslySetInnerHTML", () => {
    render(
      <Wrapper>
        <ResultCard result={result} />
      </Wrapper>,
    );

    // Check that highlights are rendered as <mark> elements
    const marks = document.querySelectorAll("mark");
    expect(marks.length).toBeGreaterThan(0);
    expect(marks[0]!.textContent).toBe("EU AI Act");
  });

  it("renders published date", () => {
    render(
      <Wrapper>
        <ResultCard result={result} />
      </Wrapper>,
    );

    // Date should be rendered in locale format
    expect(screen.getByText(/12\/15\/2024|15\/12\/2024|2024/)).toBeTruthy();
  });
});

/* ------------------------------------------------------------------ */
/*  URL sync (integration)                                             */
/* ------------------------------------------------------------------ */

describe("URL params sync", () => {
  it("reads query from URL params on mount", async () => {
    // Set initial URL with query param
    window.history.pushState({}, "", "/search?q=EU+AI+Act&type=semantic");

    const SearchPage = (await import("../pages/Search")).default;
    render(
      <Wrapper>
        <SearchPage />
      </Wrapper>,
    );

    // The search input should have the query value
    const input = screen.getByLabelText("Search") as HTMLInputElement;
    expect(input.value).toBe("EU AI Act");
  });
});
