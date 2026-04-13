import { describe, it, expect, afterEach } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { PasswordStrengthBar } from "../components/auth/PasswordStrengthBar";

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

describe("PasswordStrengthBar", () => {
  it("shows nothing for empty password", () => {
    const { container } = render(<PasswordStrengthBar password="" />);
    expect(container.textContent).toBe("");
  });

  it("shows Weak for short simple password", () => {
    render(<PasswordStrengthBar password="abcdefgh" />);
    expect(screen.getByText("Weak")).toBeTruthy();
  });

  it("shows Medium for mixed-case password with digit", () => {
    render(<PasswordStrengthBar password="Abcdefg1" />);
    expect(screen.getByText("Medium")).toBeTruthy();
  });

  it("shows Strong for long complex password", () => {
    render(<PasswordStrengthBar password="MyStr0ng!Pass#2024" />);
    expect(screen.getByText("Strong")).toBeTruthy();
  });
});

describe("Login page", () => {
  it("renders login form with email and password fields", async () => {
    const Login = (await import("../pages/Login")).default;
    render(<Wrapper><Login /></Wrapper>);
    expect(screen.getByLabelText("Email")).toBeTruthy();
    expect(screen.getByLabelText("Password")).toBeTruthy();
    expect(screen.getByText("Sign In")).toBeTruthy();
  });

  it("has autocomplete=off on password field", async () => {
    const Login = (await import("../pages/Login")).default;
    render(<Wrapper><Login /></Wrapper>);
    const passwordInput = screen.getByLabelText("Password");
    expect(passwordInput.getAttribute("autocomplete")).toBe("off");
  });

  it("shows remember me and forgot password link", async () => {
    const Login = (await import("../pages/Login")).default;
    render(<Wrapper><Login /></Wrapper>);
    expect(screen.getByText("Remember me")).toBeTruthy();
    expect(screen.getByText("Forgot password?")).toBeTruthy();
  });

  it("shows register link", async () => {
    const Login = (await import("../pages/Login")).default;
    render(<Wrapper><Login /></Wrapper>);
    expect(screen.getByText("Register")).toBeTruthy();
  });
});

describe("Register page", () => {
  it("renders registration form fields", async () => {
    const Register = (await import("../pages/Register")).default;
    render(<Wrapper><Register /></Wrapper>);
    expect(screen.getByLabelText("Full Name")).toBeTruthy();
    expect(screen.getByLabelText("Email")).toBeTruthy();
    expect(screen.getByLabelText("Password")).toBeTruthy();
    expect(screen.getByLabelText("Confirm Password")).toBeTruthy();
  });

  it("displays password requirements", async () => {
    const Register = (await import("../pages/Register")).default;
    render(<Wrapper><Register /></Wrapper>);
    expect(screen.getByText("At least 8 characters")).toBeTruthy();
    expect(screen.getByText("At least one uppercase and one lowercase letter")).toBeTruthy();
    expect(screen.getByText("At least one digit")).toBeTruthy();
  });

  it("has role selector", async () => {
    const Register = (await import("../pages/Register")).default;
    render(<Wrapper><Register /></Wrapper>);
    expect(screen.getByLabelText("Role")).toBeTruthy();
  });
});

describe("ForgotPassword page", () => {
  it("renders forgot password form", async () => {
    const ForgotPassword = (await import("../pages/ForgotPassword")).default;
    render(<Wrapper><ForgotPassword /></Wrapper>);
    expect(screen.getByText("Reset Password")).toBeTruthy();
    expect(screen.getByLabelText("Email")).toBeTruthy();
    expect(screen.getByText("Send Reset Link")).toBeTruthy();
  });

  it("shows back to sign in link", async () => {
    const ForgotPassword = (await import("../pages/ForgotPassword")).default;
    render(<Wrapper><ForgotPassword /></Wrapper>);
    expect(screen.getByText("Back to Sign In")).toBeTruthy();
  });
});

describe("ProtectedRoute", () => {
  it("exports ProtectedRoute component", async () => {
    const mod = await import("../components/auth/ProtectedRoute");
    expect(mod.ProtectedRoute).toBeDefined();
  });

  it("shows 403 page for wrong role", async () => {
    const { useAuthStore } = await import("../store/authStore");
    useAuthStore.setState({
      isAuthenticated: true,
      user: { id: "1", email: "test@test.com", fullName: "Test", role: "viewer", organization: null },
      accessToken: "token",
      refreshToken: "refresh",
    });

    const { ProtectedRoute } = await import("../components/auth/ProtectedRoute");
    render(
      <Wrapper>
        <ProtectedRoute requiredRoles={["admin"]}>
          <div>Admin content</div>
        </ProtectedRoute>
      </Wrapper>,
    );
    expect(screen.queryByText("Admin content")).toBeNull();
    expect(screen.getByText("403")).toBeTruthy();

    useAuthStore.setState({
      isAuthenticated: false, user: null, accessToken: null, refreshToken: null,
    });
  });
});
