import { describe, it, expect, vi, afterEach } from "vitest";
import { cleanup, render, screen, fireEvent } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { ReportWizard } from "../components/reports/ReportWizard";
import { ReportCard } from "../components/reports/ReportCard";
import type { Report } from "../components/reports/ReportCard";

afterEach(() => { cleanup(); });

const DOCS = [
  { id: "1", title: "EU AI Act", jurisdiction: "EU", status: "enriched" },
  { id: "2", title: "NIST Framework", jurisdiction: "US-Federal", status: "enriched" },
  { id: "3", title: "UK ICO Guidance", jurisdiction: "UK", status: "processing" },
];

function Wrapper({ children }: { children: React.ReactNode }) {
  return <BrowserRouter>{children}</BrowserRouter>;
}

/* ------------------------------------------------------------------ */
/*  ReportWizard                                                       */
/* ------------------------------------------------------------------ */

describe("ReportWizard", () => {
  const defaults = {
    documents: DOCS,
    onGenerate: vi.fn(),
    onCancel: vi.fn(),
  };

  it("renders step 1 with document list", () => {
    render(<Wrapper><ReportWizard {...defaults} /></Wrapper>);
    expect(screen.getByText("EU AI Act")).toBeTruthy();
    expect(screen.getByText("NIST Framework")).toBeTruthy();
    expect(screen.getByText("UK ICO Guidance")).toBeTruthy();
  });

  it("disables Next button when no documents selected", () => {
    render(<Wrapper><ReportWizard {...defaults} /></Wrapper>);
    const nextBtn = screen.getByRole("button", { name: /next/i });
    expect(nextBtn).toBeDisabled();
  });

  it("enables Next button after selecting a document", () => {
    render(<Wrapper><ReportWizard {...defaults} /></Wrapper>);
    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[0]!);
    const nextBtn = screen.getByRole("button", { name: /next/i });
    expect(nextBtn).not.toBeDisabled();
  });

  it("navigates through all 4 steps", () => {
    render(<Wrapper><ReportWizard {...defaults} /></Wrapper>);

    // Step 1: select a document and advance
    fireEvent.click(screen.getAllByRole("checkbox")[0]!);
    fireEvent.click(screen.getByRole("button", { name: /next/i }));

    // Step 2: template selection visible
    expect(screen.getByText("Standard")).toBeTruthy();
    expect(screen.getByText("Executive")).toBeTruthy();
    expect(screen.getByText("Detailed")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /next/i }));

    // Step 3: configure form visible
    expect(screen.getByLabelText("Report Title")).toBeTruthy();
    expect(screen.getByLabelText("Audience")).toBeTruthy();
  });

  it("validates title is required on step 3", () => {
    render(<Wrapper><ReportWizard {...defaults} /></Wrapper>);

    // Advance to step 3
    fireEvent.click(screen.getAllByRole("checkbox")[0]!);
    fireEvent.click(screen.getByRole("button", { name: /next/i }));
    fireEvent.click(screen.getByRole("button", { name: /next/i }));

    // Try to advance without title
    fireEvent.click(screen.getByRole("button", { name: /next/i }));
    expect(screen.getByText("Report title is required")).toBeTruthy();
  });

  it("advances to review step after filling title", () => {
    render(<Wrapper><ReportWizard {...defaults} /></Wrapper>);

    // Step 1
    fireEvent.click(screen.getAllByRole("checkbox")[0]!);
    fireEvent.click(screen.getByRole("button", { name: /next/i }));
    // Step 2
    fireEvent.click(screen.getByRole("button", { name: /next/i }));
    // Step 3 - fill title
    fireEvent.change(screen.getByLabelText("Report Title"), { target: { value: "Test Report" } });
    fireEvent.click(screen.getByRole("button", { name: /next/i }));

    // Step 4 - review
    expect(screen.getByText("Test Report")).toBeTruthy();
    expect(screen.getByText("Generate Report")).toBeTruthy();
  });

  it("calls onGenerate with correct data", () => {
    const onGenerate = vi.fn();
    render(<Wrapper><ReportWizard {...defaults} onGenerate={onGenerate} /></Wrapper>);

    // Complete wizard
    fireEvent.click(screen.getAllByRole("checkbox")[0]!);
    fireEvent.click(screen.getByRole("button", { name: /next/i }));
    fireEvent.click(screen.getByRole("button", { name: /next/i }));
    fireEvent.change(screen.getByLabelText("Report Title"), { target: { value: "My Report" } });
    fireEvent.click(screen.getByRole("button", { name: /next/i }));
    fireEvent.click(screen.getByText("Generate Report"));

    expect(onGenerate).toHaveBeenCalledOnce();
    const result = onGenerate.mock.calls[0][0];
    expect(result.title).toBe("My Report");
    expect(result.documentIds).toEqual(["1"]);
    expect(result.template).toBe("standard");
    expect(result.format).toBe("pdf");
  });

  it("calls onCancel when Cancel is clicked on step 1", () => {
    const onCancel = vi.fn();
    render(<Wrapper><ReportWizard {...defaults} onCancel={onCancel} /></Wrapper>);
    fireEvent.click(screen.getByRole("button", { name: /cancel/i }));
    expect(onCancel).toHaveBeenCalledOnce();
  });

  it("navigates back with Back button", () => {
    render(<Wrapper><ReportWizard {...defaults} /></Wrapper>);

    fireEvent.click(screen.getAllByRole("checkbox")[0]!);
    fireEvent.click(screen.getByRole("button", { name: /next/i }));
    // Now on step 2 — Back should go to step 1
    fireEvent.click(screen.getByRole("button", { name: /back/i }));
    expect(screen.getByText("1 selected")).toBeTruthy();
  });

  it("filters documents by search query", () => {
    render(<Wrapper><ReportWizard {...defaults} /></Wrapper>);
    const searchInput = screen.getByLabelText("Search documents");
    fireEvent.change(searchInput, { target: { value: "NIST" } });
    expect(screen.getByText("NIST Framework")).toBeTruthy();
    expect(screen.queryByText("EU AI Act")).toBeNull();
  });

  it("pre-selects documents from initialDocumentIds", () => {
    render(<Wrapper><ReportWizard {...defaults} initialDocumentIds={["2"]} /></Wrapper>);
    expect(screen.getByText("1 selected")).toBeTruthy();
  });
});

/* ------------------------------------------------------------------ */
/*  ReportCard                                                         */
/* ------------------------------------------------------------------ */

describe("ReportCard", () => {
  const report: Report = {
    id: "r1",
    title: "Test Report",
    status: "completed",
    template: "executive",
    format: "pdf",
    createdAt: "2024-12-20T10:00:00Z",
    documentCount: 3,
  };

  it("renders report title and metadata", () => {
    render(
      <ReportCard report={report} onView={vi.fn()} onDownload={vi.fn()} onDelete={vi.fn()} />,
    );
    expect(screen.getByText("Test Report")).toBeTruthy();
    expect(screen.getByText("Completed")).toBeTruthy();
    expect(screen.getByText("Executive template")).toBeTruthy();
    expect(screen.getByText("3 docs")).toBeTruthy();
  });

  it("disables download for non-completed reports", () => {
    const generating: Report = { ...report, status: "generating" };
    render(
      <ReportCard report={generating} onView={vi.fn()} onDownload={vi.fn()} onDelete={vi.fn()} />,
    );
    expect(screen.getByLabelText("Download report")).toBeDisabled();
  });

  it("calls onView when View is clicked", () => {
    const onView = vi.fn();
    render(<ReportCard report={report} onView={onView} onDownload={vi.fn()} onDelete={vi.fn()} />);
    fireEvent.click(screen.getByLabelText("View report"));
    expect(onView).toHaveBeenCalledWith("r1");
  });

  it("calls onDelete when delete button is clicked", () => {
    const onDelete = vi.fn();
    render(<ReportCard report={report} onView={vi.fn()} onDownload={vi.fn()} onDelete={onDelete} />);
    fireEvent.click(screen.getByLabelText("Delete report"));
    expect(onDelete).toHaveBeenCalledWith("r1");
  });
});
