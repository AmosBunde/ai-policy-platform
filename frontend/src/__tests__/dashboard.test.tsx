import { describe, it, expect, afterEach } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { KPICard } from "../components/dashboard/KPICard";
import { RecentDocuments } from "../components/dashboard/RecentDocuments";
import { RefreshControl } from "../components/dashboard/RefreshControl";
import { FileText } from "lucide-react";

afterEach(() => { cleanup(); });

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

function Wrapper({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{children}</BrowserRouter>
    </QueryClientProvider>
  );
}

describe("KPICard", () => {
  it("renders with label and value", () => {
    render(
      <KPICard
        label="Total Documents"
        value={1247}
        icon={<FileText className="h-5 w-5" />}
      />,
    );
    expect(screen.getByText("Total Documents")).toBeTruthy();
  });

  it("renders trend label", () => {
    render(
      <KPICard
        label="Documents"
        value={100}
        icon={<FileText className="h-5 w-5" />}
        trend="up"
        trendLabel="+12 today"
      />,
    );
    expect(screen.getByText("+12 today")).toBeTruthy();
  });

  it("renders skeleton when loading", () => {
    const { container } = render(
      <KPICard label="Loading" value={0} icon={<FileText />} loading />,
    );
    expect(container.querySelector(".animate-pulse")).toBeTruthy();
  });
});

describe("RecentDocuments", () => {
  it("renders document rows", () => {
    const docs = [
      { id: "1", title: "EU AI Act", jurisdiction: "EU", urgencyLevel: "critical", status: "enriched", createdAt: new Date().toISOString() },
    ];
    render(
      <Wrapper>
        <RecentDocuments documents={docs} />
      </Wrapper>,
    );
    expect(screen.getByText("EU AI Act")).toBeTruthy();
    expect(screen.getByText("EU")).toBeTruthy();
    expect(screen.getByText("critical")).toBeTruthy();
  });

  it("shows empty state", () => {
    render(
      <Wrapper>
        <RecentDocuments documents={[]} />
      </Wrapper>,
    );
    expect(screen.getByText("No documents found")).toBeTruthy();
  });

  it("renders skeleton when loading", () => {
    const { container } = render(
      <Wrapper>
        <RecentDocuments documents={[]} loading />
      </Wrapper>,
    );
    expect(container.querySelector(".animate-pulse")).toBeTruthy();
  });
});

describe("RefreshControl", () => {
  it("renders refresh interval options", () => {
    render(<RefreshControl interval={30_000} onIntervalChange={() => {}} />);
    expect(screen.getByText("30s")).toBeTruthy();
    expect(screen.getByText("60s")).toBeTruthy();
    expect(screen.getByText("Off")).toBeTruthy();
  });

  it("shows auto-refresh label", () => {
    render(<RefreshControl interval={null} onIntervalChange={() => {}} />);
    expect(screen.getByText("Auto-refresh:")).toBeTruthy();
  });
});
