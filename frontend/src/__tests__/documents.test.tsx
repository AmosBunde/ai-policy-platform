import { describe, it, expect, afterEach } from "vitest";
import { cleanup, render, screen, fireEvent } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StatusBadge } from "../components/documents/StatusBadge";
import { EnrichmentPanel } from "../components/documents/EnrichmentPanel";
import { DocumentTable } from "../components/documents/DocumentTable";

afterEach(() => { cleanup(); });

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

function Wrapper({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{children}</BrowserRouter>
    </QueryClientProvider>
  );
}

const SAMPLE_ENRICHMENT = {
  summary: "AI regulation summary text.",
  keyChanges: [
    { change: "Mandatory audits", affectedParties: ["AI developers"] },
  ],
  classification: [
    { domain: "safety", confidence: 0.95 },
    { domain: "privacy", confidence: 0.6 },
  ],
  impactScores: [
    { region: "EU", productCategory: "SaaS", score: 9, justification: "Direct impact" },
  ],
  draftResponse: "Compliance response draft text.",
  urgencyLevel: "high",
  confidenceScore: 0.85,
};

describe("StatusBadge", () => {
  it("renders ingested status", () => {
    render(<StatusBadge status="ingested" />);
    expect(screen.getByText("Ingested")).toBeTruthy();
  });

  it("renders enriched status", () => {
    render(<StatusBadge status="enriched" />);
    expect(screen.getByText("Enriched")).toBeTruthy();
  });

  it("renders failed status", () => {
    render(<StatusBadge status="failed" />);
    expect(screen.getByText("Failed")).toBeTruthy();
  });

  it("handles unknown status", () => {
    render(<StatusBadge status="unknown" />);
    expect(screen.getByText("unknown")).toBeTruthy();
  });
});

describe("EnrichmentPanel", () => {
  it("shows summary tab by default", () => {
    render(<EnrichmentPanel enrichment={SAMPLE_ENRICHMENT} />);
    expect(screen.getByText("AI regulation summary text.")).toBeTruthy();
  });

  it("switches to key changes tab", () => {
    render(<EnrichmentPanel enrichment={SAMPLE_ENRICHMENT} />);
    fireEvent.click(screen.getByText("Key Changes"));
    expect(screen.getByText("Mandatory audits")).toBeTruthy();
  });

  it("switches to classification tab", () => {
    render(<EnrichmentPanel enrichment={SAMPLE_ENRICHMENT} />);
    fireEvent.click(screen.getByText("Classification"));
    expect(screen.getByText("safety")).toBeTruthy();
    expect(screen.getByText("95%")).toBeTruthy();
  });

  it("switches to impact tab", () => {
    render(<EnrichmentPanel enrichment={SAMPLE_ENRICHMENT} />);
    fireEvent.click(screen.getByText("Impact Matrix"));
    expect(screen.getByText("9/10")).toBeTruthy();
  });

  it("switches to draft response tab", () => {
    render(<EnrichmentPanel enrichment={SAMPLE_ENRICHMENT} />);
    fireEvent.click(screen.getByText("Draft Response"));
    expect(screen.getByText("Compliance response draft text.")).toBeTruthy();
    expect(screen.getByText("Copy to clipboard")).toBeTruthy();
  });

  it("shows message when no enrichment", () => {
    render(<EnrichmentPanel enrichment={null} />);
    expect(screen.getByText("No enrichment data available.")).toBeTruthy();
  });
});

describe("DocumentTable", () => {
  const docs = [
    { id: "1", title: "EU AI Act", jurisdiction: "EU", urgencyLevel: "critical", status: "enriched", publishedAt: "2024-12-15" },
    { id: "2", title: "NIST Framework", jurisdiction: "US-Federal", urgencyLevel: "normal", status: "ingested", publishedAt: "2024-11-20" },
  ];

  it("renders document rows", () => {
    render(
      <Wrapper>
        <DocumentTable
          documents={docs}
          selectedIds={new Set()}
          onToggleSelect={() => {}}
          onToggleSelectAll={() => {}}
          sortField="publishedAt"
          sortDir="desc"
          onSort={() => {}}
        />
      </Wrapper>,
    );
    expect(screen.getByText("EU AI Act")).toBeTruthy();
    expect(screen.getByText("NIST Framework")).toBeTruthy();
  });

  it("shows selected count via checkboxes", () => {
    render(
      <Wrapper>
        <DocumentTable
          documents={docs}
          selectedIds={new Set(["1"])}
          onToggleSelect={() => {}}
          onToggleSelectAll={() => {}}
          sortField="publishedAt"
          sortDir="desc"
          onSort={() => {}}
        />
      </Wrapper>,
    );
    const checkboxes = screen.getAllByRole("checkbox");
    // First checkbox is "select all", then one per doc
    expect(checkboxes.length).toBe(3);
  });
});
