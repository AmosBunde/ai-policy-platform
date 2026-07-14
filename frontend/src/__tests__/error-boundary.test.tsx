import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { cleanup, render, screen, fireEvent } from "@testing-library/react";
import { useState } from "react";
import { ErrorBoundary } from "../components/ui/ErrorBoundary";

afterEach(() => { cleanup(); });

function Bomb({ shouldThrow }: { shouldThrow: boolean }) {
  if (shouldThrow) {
    throw new Error("test explosion");
  }
  return <div>content rendered</div>;
}

describe("ErrorBoundary", () => {
  beforeEach(() => {
    // Suppress React's expected error logging noise
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  it("renders children when nothing throws", () => {
    render(
      <ErrorBoundary>
        <Bomb shouldThrow={false} />
      </ErrorBoundary>,
    );
    expect(screen.getByText("content rendered")).toBeInTheDocument();
  });

  it("shows branded fallback instead of white screen on render error", () => {
    render(
      <ErrorBoundary>
        <Bomb shouldThrow />
      </ErrorBoundary>,
    );
    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /try again/i })).toBeInTheDocument();
  });

  it("includes the scope name in the fallback message", () => {
    render(
      <ErrorBoundary scope="Reports">
        <Bomb shouldThrow />
      </ErrorBoundary>,
    );
    expect(screen.getByText(/The Reports view failed to load/)).toBeInTheDocument();
  });

  it("recovers via the Try again button once the cause is gone", () => {
    function Harness() {
      const [shouldThrow, setShouldThrow] = useState(true);
      return (
        <div>
          <button onClick={() => setShouldThrow(false)}>fix it</button>
          <ErrorBoundary>
            <Bomb shouldThrow={shouldThrow} />
          </ErrorBoundary>
        </div>
      );
    }
    render(<Harness />);
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();

    // Remove the error cause, then reset the boundary
    fireEvent.click(screen.getByText("fix it"));
    fireEvent.click(screen.getByRole("button", { name: /try again/i }));
    expect(screen.getByText("content rendered")).toBeInTheDocument();
  });

  it("exposes error details outside production builds", () => {
    render(
      <ErrorBoundary>
        <Bomb shouldThrow />
      </ErrorBoundary>,
    );
    expect(screen.getByText(/Error details/)).toBeInTheDocument();
    expect(screen.getByText(/test explosion/)).toBeInTheDocument();
  });
});
