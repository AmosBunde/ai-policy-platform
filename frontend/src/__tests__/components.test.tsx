import { describe, it, expect, afterEach } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Input } from "../components/ui/Input";
import { Spinner } from "../components/ui/Spinner";
import { Toast } from "../components/ui/Toast";

afterEach(() => { cleanup(); });

describe("Button", () => {
  it("renders with children", () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText("Click me")).toBeTruthy();
  });

  it("shows loading spinner", () => {
    render(<Button loading>Submit</Button>);
    expect(screen.getByText("Submit")).toBeTruthy();
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("is disabled when disabled prop is true", () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByRole("button")).toBeDisabled();
  });
});

describe("Card", () => {
  it("renders children", () => {
    render(<Card>Card content</Card>);
    expect(screen.getByText("Card content")).toBeTruthy();
  });

  it("renders glass variant", () => {
    const { container } = render(<Card variant="glass">Glass</Card>);
    expect(container.firstChild).toBeTruthy();
  });
});

describe("Badge", () => {
  it("renders with text", () => {
    render(<Badge>Active</Badge>);
    expect(screen.getByText("Active")).toBeTruthy();
  });

  it("renders success variant", () => {
    render(<Badge variant="success">Success</Badge>);
    expect(screen.getByText("Success")).toBeTruthy();
  });
});

describe("Input", () => {
  it("renders with label", () => {
    render(<Input label="Email" />);
    expect(screen.getByLabelText("Email")).toBeTruthy();
  });

  it("shows error message", () => {
    render(<Input label="Password" error="Required" />);
    expect(screen.getByText("Required")).toBeTruthy();
  });

  it("shows helper text", () => {
    render(<Input label="Name" helperText="Enter your full name" />);
    expect(screen.getByText("Enter your full name")).toBeTruthy();
  });
});

describe("Spinner", () => {
  it("renders with loading role", () => {
    render(<Spinner />);
    expect(screen.getByRole("status")).toBeTruthy();
  });
});

describe("Toast", () => {
  it("renders message", () => {
    render(<Toast message="Saved!" onClose={() => {}} />);
    expect(screen.getByText("Saved!")).toBeTruthy();
  });

  it("renders with alert role", () => {
    render(<Toast message="Error" variant="error" onClose={() => {}} />);
    expect(screen.getByRole("alert")).toBeTruthy();
  });
});
