import { describe, it, expect, afterEach, beforeEach } from "vitest";
import { cleanup, render, screen, fireEvent } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useAuthStore } from "../store/authStore";

afterEach(() => {
  cleanup();
  useAuthStore.setState({
    isAuthenticated: false,
    user: null,
    accessToken: null,
    refreshToken: null,
  });
});

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

function Wrapper({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{children}</BrowserRouter>
    </QueryClientProvider>
  );
}

function setUser(role: string) {
  useAuthStore.setState({
    isAuthenticated: true,
    user: { id: "1", email: "test@test.com", fullName: "Test User", role, organization: "TestOrg" },
    accessToken: "token",
    refreshToken: "refresh",
  });
}

/* ------------------------------------------------------------------ */
/*  Tab navigation                                                     */
/* ------------------------------------------------------------------ */

describe("Settings tab navigation", () => {
  beforeEach(() => setUser("admin"));

  it("renders all 4 tabs for admin user", async () => {
    const Settings = (await import("../pages/Settings")).default;
    render(<Wrapper><Settings /></Wrapper>);
    expect(screen.getByRole("tab", { name: /profile/i })).toBeTruthy();
    expect(screen.getByRole("tab", { name: /watch rules/i })).toBeTruthy();
    expect(screen.getByRole("tab", { name: /notifications/i })).toBeTruthy();
    expect(screen.getByRole("tab", { name: /admin/i })).toBeTruthy();
  });

  it("shows Profile content by default", async () => {
    const Settings = (await import("../pages/Settings")).default;
    render(<Wrapper><Settings /></Wrapper>);
    expect(screen.getByText("Profile Information")).toBeTruthy();
  });

  it("switches to Watch Rules tab", async () => {
    const Settings = (await import("../pages/Settings")).default;
    render(<Wrapper><Settings /></Wrapper>);
    fireEvent.click(screen.getByRole("tab", { name: /watch rules/i }));
    expect(screen.getByText("EU High Urgency")).toBeTruthy();
    expect(screen.getByText("US Federal Updates")).toBeTruthy();
  });

  it("switches to Notifications tab", async () => {
    const Settings = (await import("../pages/Settings")).default;
    render(<Wrapper><Settings /></Wrapper>);
    fireEvent.click(screen.getByRole("tab", { name: /notifications/i }));
    expect(screen.getByText("Notification Channels")).toBeTruthy();
    expect(screen.getByText("Digest Frequency")).toBeTruthy();
  });

  it("switches to Admin tab", async () => {
    const Settings = (await import("../pages/Settings")).default;
    render(<Wrapper><Settings /></Wrapper>);
    fireEvent.click(screen.getByRole("tab", { name: /admin/i }));
    expect(screen.getByText("Administration")).toBeTruthy();
    expect(screen.getByText("User Management")).toBeTruthy();
  });
});

/* ------------------------------------------------------------------ */
/*  Admin panel visibility                                             */
/* ------------------------------------------------------------------ */

describe("Admin panel hidden for non-admin", () => {
  it("does not render Admin tab for analyst role", async () => {
    setUser("analyst");
    const Settings = (await import("../pages/Settings")).default;
    render(<Wrapper><Settings /></Wrapper>);
    expect(screen.queryByRole("tab", { name: /admin/i })).toBeNull();
  });

  it("does not render Admin tab for viewer role", async () => {
    setUser("viewer");
    const Settings = (await import("../pages/Settings")).default;
    render(<Wrapper><Settings /></Wrapper>);
    expect(screen.queryByRole("tab", { name: /admin/i })).toBeNull();
  });

  it("renders 3 tabs for non-admin user", async () => {
    setUser("analyst");
    const Settings = (await import("../pages/Settings")).default;
    render(<Wrapper><Settings /></Wrapper>);
    const tabs = screen.getAllByRole("tab");
    expect(tabs.length).toBe(3);
  });
});

/* ------------------------------------------------------------------ */
/*  Password change validation                                         */
/* ------------------------------------------------------------------ */

describe("Password change requires current password", () => {
  beforeEach(() => setUser("analyst"));

  it("shows error when current password is empty", async () => {
    const Settings = (await import("../pages/Settings")).default;
    render(<Wrapper><Settings /></Wrapper>);

    // Fill new password but leave current empty
    fireEvent.change(screen.getByLabelText("New Password"), { target: { value: "NewStr0ng!Pass" } });
    fireEvent.change(screen.getByLabelText("Confirm New Password"), { target: { value: "NewStr0ng!Pass" } });
    fireEvent.click(screen.getByRole("button", { name: "Change Password" }));

    expect(screen.getByText("Current password is required")).toBeTruthy();
  });

  it("shows error when new password is too short", async () => {
    const Settings = (await import("../pages/Settings")).default;
    render(<Wrapper><Settings /></Wrapper>);

    fireEvent.change(screen.getByLabelText("Current Password"), { target: { value: "oldpass" } });
    fireEvent.change(screen.getByLabelText("New Password"), { target: { value: "short" } });
    fireEvent.change(screen.getByLabelText("Confirm New Password"), { target: { value: "short" } });
    fireEvent.click(screen.getByRole("button", { name: "Change Password" }));

    expect(screen.getByText("Password must be at least 8 characters")).toBeTruthy();
  });

  it("shows error when passwords do not match", async () => {
    const Settings = (await import("../pages/Settings")).default;
    render(<Wrapper><Settings /></Wrapper>);

    fireEvent.change(screen.getByLabelText("Current Password"), { target: { value: "oldpass123" } });
    fireEvent.change(screen.getByLabelText("New Password"), { target: { value: "NewStr0ng!Pass" } });
    fireEvent.change(screen.getByLabelText("Confirm New Password"), { target: { value: "Different!Pass1" } });
    fireEvent.click(screen.getByRole("button", { name: "Change Password" }));

    expect(screen.getByText("Passwords do not match")).toBeTruthy();
  });

  it("clears form on successful password change", async () => {
    const Settings = (await import("../pages/Settings")).default;
    render(<Wrapper><Settings /></Wrapper>);

    const currentPw = screen.getByLabelText("Current Password") as HTMLInputElement;
    const newPw = screen.getByLabelText("New Password") as HTMLInputElement;
    const confirmPw = screen.getByLabelText("Confirm New Password") as HTMLInputElement;

    fireEvent.change(currentPw, { target: { value: "oldpass123" } });
    fireEvent.change(newPw, { target: { value: "NewStr0ng!Pass" } });
    fireEvent.change(confirmPw, { target: { value: "NewStr0ng!Pass" } });
    fireEvent.click(screen.getByRole("button", { name: "Change Password" }));

    expect(currentPw.value).toBe("");
    expect(newPw.value).toBe("");
    expect(confirmPw.value).toBe("");
  });

  it("shows password strength indicator", async () => {
    const Settings = (await import("../pages/Settings")).default;
    render(<Wrapper><Settings /></Wrapper>);

    fireEvent.change(screen.getByLabelText("New Password"), { target: { value: "MyStr0ng!Pass" } });
    expect(screen.getByText("Strong")).toBeTruthy();
  });
});
